from app.intent import Pattern


def rewrite_criteria(criteria: str, patterns: set[Pattern], language: str) -> str:
    rewritten = criteria.strip()

    # ----------------------------
    # Require all ties
    # ----------------------------
    if Pattern.REQUIRE_ALL_TIES in patterns:
        if language.lower().startswith("ja"):
            rewritten += (
                "\n\n【重要】\n"
                "最大値が同じ場合は、該当するすべての行を返してください。"
                "LIMIT や FETCH FIRST は使用しないでください。"
            )
        else:
            rewritten += (
                "\n\nIMPORTANT:\n"
                "If multiple rows share the maximum value, return ALL of them. "
                "Do NOT use LIMIT or FETCH FIRST."
            )

    # ----------------------------
    # Anti join (missing rows)
    # ----------------------------
    if Pattern.ANTI_JOIN in patterns:
        if language.lower().startswith("ja"):
            rewritten += (
                "\n\n【注意】\n"
                "NOT IN は使用禁止です。"
                "NOT EXISTS または LEFT JOIN ... IS NULL を使用してください。"
            )
        else:
            rewritten += (
                "\n\nNOTE:\n"
                "Do NOT use NOT IN. "
                "Use NOT EXISTS or LEFT JOIN ... IS NULL."
            )

    # ----------------------------
    # Zero row preservation
    # ----------------------------
    if Pattern.ZERO_ROW in patterns:
        if language.lower().startswith("ja"):
            rewritten += (
                "\n\n【注意】\n"
                "該当データが存在しない場合でも、対象エンティティを必ず含めてください。"
                "LEFT JOIN と COALESCE を使用してください。"
            )
        else:
            rewritten += (
                "\n\nNOTE:\n"
                "Include rows even if there are no matching records. "
                "Use LEFT JOIN and COALESCE."
            )

    return rewritten
