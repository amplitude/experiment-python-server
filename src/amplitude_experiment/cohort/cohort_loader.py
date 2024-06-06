from typing import Dict, Set, Optional
from concurrent.futures import ThreadPoolExecutor, Future
import threading

from src.amplitude_experiment.cohort.cohort_description import CohortDescription
from src.amplitude_experiment.cohort.cohort_download_api import CohortDownloadApi, DirectCohortDownloadApiV5
from src.amplitude_experiment.cohort.cohort_storage import CohortStorage


class CohortLoader:
    def __init__(self, max_cohort_size: int, cohort_download_api: CohortDownloadApi, cohort_storage: CohortStorage,
                 direct_cohort_download_api: Optional[DirectCohortDownloadApiV5] = None):
        self.max_cohort_size = max_cohort_size
        self.cohort_download_api = cohort_download_api
        self.cohort_storage = cohort_storage
        self.direct_cohort_download_api = direct_cohort_download_api

        self.jobs: Dict[str, Future] = {}
        self.cached_jobs: Dict[str, Future] = {}

        self.lock_jobs = threading.Lock()
        self.lock_cached_jobs = threading.Lock()

        self.executor = ThreadPoolExecutor(
            max_workers=32,
            thread_name_prefix='CohortLoaderExecutor'
        )

    def load_cohort(self, cohort_id: str) -> Future:
        with self.lock_jobs:
            if cohort_id not in self.jobs:
                def task():
                    print(f"Loading cohort {cohort_id}")
                    cohort_description = self.get_cohort_description(cohort_id)
                    if self.should_download_cohort(cohort_description):
                        cohort_members = self.download_cohort(cohort_description)
                        self.cohort_storage.put_cohort(cohort_description, cohort_members)

                future = self.executor.submit(task)
                future.add_done_callback(lambda _: self.jobs.pop(cohort_id, None))
                self.jobs[cohort_id] = future
            return self.jobs[cohort_id]

    def load_cached_cohort(self, cohort_id: str) -> Future:
        with self.lock_cached_jobs:
            if cohort_id not in self.cached_jobs:
                def task():
                    print(f"Loading cohort from cache {cohort_id}")
                    cohort_description = self.get_cohort_description(cohort_id)
                    cohort_description.last_computed = 0
                    if self.should_download_cohort(cohort_description):
                        cohort_members = self.download_cached_cohort(cohort_description)
                        self.cohort_storage.put_cohort(cohort_description, cohort_members)

                future = self.executor.submit(task)
                self.cached_jobs[cohort_id] = future
                future.add_done_callback(lambda _: self.cached_jobs.pop(cohort_id, None))
                return future
            else:
                return self.cached_jobs[cohort_id]

    def get_cohort_description(self, cohort_id: str) -> CohortDescription:
        return self.cohort_download_api.get_cohort_description(cohort_id)

    def should_download_cohort(self, cohort_description: CohortDescription) -> bool:
        storage_description = self.cohort_storage.get_cohort_description(cohort_description.id)
        return (cohort_description.size <= self.max_cohort_size and
                cohort_description.last_computed > (storage_description.last_computed if storage_description else -1))

    def download_cohort(self, cohort_description: CohortDescription) -> Set[str]:
        return self.cohort_download_api.get_cohort_members(cohort_description)

    def download_cached_cohort(self, cohort_description: CohortDescription) -> Set[str]:
        return (self.direct_cohort_download_api.get_cached_cohort_members(cohort_description.id,
                                                                          cohort_description.group_type)
                if self.direct_cohort_download_api else
                self.cohort_download_api.get_cohort_members(cohort_description))
