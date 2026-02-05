from enum import Enum

class Pattern(str, Enum):
    TOP_PER_GROUP = "TOP_PER_GROUP"
    ANTI_JOIN = "ANTI_JOIN"
    ZERO_ROW = "ZERO_ROW"
    DEDUP = "DEDUP"
    SIMPLE_SELECT = "SIMPLE_SELECT"
    DISTINCT_DATE = "DISTINCT_DATE"
    ALL_USERS = "ALL_USERS"


def detect_patterns(criteria: str) -> set[Pattern]:
    c = criteria.lower()
    patterns: set[Pattern] = set()

    # Top per group / max / highest
    if any(w in c for w in [
        "highest", "maximum", "max", "top",
        "most", "largest", "best", "spent the most"
    ]):
        patterns.add(Pattern.TOP_PER_GROUP)

    # Anti-join / missing rows
    if any(w in c for w in [
        "never", "no record", "missing",
        "without", "did not", "not placed",
        "no orders", "no purchases"
    ]):
        patterns.add(Pattern.ANTI_JOIN)
        patterns.add(Pattern.ZERO_ROW)

    # Distinct date logic
    if any(w in c for w in [
        "distinct day", "different day",
        "more than one day"
    ]):
        patterns.add(Pattern.DISTINCT_DATE)

    # All users
    if "all users" in c:
        patterns.add(Pattern.ALL_USERS)
        patterns.add(Pattern.ZERO_ROW)

    # Deduplication
    if any(w in c for w in [
        "duplicate", "duplicates", "unique",
        "remove duplicates"
    ]):
        patterns.add(Pattern.DEDUP)

    # Default fallback
    if not patterns:
        patterns.add(Pattern.SIMPLE_SELECT)

    return patterns
