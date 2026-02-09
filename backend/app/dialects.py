DIALECT_RULES = {
    "mysql": """Use MySQL syntax.
- COALESCE(...) for zero handling
- DATE functions: DATE(), DATE_FORMAT(...) as needed
- LIMIT n for pagination (only if explicitly requested)
- Avoid reserved/keyword aliases; prefer rnk over rank for window functions
""",
    "postgresql": """Use PostgreSQL syntax.
- COALESCE(...) for zero handling
- DISTINCT ON requires ORDER BY; prefer COUNT(DISTINCT ...) for distinct counts
- LIMIT n for pagination (only if explicitly requested)
""",
    "sqlserver": """Use SQL Server syntax.
- COALESCE(...) for zero handling
- Use TOP n instead of LIMIT (only if explicitly requested)
- DATE functions: CAST(column AS DATE) for date-only
""",
    "sqlite": """Use SQLite syntax.
- COALESCE(...) for zero handling
- DATE functions: date(column) for date-only
- LIMIT n for pagination (only if explicitly requested)
"""
}
