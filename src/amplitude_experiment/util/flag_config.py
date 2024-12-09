from typing import List, Dict, Set

from ..cohort.cohort import USER_GROUP_TYPE
from ..evaluation.types import EvaluationFlag, EvaluationSegment, EvaluationCondition, EvaluationOperator


def is_cohort_filter(condition: EvaluationCondition) -> bool:
    return (
            condition.op in {EvaluationOperator.SET_CONTAINS_ANY, EvaluationOperator.SET_DOES_NOT_CONTAIN_ANY}
            and condition.selector
            and condition.selector[-1] == "cohort_ids"
    )


def get_grouped_cohort_condition_ids(segment: EvaluationSegment) -> Dict[str, Set[str]]:
    cohort_ids = {}
    conditions = segment.conditions or []
    for outer in conditions:
        for condition in outer:
            if is_cohort_filter(condition):
                if len(condition.selector) > 2:
                    context_subtype = condition.selector[1]
                    if context_subtype == "user":
                        group_type = USER_GROUP_TYPE
                    elif "groups" in condition.selector:
                        group_type = condition.selector[2]
                    else:
                        continue
                    cohort_ids.setdefault(group_type, set()).update(condition.values)
    return cohort_ids


def get_grouped_cohort_ids_from_flag(flag: EvaluationFlag) -> Dict[str, Set[str]]:
    cohort_ids = {}
    segments = flag.segments or []
    for segment in segments:
        for key, values in get_grouped_cohort_condition_ids(segment).items():
            cohort_ids.setdefault(key, set()).update(values)
    return cohort_ids


def get_all_cohort_ids_from_flag(flag: EvaluationFlag) -> Set[str]:
    return {cohort_id for values in get_grouped_cohort_ids_from_flag(flag).values() for cohort_id in values}


def get_grouped_cohort_ids_from_flags(flags: List[EvaluationFlag]) -> Dict[str, Set[str]]:
    cohort_ids = {}
    for flag in flags:
        for key, values in get_grouped_cohort_ids_from_flag(flag).items():
            cohort_ids.setdefault(key, set()).update(values)
    return cohort_ids


def get_all_cohort_ids_from_flags(flags: List[EvaluationFlag]) -> Set[str]:
    return {cohort_id for values in get_grouped_cohort_ids_from_flags(flags).values() for cohort_id in values}
