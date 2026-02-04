from app.intent import Pattern

STRATEGY_RULES = {
    Pattern.TOP_PER_GROUP: """
- Return ALL ties
- Do NOT use LIMIT
- Use window functions (RANK / DENSE_RANK)
- OR subquery with MAX() and JOIN
""",

    Pattern.ANTI_JOIN: """
- Use NOT EXISTS or LEFT JOIN ... IS NULL
- NEVER use NOT IN
""",

    Pattern.ZERO_ROW: """
- Include rows with zero matches
- Use LEFT JOIN or CROSS JOIN
- Use COUNT(column), NOT COUNT(*)
- GROUP BY dimension table
""",

    Pattern.DEDUP: """
- Remove duplicates
- Use GROUP BY or ROW_NUMBER()
""",

    Pattern.SIMPLE_SELECT: """
- Simple SELECT query
- Avoid unnecessary JOINs
"""
}
