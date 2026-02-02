def validate_sql(sql: str):
    s = sql.lower().strip()

    # ----------------------------
    # Basic SQL sanity
    # ----------------------------
    if not s:
        raise ValueError("Empty SQL")

    if not s.startswith((
        "select",
        "insert",
        "update",
        "delete",
        "create",
        "alter",
        "drop",
        "truncate"
    )):
        raise ValueError("Unsupported SQL statement")

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
    if s.startswith("drop") or s.startswith("truncate"):
        raise ValueError("DROP / TRUNCATE operations are blocked")

    # ----------------------------
    # Soft warnings (future extension)
    # ----------------------------
    if s.startswith("delete") and "where" not in s:
        raise ValueError("DELETE without WHERE is not allowed")

    if s.startswith("update") and "where" not in s:
        raise ValueError("UPDATE without WHERE is not allowed")
