import os
import uuid
import json
import jwt
import shutil
import asyncio
from datetime import datetime
from app.db import (
    insert_document,
    update_document_status,
    insert_summary,
    get_db_connection,
)
from app.cache import (
    redis_client,
    load_policies_into_cache,
    get_prohibited_keywords,
    get_max_words_free,
    get_template_for_doc_type,
)
from fastapi import HTTPException, UploadFile

# Directory to temporarily store uploaded files (if needed)
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def now_iso() -> str:
    return datetime.utcnow().isoformat()

def generate_doc_id() -> str:
    return str(uuid.uuid4())

async def run_ocr(uploaded_file: UploadFile) -> str:
    """
    Placeholder OCR function. In a real system, call Tesseract or similar.
    Here, we just read the bytes and pretend it's plain text.
    """
    # Save the upload temporarily
    file_location = os.path.join(UPLOAD_DIR, f"ocr_{uuid.uuid4().hex}.tmp")
    with open(file_location, "wb") as out_file:
        contents = await uploaded_file.read()
        out_file.write(contents)
    # For this demo, just return an empty string or a placeholder.
    # In practice, use pytesseract.image_to_string()
    return ""  # Or return "Recognized text..."

def classify_document_type(text: str) -> str:
    """
    Very simple keyword-based classification:
      - If it contains "abstract" or "introduction" or "references" → academic
      - If it has many line breaks and is shortish → slides
      - If it looks like HTML or has "news" → news
      - Else, "other"
    """
    lowered = text.lower()
    if any(keyword in lowered for keyword in ["abstract", "introduction", "references"]):
        return "academic"
    if len(text) < 500 and text.count("\n") > 5:
        return "slides"
    if "<!doctype html" in lowered or "news" in lowered:
        return "news"
    return "other"

def simple_text_summarizer(text: str, style_prompt: str) -> str:
    """
    Placeholder summarizer. In real code, call an LLM (OpenAI GPT, etc.).
    Here, we just truncate or echo a dummy summary.
    """
    # For demo: return first N characters depending on style
    # style_prompt might contain "500-word", "5 bullet", etc.
    # We'll ignore and just take the first 300 chars as a placeholder.
    return text[:300] + "\n\n[Summary truncated for demo.]"

def simple_note_generator(text: str, doc_type: str) -> str:
    """
    Placeholder for notes/mind-map generator. In reality: LLM generation.
    Here, we return a JSON with one dummy Q&A pair.
    """
    dummy_notes = {
        "doc_type": doc_type,
        "questions_and_answers": [
            { "question": "What is this document about?", "answer": "Demo placeholder." }
        ],
        "mind_map": { "root": "Document", "branches": [] }
    }
    return json.dumps(dummy_notes)

async def process_document(user_id: str, role: str, uploaded_file: UploadFile):
    """
    Core function that implements:
    1) Ingest & Preprocess (OCR if needed)
    2) Classification (academic/news/slides/other)
    3) Governance check (word limit, prohibited keywords)
    4) Summarization & Note generation
    5) Store in SQL
    6) Notify via Redis Streams
    7) Logging
    """
    # 1. Generate a new doc_id
    doc_id = generate_doc_id()
    filename = uploaded_file.filename

    # 2. Ingest & Preprocess
    #    If it's a PDF or image → run OCR; else, read as plain text
    if filename.endswith(".pdf") or uploaded_file.content_type.startswith("image/"):
        raw_text = await run_ocr(uploaded_file)
    else:
        raw_text_bytes = await uploaded_file.read()
        raw_text = raw_text_bytes.decode("utf-8", errors="replace")

    word_count = len(raw_text.split())

    # 3. Insert initial document record with status "ingested"
    insert_document(
        doc_id=doc_id,
        user_id=user_id,
        filename=filename,
        raw_text=raw_text,
        doc_type="",            # to be updated
        status="ingested"
    )

    # 4. Load policies into cache (if not already loaded)
    load_policies_into_cache()

    # 5. Enforce word count limit for FreeUser
    max_free = get_max_words_free()
    if role == "FreeUser" and word_count > max_free:
        # Auto-reject
        log_event_flagged(
            doc_id, user_id, "word_limit_exceeded", role
        )
        update_document_status(doc_id, status="rejected")
        raise HTTPException(
            status_code=403,
            detail=f"Word limit exceeded ({word_count} > {max_free}) for FreeUser"
        )

    # 6. Classify document type
    doc_type = classify_document_type(raw_text)

    # 7. Check for prohibited keywords
    prohibited_keywords = get_prohibited_keywords()
    flagged_word = None
    for word in raw_text.lower().split():
        if word in prohibited_keywords:
            flagged_word = word
            break

    if flagged_word:
        # Found prohibited content
        if role == "PremiumUser":
            # Route to Review queue
            redis_client.xadd(
                "review_queue",
                {
                    "doc_id": doc_id,
                    "user_id": user_id,
                    "reason": f"keyword_match:{flagged_word}",
                    "timestamp": now_iso()
                }
            )
            update_document_status(doc_id, status="pending_review", doc_type=doc_type)
            log_event_flagged(doc_id, user_id, flagged_word, role)
            return { "status": "pending_review", "reason": f"Flagged for keyword: {flagged_word}" }
        else:
            # Auto-reject (FreeUser or anonymous)
            log_event_flagged(doc_id, user_id, flagged_word, role)
            update_document_status(doc_id, status="rejected", doc_type=doc_type)
            raise HTTPException(
                status_code=403,
                detail=f"Prohibited content detected: '{flagged_word}'"
            )

    # 8. Summarize & Generate Notes
    template = get_template_for_doc_type(doc_type)
    if template is None:
        # Use a default summary template if not provided
        template = "Produce a 200-word summary of this text."

    summary_text = simple_text_summarizer(raw_text, template)
    notes_json = simple_note_generator(raw_text, doc_type)

    # 9. Store summary & update document status in SQL
    insert_summary(doc_id, summary_text, notes_json)
    update_document_status(doc_id, status="completed", doc_type=doc_type)

    # 10. Notify processed via Redis Stream
    redis_client.xadd(
        "processed_notifications",
        {
            "doc_id": doc_id,
            "user_id": user_id,
            "doc_type": doc_type,
            "timestamp": now_iso()
        }
    )

    # 11. Log event
    log_event_processed(doc_id, user_id, doc_type, len(summary_text.split()))

    return { "status": "completed", "doc_id": doc_id }


# ----------------- Observability Helpers -----------------

def log_event_processed(doc_id: str, user_id: str, doc_type: str, summary_length: int):
    """Log a successful processing event in logs/event_log.json."""
    import datetime
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "agent_id": "note_agent_v1",
        "user_id": user_id,
        "doc_id": doc_id,
        "doc_type": doc_type,
        "summary_length": summary_length,
        "decision": "summarized"
    }
    os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)
    with open(os.path.join(os.path.dirname(__file__), "logs", "event_log.json"), "a") as f:
        f.write(json.dumps(entry) + "\n")


def log_event_flagged(doc_id: str, user_id: str, reason: str, role: str):
    """Log a flagged (policy exception) event in logs/policy_exceptions.json."""
    import datetime
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "agent_id": "note_agent_v1",
        "user_id": user_id,
        "doc_id": doc_id,
        "flagged_reason": reason,
        "action": "flagged_for_review" if role == "PremiumUser" else "auto_reject",
        "role_checked": role
    }
    os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)
    with open(os.path.join(os.path.dirname(__file__), "logs", "policy_exceptions.json"), "a") as f:
        f.write(json.dumps(entry) + "\n")
