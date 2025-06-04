from app.db import upsert_policy
from app.cache import load_policies_into_cache

def update_policy(key_name: str, new_value: str):
    """
    Insert or update a policy entry in SQLite, then refresh the Redis cache.
    new_value should be a JSON‐encoded string if the policy is JSON (e.g. prohibited_keywords).
    """
    upsert_policy(key_name, new_value)
    # Immediately reload cache
    load_policies_into_cache()
