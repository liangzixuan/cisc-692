from app.db import engine
import json

with engine.connect() as conn:
    conn.execute(
        "INSERT INTO policies (key_name, value) VALUES (:key, :val)",
        { "key": "prohibited_keywords", "val": json.dumps(["self-harm","hate","terror"]) }
    )
    conn.execute(
        "INSERT INTO policies (key_name, value) VALUES (:key, :val)",
        { "key": "max_words_free", "val": "2000" }
    )
    templates = {
        "academic": "Write a concise 500-word abstract of this academic paper.",
        "news": "List 5 key bullet points summarizing this news article.",
        "slides": "Generate a 10-point outline of this presentation.",
        "other": "Produce a 200-word summary of this text."
    }
    conn.execute(
        "INSERT INTO policies (key_name, value) VALUES (:key, :val)",
        { "key": "templates", "val": json.dumps(templates) }
    )
    conn.commit()
