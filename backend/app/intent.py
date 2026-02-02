WRITE_KEYWORDS = [
    "delete", "remove", "insert", "add",
    "update", "modify", "drop",
    "truncate", "create", "alter"
]

def detect_operation(criteria: str) -> str:
    c = criteria.lower()
    if any(w in c for w in WRITE_KEYWORDS):
        return "WRITE"
    return "READ"


def detect_pattern(criteria: str) -> str | None:
    c = criteria.lower()

    if "duplicate" in c:
        return "DEDUPLICATION"
    if "latest" in c or "most recent" in c:
        return "LATEST_PER_GROUP"
    if "never" in c or "not ordered" in c:
        return "ANTI_JOIN"
    if "all" in c:
        return "ALL_CONDITION"
    if "highest" in c or "maximum" in c:
        return "TOP_PER_GROUP"

    return None
