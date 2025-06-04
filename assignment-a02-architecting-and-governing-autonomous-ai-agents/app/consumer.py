import asyncio
import redis
import time
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import validate_jwt_and_get_role
from app.db import update_document_status
from app.agent_logic import log_event_processed, log_event_flagged

# Redis connection
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# FastAPI app for reviewer override (optional if you want to POST overrides).
app = FastAPI(title="Reviewer Consumer API")

# Ensure the consumer group exists
try:
    redis_client.xgroup_create("review_queue", "reviewers", id="0", mkstream=True)
except redis.exceptions.ResponseError:
    # Group already exists
    pass

class ReviewOverrideRequest(BaseModel):
    doc_id: str
    action: str    # "approve" or "reject"
    notes: str | None = None

@app.post("/override_review/")
async def override_review(
    req: ReviewOverrideRequest,
    user_data = Depends(validate_jwt_and_get_role)
):
    user_id, role = user_data
    if role != "Reviewer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Reviewer privileges required")

    if req.action not in ["approve", "reject"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action")
    new_status = "completed" if req.action == "approve" else "rejected"
    update_document_status(req.doc_id, new_status)

    # Log reviewer override
    if req.action == "approve":
        log_event_processed(req.doc_id, user_id, "review_override", 0)
    else:
        log_event_flagged(req.doc_id, user_id, "review_reject", role)

    # Acknowledge the message in Redis if it exists (optional)
    # We could search for the message ID in the pending list, but for demo we skip that step.

    return { "status": f"document {req.doc_id} {req.action}d by reviewer {user_id}" }


def review_consumer_loop():
    """
    Continuously read flagged documents from 'review_queue'.
    For each message, print details. A real dashboard would push these to a UI.
    """
    while True:
        try:
            entries = redis_client.xreadgroup("reviewers", "consumer1", {"review_queue": ">"}, count=5, block=1000)
            if entries:
                for stream_name, messages in entries:
                    for message_id, msg_data in messages:
                        doc_id = msg_data.get("doc_id")
                        user_id = msg_data.get("user_id")
                        reason = msg_data.get("reason")
                        timestamp = msg_data.get("timestamp")
                        print(f"[{datetime.utcnow().isoformat()}] "
                              f"[REVIEWER CONSUMER] Document '{doc_id}' flagged by user '{user_id}', reason: {reason}, time: {timestamp}")
                        # Acknowledge immediately so this example does not block indefinitely
                        redis_client.xack("review_queue", "reviewers", message_id)
        except Exception as e:
            print(f"[{datetime.utcnow().isoformat()}] Error in review_consumer_loop: {e}")
        time.sleep(1)


if __name__ == "__main__":
    print("Starting Review Consumer Loop (listening for flagged docs)...")
    review_consumer_loop()
