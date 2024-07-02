import logging
from typing import Dict, Set
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
import threading

from .cohort import Cohort
from .cohort_download_api import CohortDownloadApi
from .cohort_storage import CohortStorage


class CohortLoader:
    def __init__(self, cohort_download_api: CohortDownloadApi, cohort_storage: CohortStorage,
                 logger: logging.Logger = None):
        self.cohort_download_api = cohort_download_api
        self.cohort_storage = cohort_storage
        self.jobs: Dict[str, Future] = {}
        self.lock_jobs = threading.Lock()
        self.executor = ThreadPoolExecutor(
            max_workers=32,
            thread_name_prefix='CohortLoaderExecutor'
        )
        self.logger = logger or logging.getLogger("Amplitude")

    def load_cohort(self, cohort_id: str) -> Future:
        with self.lock_jobs:
            if cohort_id not in self.jobs:
                def task():
                    try:
                        cohort = self.download_cohort(cohort_id)
                        self.cohort_storage.put_cohort(cohort)
                    except Exception as e:
                        raise e

                future = self.executor.submit(task)
                future.add_done_callback(lambda f: self._remove_job(cohort_id))
                self.jobs[cohort_id] = future
            return self.jobs[cohort_id]

    def _remove_job(self, cohort_id: str):
        if cohort_id in self.jobs:
            del self.jobs[cohort_id]

    def download_cohort(self, cohort_id: str) -> Cohort:
        cohort = self.cohort_storage.get_cohort(cohort_id)
        return self.cohort_download_api.get_cohort(cohort_id, cohort)

    def update_stored_cohorts(self) -> Future:
        def task():
            futures = [self.load_cohort(cohort_id) for cohort_id in self.cohort_storage.get_cohort_ids()]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"Error updating cohort: {e}")

        return self.executor.submit(task)
