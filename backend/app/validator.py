import re

def validate_sql(sql: str):
    s = sql.strip().lower()

    # ----------------------------
    # Basic sanity
    # ----------------------------
    if not s:
        raise ValueError("Empty SQL")

    # Remove wrapping parentheses
    while s.startswith("(") and s.endswith(")"):
        s = s[1:-1].strip()

    # Extract first keyword (robust)
    match = re.match(r"^(with|select|insert|update|delete|create|alter|drop|truncate)\b", s)
    if not match:
        raise ValueError("Unsupported SQL statement")

    stmt_type = match.group(1)

    # ----------------------------
    # Injection / comment blocking
    # ----------------------------
    forbidden = [";--", "/*", "*/"]
    for f in forbidden:
        if f in s:
            raise ValueError("Invalid or unsafe SQL detected")

    # ----------------------------
    # Hard safety blocks
    # ----------------------------
    if stmt_type in ("drop", "truncate"):
        raise ValueError("DROP / TRUNCATE operations are blocked")

    # ----------------------------
    # Soft safety rules
    # ----------------------------
    if stmt_type == "delete" and "where" not in s:
        raise ValueError("DELETE without WHERE is not allowed")

    if stmt_type == "update" and "where" not in s:
        raise ValueError("UPDATE without WHERE is not allowed")