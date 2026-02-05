import re
from app.intent import Pattern


def verify_sql(sql: str, patterns: set[Pattern]) -> None:
    """
    Raises ValueError if SQL violates intent-aware rules
    """
    errors = []
    s = sql.lower()

    # ----------------------------
    # GLOBAL SAFETY
    # ----------------------------
    if "not in" in s:
        errors.append("NOT IN is forbidden (NULL semantics).")

    # ----------------------------
    # TOP PER GROUP
    # ----------------------------
    if Pattern.TOP_PER_GROUP in patterns:
        if "limit" in s:
            errors.append("TOP_PER_GROUP: LIMIT is not allowed (ties must be returned).")

        if re.search(r"max\s*\(\s*amount\s*\)", s):
            errors.append("TOP_PER_GROUP: Use SUM(amount), not MAX(amount).")

        if "sum(amount)" not in s:
            errors.append("TOP_PER_GROUP: SUM(amount) is required.")

    # ----------------------------
    # DISTINCT DATE
    # ----------------------------
    if Pattern.DISTINCT_DATE in patterns:
        if "count(distinct" not in s:
            errors.append("DISTINCT_DATE: Must use COUNT(DISTINCT date_column).")

    # ----------------------------
    # ZERO ROW / ALL USERS
    # ----------------------------
    if Pattern.ZERO_ROW in patterns or Pattern.ALL_USERS in patterns:
        if "left join" not in s:
            errors.append("ZERO_ROW / ALL_USERS: LEFT JOIN is required.")

        if "coalesce" not in s:
            errors.append("ZERO_ROW / ALL_USERS: COALESCE is required.")

    # ----------------------------
    # SIMPLE SELECT
    # ----------------------------
    if Pattern.SIMPLE_SELECT in patterns:
        if "with " in s:
            errors.append("SIMPLE_SELECT: WITH clause is not allowed.")

    if errors:
        raise ValueError("\n".join(errors))
