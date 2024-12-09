from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from dataclasses_json import dataclass_json

from .select import selectable


@selectable
@dataclass_json
@dataclass
class EvaluationVariant:
    """Represents a variant in a feature flag evaluation."""
    key: Optional[str] = None
    value: Optional[Any] = None
    payload: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass_json
@dataclass
class EvaluationDistribution:
    """Represents distribution configuration for a variant."""
    variant: str
    range: List[int]


@dataclass_json
@dataclass
class EvaluationAllocation:
    """Represents allocation configuration for bucketing."""
    range: List[int]
    distributions: List[EvaluationDistribution]


@dataclass_json
@dataclass
class EvaluationCondition:
    """Represents a condition for flag evaluation."""
    selector: List[str]
    op: str
    values: List[str]


@dataclass_json
@dataclass
class EvaluationBucket:
    """Represents bucketing configuration for a segment."""
    selector: List[str]
    salt: str
    allocations: List[EvaluationAllocation]


@dataclass_json
@dataclass
class EvaluationSegment:
    """Represents a segment in a feature flag."""
    bucket: Optional[EvaluationBucket] = None
    conditions: Optional[List[List[EvaluationCondition]]] = None
    variant: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass_json
@dataclass
class EvaluationFlag:
    """Represents a complete feature flag configuration."""
    key: str
    variants: Dict[str, EvaluationVariant]
    segments: List[EvaluationSegment]
    dependencies: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class EvaluationOperator:
    """Constants for evaluation operators."""
    IS = 'is'
    IS_NOT = 'is not'
    CONTAINS = 'contains'
    DOES_NOT_CONTAIN = 'does not contain'
    LESS_THAN = 'less'
    LESS_THAN_EQUALS = 'less or equal'
    GREATER_THAN = 'greater'
    GREATER_THAN_EQUALS = 'greater or equal'
    VERSION_LESS_THAN = 'version less'
    VERSION_LESS_THAN_EQUALS = 'version less or equal'
    VERSION_GREATER_THAN = 'version greater'
    VERSION_GREATER_THAN_EQUALS = 'version greater or equal'
    SET_IS = 'set is'
    SET_IS_NOT = 'set is not'
    SET_CONTAINS = 'set contains'
    SET_DOES_NOT_CONTAIN = 'set does not contain'
    SET_CONTAINS_ANY = 'set contains any'
    SET_DOES_NOT_CONTAIN_ANY = 'set does not contain any'
    REGEX_MATCH = 'regex match'
    REGEX_DOES_NOT_MATCH = 'regex does not match'
