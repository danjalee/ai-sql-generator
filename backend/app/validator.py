import re

ALLOWED_START = ("select",)

DISALLOWED_KEYWORDS = [
    "delete",
    "update",
    "insert",
    "drop",
    "truncate",
    "alter"
]

def validate_sql(sql: str):
    s = sql.strip().lower()

    # Must start with SELECT
    if not s.startswith(ALLOWED_START):
        raise Exception("Unsupported SQL statement")

    # Block destructive statements
    for kw in DISALLOWED_KEYWORDS:
        if re.search(rf"\b{kw}\b", s):
            raise Exception("Destructive SQL is not allowed")

    # Allow JOIN variants including CROSS JOIN
    # (NO restriction needed here anymore)

    # Basic sanity check
    if ";" in s[:-1]:
        raise Exception("Multiple SQL statements detected")

    return True
