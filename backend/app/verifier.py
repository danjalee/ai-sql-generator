import requests
from app.intent import Pattern


def call_llm(prompt: str) -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:3b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0,
                "top_p": 0.1
            }
        },
        timeout=60
    )
    response.raise_for_status()

    raw = response.json().get("response", "").strip()

    # Remove markdown if present
    if "```" in raw:
        raw = raw.split("```")[1].strip()

    return raw.rstrip(";")


def verify_sql(sql: str, patterns: set[Pattern]) -> None:
    """
    Raises ValueError if SQL violates strategy rules
    """
    errors = []
    sql_upper = sql.upper()

    # ANTI JOIN rules
    if Pattern.ANTI_JOIN in patterns:
        if "NOT IN" in sql_upper:
            errors.append(
                "ANTI_JOIN violation: NOT IN is not allowed. "
                "Use NOT EXISTS or LEFT JOIN ... IS NULL."
            )

    # TOP PER GROUP rules
    if Pattern.TOP_PER_GROUP in patterns:
        if "LIMIT" in sql_upper:
            errors.append(
                "TOP_PER_GROUP violation: LIMIT is not allowed. "
                "You must return ALL ties."
            )

    # ZERO ROW rules
    if Pattern.ZERO_ROW in patterns:
        if "LEFT JOIN" not in sql_upper:
            errors.append(
                "ZERO_ROW violation: LEFT JOIN is required to include zero rows."
            )
        if "COUNT(*)" in sql_upper:
            errors.append(
                "ZERO_ROW violation: Use COUNT(column), not COUNT(*)."
            )

    # SIMPLE SELECT rules
    if Pattern.SIMPLE_SELECT in patterns:
        if "WITH " in sql_upper:
            errors.append(
                "SIMPLE_SELECT violation: WITH clause is not allowed."
            )

    if errors:
        raise ValueError("\n".join(errors))
