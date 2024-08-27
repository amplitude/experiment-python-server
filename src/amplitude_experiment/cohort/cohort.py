from dataclasses import dataclass, field
from typing import ClassVar, Set

USER_GROUP_TYPE: ClassVar[str] = "User"


@dataclass
class Cohort:
    id: str
    last_modified: int
    size: int
    member_ids: Set[str]
    group_type: str = field(default=USER_GROUP_TYPE)
