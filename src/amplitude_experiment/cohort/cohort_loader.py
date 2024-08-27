import logging
from typing import Dict, Set
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
import threading

from .cohort import Cohort
from .cohort_download_api import CohortDownloadApi
from .cohort_storage import CohortStorage
from ..exception import CohortsDownloadException


class CohortLoader:
    def __init__(self, cohort_download_api: CohortDownloadApi, cohort_storage: CohortStorage):
        self.cohort_download_api = cohort_download_api
        self.cohort_storage = cohort_storage
        self.jobs: Dict[str, Future] = {}
        self.lock_jobs = threading.Lock()
        self.executor = ThreadPoolExecutor(
            max_workers=32,
            thread_name_prefix='CohortLoaderExecutor'
        )

    def load_cohort(self, cohort_id: str) -> Future:
        with self.lock_jobs:
            if cohort_id not in self.jobs:
                future = self.executor.submit(self.__load_cohort_internal, cohort_id)
                future.add_done_callback(lambda f: self._remove_job(cohort_id))
                self.jobs[cohort_id] = future
            return self.jobs[cohort_id]

    def _remove_job(self, cohort_id: str):
        if cohort_id in self.jobs:
            with self.lock_jobs:
                self.jobs.pop(cohort_id, None)

    def download_cohort(self, cohort_id: str) -> Cohort:
        cohort = self.cohort_storage.get_cohort(cohort_id)
        return self.cohort_download_api.get_cohort(cohort_id, cohort)

    def download_cohorts(self, cohort_ids: Set[str]) -> Future:
        def update_task(task_cohort_ids):
            errors = []
            futures = []
            for cohort_id in task_cohort_ids:
                future = self.load_cohort(cohort_id)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    cohort_id = next((c_id for c_id, f in self.jobs.items() if f == future), None)
                    if cohort_id:
                        errors.append((cohort_id, e))

            if errors:
                raise CohortsDownloadException(errors)

        return self.executor.submit(update_task, cohort_ids)

    def __load_cohort_internal(self, cohort_id):
        try:
            cohort = self.download_cohort(cohort_id)
            if cohort is not None:
                self.cohort_storage.put_cohort(cohort)
        except Exception as e:
            raise e
