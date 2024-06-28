import logging
from typing import Optional, Set
import threading

from ..exception import CohortNotModifiedException
from ..local.config import LocalEvaluationConfig
from ..cohort.cohort_loader import CohortLoader
from ..cohort.cohort_storage import CohortStorage
from ..flag.flag_config_api import FlagConfigApi
from ..flag.flag_config_storage import FlagConfigStorage
from ..local.poller import Poller
from ..util.flag_config import get_all_cohort_ids_from_flag


class DeploymentRunner:
    def __init__(
            self,
            config: LocalEvaluationConfig,
            flag_config_api: FlagConfigApi,
            flag_config_storage: FlagConfigStorage,
            cohort_storage: CohortStorage,
            cohort_loader: Optional[CohortLoader] = None,
    ):
        self.config = config
        self.flag_config_api = flag_config_api
        self.flag_config_storage = flag_config_storage
        self.cohort_storage = cohort_storage
        self.cohort_loader = cohort_loader
        self.lock = threading.Lock()
        self.poller = Poller(self.config.flag_config_polling_interval_millis / 1000, self.__periodic_refresh)
        self.logger = logging.getLogger("Amplitude")
        self.logger.addHandler(logging.StreamHandler())
        if self.config.debug:
            self.logger.setLevel(logging.DEBUG)

    def start(self):
        with self.lock:
            self.refresh()
            self.poller.start()

    def stop(self):
        self.poller.stop()

    def __periodic_refresh(self):
        try:
            self.refresh()
        except Exception as e:
            self.logger.error(f"Refresh flag and cohort configs failed: {e}")

    def refresh(self):
        self.logger.debug("Refreshing flag configs.")
        try:
            flag_configs = self.flag_config_api.get_flag_configs()
        except Exception as e:
            self.logger.error(f'Failed to fetch flag configs: {e}')
            raise Exception

        flag_keys = {flag['key'] for flag in flag_configs}
        self.flag_config_storage.remove_if(lambda f: f['key'] not in flag_keys)

        for flag_config in flag_configs:
            cohort_ids = get_all_cohort_ids_from_flag(flag_config)
            if not self.cohort_loader or not cohort_ids:
                self.logger.debug(f"Putting non-cohort flag {flag_config['key']}")
                self.flag_config_storage.put_flag_config(flag_config)
                continue

            # Keep track of old flag and cohort for each flag
            old_flag_config = self.flag_config_storage.get_flag_config(flag_config['key'])

            try:
                self._load_cohorts(flag_config, cohort_ids)
                self.flag_config_storage.put_flag_config(flag_config)  # Store new flag config
                self.logger.debug(f"Stored flag config {flag_config['key']}")

            except Exception as e:
                self.logger.warning(f"Failed to load all cohorts for flag {flag_config['key']}. "
                                    f"Using the old flag config.")
                self.flag_config_storage.put_flag_config(old_flag_config)
                raise e

        self._delete_unused_cohorts()
        self.logger.debug(f"Refreshed {len(flag_configs)} flag configs.")

    def _load_cohorts(self, flag_config: dict, cohort_ids: Set[str]):
        def task():
            try:
                for cohort_id in cohort_ids:
                    future = self.cohort_loader.load_cohort(cohort_id)
                    future.result()
                    self.logger.debug(f"Cohort {cohort_id} loaded for flag {flag_config['key']}")
            except Exception as e:
                if not isinstance(e, CohortNotModifiedException):
                    self.logger.error(f"Failed to load cohorts for flag {flag_config['key']}: {e}")
                    raise e

        cohort_fetched = self.cohort_loader.executor.submit(task)
        # Wait for both flag and cohort loading to complete
        cohort_fetched.result()

    def _delete_unused_cohorts(self):
        flag_cohort_ids = set()
        for flag in self.flag_config_storage.get_flag_configs().values():
            flag_cohort_ids.update(get_all_cohort_ids_from_flag(flag))

        storage_cohorts = self.cohort_storage.get_cohorts()
        deleted_cohort_ids = set(storage_cohorts.keys()) - flag_cohort_ids

        for deleted_cohort_id in deleted_cohort_ids:
            deleted_cohort = storage_cohorts.get(deleted_cohort_id)
            if deleted_cohort is not None:
                self.cohort_storage.delete_cohort(deleted_cohort.group_type, deleted_cohort_id)

