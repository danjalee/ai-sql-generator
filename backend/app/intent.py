from enum import Enum


class Pattern(str, Enum):
    TOP_PER_GROUP = "TOP_PER_GROUP"
    ANTI_JOIN = "ANTI_JOIN"
    ZERO_ROW = "ZERO_ROW"
    DEDUP = "DEDUP"
    SIMPLE_SELECT = "SIMPLE_SELECT"


def detect_patterns(criteria: str) -> set[Pattern]:
    c = criteria.lower()
    patterns: set[Pattern] = set()

    # ---------- ZERO ROW / ALL COMBINATIONS ----------
    if any(w in c for w in [
        "each", "every", "even if", "including",
        "including zero", "all students", "all users"
    ]):
        patterns.add(Pattern.ZERO_ROW)

    # ---------- TOP PER GROUP ----------
    if any(w in c for w in [
        "highest", "maximum", "max", "top",
        "largest", "most", "best"
    ]):
        patterns.add(Pattern.TOP_PER_GROUP)

    # ---------- ANTI JOIN ----------
    if any(w in c for w in [
        "never", "not ordered", "no record",
        "missing", "without", "did not"
    ]):
        patterns.add(Pattern.ANTI_JOIN)
        patterns.add(Pattern.ZERO_ROW)

    # ---------- DEDUP ----------
    if any(w in c for w in [
        "duplicate", "duplicates", "remove duplicate"
    ]):
        patterns.add(Pattern.DEDUP)

    # ---------- FALLBACK ----------
    if not patterns:
        patterns.add(Pattern.SIMPLE_SELECT)

    return patterns
