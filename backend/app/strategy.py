from app.intent import Pattern

STRATEGY_RULES = {
    Pattern.TOP_PER_GROUP: """
- Use window functions per department
- DENSE_RANK() or RANK() over (PARTITION BY department ORDER BY salary DESC)
- Return rows where rank <= requested top N
""",

    Pattern.REQUIRE_ALL_TIES: """
- Return ALL rows that share the maximum value
- NEVER use LIMIT or FETCH FIRST
""",

    Pattern.ANTI_JOIN: """
- Use NOT EXISTS or LEFT JOIN ... IS NULL
- NEVER use NOT IN
""",

    Pattern.ZERO_ROW: """
- Include rows with zero matches
- Use LEFT JOIN
- Use COALESCE(...) for zero values
""",

    Pattern.DISTINCT_DATE: """
- Use COUNT(DISTINCT date_column)
""",

    Pattern.ALL_USERS: """
- Preserve all users
- LEFT JOIN required
""",

    Pattern.DEDUP: """
- Remove duplicates using DISTINCT or GROUP BY
""",

    Pattern.SIMPLE_SELECT: """
- Single SELECT
- No WITH clause
"""
}
