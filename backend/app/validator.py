import re

ALLOWED_START = ("select", "with")

DISALLOWED = [
    "delete", "update", "insert",
    "drop", "truncate", "alter"
]

def validate_sql(sql: str):
    s = sql.strip().lower()

    if not s:
        raise Exception("Empty SQL")

    if not s.startswith(ALLOWED_START):
        raise Exception("Only SELECT statements allowed")

    for kw in DISALLOWED:
        if re.search(rf"\b{kw}\b", s):
            raise Exception("Destructive SQL blocked")

    if ";" in s[:-1]:
        raise Exception("Multiple statements detected")

    return True
