import re
from app.intent import Pattern


def verify_sql(sql: str, patterns: set[Pattern]) -> None:
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
        if "sum(" not in s:
            errors.append("TOP_PER_GROUP: SUM() must be used for aggregation.")

    # ----------------------------
    # ALL TIES REQUIRED
    # ----------------------------
    if Pattern.REQUIRE_ALL_TIES in patterns:
        if "limit" in s or "fetch first" in s:
            errors.append(
                "REQUIRE_ALL_TIES: LIMIT / FETCH FIRST is forbidden. "
                "All ties must be returned."
            )

    # ----------------------------
    # DISTINCT DATE
    # ----------------------------
    if Pattern.DISTINCT_DATE in patterns:
        if not re.search(r"count\s*\(\s*distinct", s):
            errors.append(
                "DISTINCT_DATE: COUNT(DISTINCT date_column) is required."
            )

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
