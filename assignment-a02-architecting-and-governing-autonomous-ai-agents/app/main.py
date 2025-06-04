import os
import uuid
import shutil
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from starlette.responses import JSONResponse

from app.auth import validate_jwt_and_get_role
from app.db import initialize_database, insert_document, update_document_status
from app.agent_logic import process_document
from app.policies import update_policy
from app.cache import load_policies_into_cache
from app.db import insert_user

app = FastAPI(title="NoteGPT Assignment API")

# Ensure the database and tables exist
initialize_database()
# Load initial policies into cache
load_policies_into_cache()

# ----------------- Data Models -----------------
class UpdatePolicyRequest(BaseModel):
    key_name: str
    new_value: str  # For arrays or JSON, pass a JSON-encoded string

class ReviewOverrideRequest(BaseModel):
    doc_id: str
    action: str       # "approve" or "reject"
    notes: str | None = None

# ----------------- Mock Token Generator (for testing only) -----------------
# In a real system, you'd have a separate auth service issuing JWTs.
@app.post("/token/")
def get_token(user_id: str, role: str):
    """
    Generate a JWT for testing. In production, use a proper user login flow.
    Acceptable roles: FreeUser, PremiumUser, Reviewer, Admin
    """
    import jwt, datetime

    SECRET_KEY = "supersecretkey"
    ALGORITHM = "HS256"
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # Auto-create a user in the database (for demo)
    if role in ["FreeUser", "PremiumUser", "Reviewer", "Admin"]:
        subscription_tier = "Free" if role == "FreeUser" else (
                            "Premium" if role == "PremiumUser" else "N/A")
        insert_user(user_id=user_id, username=user_id, role=role, tier=subscription_tier)

    return { "access_token": token, "token_type": "bearer" }

# ----------------- Core Endpoints -----------------
@app.post("/submit_document/")
async def submit_document(
    file: UploadFile = File(...),
    user_data = Depends(validate_jwt_and_get_role)
):
    """
    Endpoint for users to submit a document (PDF, image, or plain text).
    Returns status: "completed" or "pending_review"/"rejected".
    """
    user_id, role = user_data

    # Delegate to process_document() - returns a dict with status
    try:
        result = await process_document(user_id, role, file)
        return JSONResponse(status_code=200, content=result)
    except HTTPException as he:
        raise he
    except Exception as e:
        # Unexpected error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal processing error: {str(e)}"
        )

@app.post("/override_review/")
async def override_review(
    req: ReviewOverrideRequest,
    user_data = Depends(validate_jwt_and_get_role)
):
    """
    Endpoint for a Reviewer to approve or reject a flagged document.
    """
    user_id, role = user_data
    if role != "Reviewer":
        raise HTTPException(status_code=403, detail="Reviewer privileges required")

    # Update documents table accordingly
    if req.action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    new_status = "completed" if req.action == "approve" else "rejected"
    update_document_status(req.doc_id, new_status)

    # Log override event
    from .agent_logic import log_event_processed, log_event_flagged
    if req.action == "approve":
        log_event_processed(req.doc_id, user_id, "review_override", 0)
    else:
        log_event_flagged(req.doc_id, user_id, "review_reject", role)

    return { "status": f"document {req.doc_id} {req.action}d by reviewer {user_id}" }

@app.post("/update_policy/")
async def api_update_policy(
    req: UpdatePolicyRequest,
    user_data = Depends(validate_jwt_and_get_role)
):
    """
    Endpoint for an Admin to update policy. new_value must be a JSON-encoded string
    if the policy is a list or object (e.g. prohibited_keywords).
    """
    user_id, role = user_data
    if role != "Admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")

    try:
        # Insert/update the policy in SQLite and reload Redis cache
        update_policy(req.key_name, req.new_value)
        return { "status": "policy_updated", "key": req.key_name }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update policy: {str(e)}")


@app.get("/")
async def root():
    return { "message": "NoteGPT Assignment Backend is running." }
