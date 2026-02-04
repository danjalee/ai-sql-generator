from app.intent import Pattern

STRATEGY_RULES = {
    Pattern.TOP_PER_GROUP: """
- Return ALL ties
- Do NOT use LIMIT
- Use subquery with MAX() OR window functions
""",

    Pattern.ANTI_JOIN: """
- Use NOT EXISTS or LEFT JOIN ... IS NULL
- NEVER use NOT IN
""",

    Pattern.ZERO_ROW: """
- Include rows with zero matches
- Use LEFT JOIN
- Use COUNT(column), NOT COUNT(*)
""",

    Pattern.DEDUP: """
- Remove duplicates using GROUP BY or DISTINCT
""",

    Pattern.SIMPLE_SELECT: """
- Single SELECT
- No WITH
- No unnecessary JOIN
"""
}