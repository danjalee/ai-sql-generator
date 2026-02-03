import re

ALLOWED_START = (
    "select",
    "with"
)

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

    if not s:
        raise Exception("Empty SQL")

    # Allow SELECT and WITH (CTE-based SELECT)
    if not s.startswith(ALLOWED_START):
        raise Exception("Unsupported SQL statement")

    # Block destructive statements anywhere
    for kw in DISALLOWED_KEYWORDS:
        if re.search(rf"\b{kw}\b", s):
            raise Exception("Destructive SQL is not allowed")

    # Block stacked statements
    if ";" in s[:-1]:
        raise Exception("Multiple SQL statements detected")

    return True
