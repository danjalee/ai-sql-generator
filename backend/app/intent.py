from enum import Enum

class Pattern(str, Enum):
    TOP_PER_GROUP = "TOP_PER_GROUP"
    ANTI_JOIN = "ANTI_JOIN"
    ZERO_ROW = "ZERO_ROW"
    DEDUP = "DEDUP"
    SIMPLE_SELECT = "SIMPLE_SELECT"


def detect_patterns(criteria: str) -> set[Pattern]:
    c = criteria.lower()
    patterns = set()

    if any(w in c for w in ["highest", "maximum", "max", "top", "largest"]):
        patterns.add(Pattern.TOP_PER_GROUP)

    if any(w in c for w in ["never", "not ordered", "no record", "missing"]):
        patterns.add(Pattern.ANTI_JOIN)
        patterns.add(Pattern.ZERO_ROW)

    if "duplicate" in c:
        patterns.add(Pattern.DEDUP)

    if not patterns:
        patterns.add(Pattern.SIMPLE_SELECT)

    return patterns
