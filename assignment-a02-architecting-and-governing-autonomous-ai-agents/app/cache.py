import redis
import json
from app.db import fetch_policies

# Connect to Redis (host and port can be changed if needed)
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


def load_policies_into_cache():
    """
    Load all policy data from SQLite into Redis Hashes for quick lookups.
    Specifically:
      - 'prohibited_keywords' → Redis Hash: key = keyword, value = 1
      - 'max_words_free' → Redis Hash 'policies' field 'max_words_free'
      - 'templates' → Redis Hash 'templates' with field 'template_<doc_type>'
    """
    policies = fetch_policies()  # { key_name: value }

    # 1) Prohibited keywords (stored as JSON array)
    pk_json = policies.get("prohibited_keywords", "[]")
    try:
        prohibited_list = json.loads(pk_json)
    except json.JSONDecodeError:
        prohibited_list = []
    # Flush old prohibited list
    redis_client.delete("prohibited_keywords")
    for kw in prohibited_list:
        redis_client.hset("prohibited_keywords", kw, 1)

    # 2) max_words_free (store as integer in "policies" hash)
    max_free = policies.get("max_words_free", "2000")
    redis_client.hset("policies", "max_words_free", int(max_free))

    # 3) templates stored as JSON object string, e.g. { "academic": "...", ... }
    templates_json = policies.get("templates", "{}")
    try:
        templates_dict = json.loads(templates_json)
    except json.JSONDecodeError:
        templates_dict = {}
    # Flush old templates
    redis_client.delete("templates")
    for doc_type, template_text in templates_dict.items():
        redis_client.hset("templates", f"template_{doc_type}", template_text)


def get_prohibited_keywords() -> list[str]:
    """
    Returns the list of prohibited keywords from the Redis Hash.
    """
    return list(redis_client.hkeys("prohibited_keywords"))


def get_max_words_free() -> int:
    """
    Returns the integer value of 'max_words_free' from Redis Hash 'policies'.
    """
    val = redis_client.hget("policies", "max_words_free")
    return int(val) if val is not None else 2000


def get_template_for_doc_type(doc_type: str) -> str | None:
    """
    Returns the template string for a given doc_type, or None if not set.
    """
    return redis_client.hget("templates", f"template_{doc_type}")
