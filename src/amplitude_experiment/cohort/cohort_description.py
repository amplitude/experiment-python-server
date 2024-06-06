from dataclasses import dataclass, field
from typing import ClassVar

USER_GROUP_TYPE: ClassVar[str] = "User"


@dataclass
class CohortDescription:
    id: str
    last_computed: int
    size: int
    group_type: str = field(default=USER_GROUP_TYPE)
