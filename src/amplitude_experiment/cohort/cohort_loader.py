from typing import Dict, Set
from concurrent.futures import ThreadPoolExecutor, Future
import threading

from .cohort_description import CohortDescription
from .cohort_download_api import CohortDownloadApi
from .cohort_storage import CohortStorage


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
                def task():
                    try:
                        cohort_description = self.get_cohort_description(cohort_id)
                        cohort_members = self.download_cohort(cohort_description)
                        self.cohort_storage.put_cohort(cohort_description, cohort_members)
                    except Exception as e:
                        raise e

                future = self.executor.submit(task)
                future.add_done_callback(lambda f: self._remove_job(cohort_id))
                self.jobs[cohort_id] = future
            return self.jobs[cohort_id]

    def _remove_job(self, cohort_id: str):
        if cohort_id in self.jobs:
            del self.jobs[cohort_id]

    def get_cohort_description(self, cohort_id: str) -> CohortDescription:
        return self.cohort_download_api.get_cohort_description(cohort_id)

    def should_download_cohort(self, cohort_description: CohortDescription) -> bool:
        return self.cohort_storage.get_cohort_description(cohort_description.id) is None

    def download_cohort(self, cohort_description: CohortDescription) -> Set[str]:
        return self.cohort_download_api.get_cohort_members(cohort_description,
                                                           self.should_download_cohort(cohort_description))
