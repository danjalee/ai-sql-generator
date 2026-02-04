from app.intent import Pattern

STRATEGY_RULES = {
    Pattern.ZERO_ROW: """
- MUST include rows with zero matches
- Use CROSS JOIN to enumerate dimension tables
- LEFT JOIN fact tables
- NEVER use INNER JOIN
- Use COUNT(column), NOT COUNT(*)
- Use COALESCE(..., 0)
""",

    Pattern.ANTI_JOIN: """
- Use NOT EXISTS or LEFT JOIN ... IS NULL
- NEVER use NOT IN
""",

    Pattern.TOP_PER_GROUP: """
- Return ALL ties
- Do NOT use LIMIT
- Use window functions (RANK / DENSE_RANK)
- OR subquery with MAX() + JOIN
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