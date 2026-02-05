from dataclasses import dataclass
from app.intent import Pattern


@dataclass(frozen=True)
class Requirement:
    must_use: set[str]
    forbidden: set[str]


REQUIREMENTS = {
    Pattern.TOP_PER_GROUP: Requirement(
        must_use={"sum("},
        forbidden={"limit", "fetch first"}
    ),

    Pattern.REQUIRE_ALL_TIES: Requirement(
        must_use=set(),
        forbidden={"limit", "fetch first"}
    ),

    Pattern.ANTI_JOIN: Requirement(
        must_use=set(),
        forbidden={"not in"}
    ),

    Pattern.ZERO_ROW: Requirement(
        must_use={"left join", "coalesce"},
        forbidden=set()
    ),

    Pattern.DISTINCT_DATE: Requirement(
        must_use={"count(distinct"},
        forbidden=set()
    ),

    Pattern.SIMPLE_SELECT: Requirement(
        must_use=set(),
        forbidden={"with "}
    )
}
