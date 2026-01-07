def validate_sql(sql, mode):
    forbidden = [";--", "/*", "*/"]
    for f in forbidden:
        if f in sql:
            raise ValueError("Invalid SQL")

    if mode == "read" and not sql.strip().lower().startswith("select"):
        raise ValueError("Read mode allows SELECT only")
