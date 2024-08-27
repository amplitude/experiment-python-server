from typing import Dict, Set, Optional
from threading import RLock

from .cohort import Cohort, USER_GROUP_TYPE


class CohortStorage:
    def get_cohort(self, cohort_id: str):
        raise NotImplementedError

    def get_cohorts(self):
        raise NotImplementedError

    def get_cohorts_for_user(self, user_id: str, cohort_ids: Set[str]) -> Set[str]:
        raise NotImplementedError

    def get_cohorts_for_group(self, group_type: str, group_name: str, cohort_ids: Set[str]) -> Set[str]:
        raise NotImplementedError

    def put_cohort(self, cohort_description: Cohort):
        raise NotImplementedError

    def delete_cohort(self, group_type: str, cohort_id: str):
        raise NotImplementedError

    def get_cohort_ids(self) -> Set[str]:
        raise NotImplementedError


class InMemoryCohortStorage(CohortStorage):
    def __init__(self):
        self.lock = RLock()
        self.group_to_cohort_store: Dict[str, Set[str]] = {}
        self.cohort_store: Dict[str, Cohort] = {}

    def get_cohort(self, cohort_id: str):
        with self.lock:
            return self.cohort_store.get(cohort_id)

    def get_cohorts(self):
        return self.cohort_store.copy()

    def get_cohorts_for_user(self, user_id: str, cohort_ids: Set[str]) -> Set[str]:
        return self.get_cohorts_for_group(USER_GROUP_TYPE, user_id, cohort_ids)

    def get_cohorts_for_group(self, group_type: str, group_name: str, cohort_ids: Set[str]) -> Set[str]:
        result = set()
        with self.lock:
            group_type_cohorts = self.group_to_cohort_store.get(group_type, {})
            for cohort_id in group_type_cohorts:
                members = self.cohort_store.get(cohort_id).member_ids
                if cohort_id in cohort_ids and group_name in members:
                    result.add(cohort_id)
        return result

    def put_cohort(self, cohort: Cohort):
        with self.lock:
            if cohort.group_type not in self.group_to_cohort_store:
                self.group_to_cohort_store[cohort.group_type] = set()
            self.group_to_cohort_store[cohort.group_type].add(cohort.id)
            self.cohort_store[cohort.id] = cohort

    def delete_cohort(self, group_type: str, cohort_id: str):
        with self.lock:
            group_cohorts = self.group_to_cohort_store.get(group_type, {})
            if cohort_id in group_cohorts:
                group_cohorts.remove(cohort_id)
            if cohort_id in self.cohort_store:
                del self.cohort_store[cohort_id]

    def get_cohort_ids(self):
        with self.lock:
            return set(self.cohort_store.keys())
