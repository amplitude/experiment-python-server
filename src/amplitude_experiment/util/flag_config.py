from typing import List, Dict, Set, Any

from src.amplitude_experiment.cohort.cohort_description import USER_GROUP_TYPE


def is_cohort_filter(condition: Dict[str, Any]) -> bool:
    return (
            condition['op'] in {"set contains any", "set does not contain any"}
            and condition['selector']
            and condition['selector'][-1] == "cohort_ids"
    )


def get_grouped_cohort_condition_ids(segment: Dict[str, Any]) -> Dict[str, Set[str]]:
    cohort_ids = {}
    conditions = segment.get('conditions', [])
    for outer in conditions:
        for condition in outer:
            if is_cohort_filter(condition):
                if len(condition['selector']) > 2:
                    context_subtype = condition['selector'][1]
                    if context_subtype == "user":
                        group_type = USER_GROUP_TYPE
                    elif "groups" in condition['selector']:
                        group_type = condition['selector'][2]
                    else:
                        continue
                    cohort_ids.setdefault(group_type, set()).update(condition['values'])
    return cohort_ids


def get_grouped_cohort_ids(flag: Dict[str, Any]) -> Dict[str, Set[str]]:
    cohort_ids = {}
    segments = flag.get('segments', [])
    for segment in segments:
        for key, values in get_grouped_cohort_condition_ids(segment).items():
            cohort_ids.setdefault(key, set()).update(values)
    return cohort_ids


def get_all_cohort_ids(flag: Dict[str, Any]) -> Set[str]:
    return {cohort_id for values in get_grouped_cohort_ids(flag).values() for cohort_id in values}


def get_grouped_cohort_ids_from_flags(flags: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
    cohort_ids = {}
    for flag in flags:
        for key, values in get_grouped_cohort_ids(flag).items():
            cohort_ids.setdefault(key, set()).update(values)
    return cohort_ids


def get_all_cohort_ids_from_flags(flags: List[Dict[str, Any]]) -> Set[str]:
    return {cohort_id for values in get_grouped_cohort_ids_from_flags(flags).values() for cohort_id in values}
