from typing import Dict, Set, Optional
from threading import RLock

from .cohort_description import CohortDescription, USER_GROUP_TYPE


class CohortStorage:
    def get_cohorts_for_user(self, user_id: str, cohort_ids: Set[str]) -> Set[str]:
        raise NotImplementedError()

    def get_cohorts_for_group(self, group_type: str, group_name: str, cohort_ids: Set[str]) -> Set[str]:
        raise NotImplementedError()

    def get_cohort_description(self, cohort_id: str) -> Optional[CohortDescription]:
        raise NotImplementedError()

    def get_cohort_descriptions(self) -> Dict[str, CohortDescription]:
        raise NotImplementedError()

    def put_cohort(self, cohort_description: CohortDescription, members: Set[str]):
        raise NotImplementedError()

    def delete_cohort(self, group_type: str, cohort_id: str):
        raise NotImplementedError()


class InMemoryCohortStorage(CohortStorage):
    def __init__(self):
        self.lock = RLock()
        self.cohort_store: Dict[str, Dict[str, Set[str]]] = {}
        self.description_store: Dict[str, CohortDescription] = {}

    def get_cohorts_for_user(self, user_id: str, cohort_ids: Set[str]) -> Set[str]:
        return self.get_cohorts_for_group(USER_GROUP_TYPE, user_id, cohort_ids)

    def get_cohorts_for_group(self, group_type: str, group_name: str, cohort_ids: Set[str]) -> Set[str]:
        result = set()
        with self.lock:
            group_type_cohorts = self.cohort_store.get(group_type, {})
            for cohort_id, members in group_type_cohorts.items():
                if cohort_id in cohort_ids and group_name in members:
                    result.add(cohort_id)
        return result

    def get_cohort_description(self, cohort_id: str) -> Optional[CohortDescription]:
        with self.lock:
            return self.description_store.get(cohort_id)

    def get_cohort_descriptions(self) -> Dict[str, CohortDescription]:
        with self.lock:
            return self.description_store.copy()

    def put_cohort(self, cohort_description: CohortDescription, members: Set[str]):
        with self.lock:
            self.cohort_store.setdefault(cohort_description.group_type, {})[cohort_description.id] = members
            self.description_store[cohort_description.id] = cohort_description

    def delete_cohort(self, group_type: str, cohort_id: str):
        with self.lock:
            group_cohorts = self.cohort_store.get(group_type, {})
            if cohort_id in group_cohorts:
                del group_cohorts[cohort_id]
            if cohort_id in self.description_store:
                del self.description_store[cohort_id]
