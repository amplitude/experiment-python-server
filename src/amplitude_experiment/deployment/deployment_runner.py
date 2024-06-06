import logging
from typing import Optional
import threading
import time

from src.amplitude_experiment import LocalEvaluationConfig
from src.amplitude_experiment.cohort.cohort_loader import CohortLoader
from src.amplitude_experiment.cohort.cohort_storage import CohortStorage
from src.amplitude_experiment.flag.flag_config_api import FlagConfigApi
from src.amplitude_experiment.flag.flag_config_storage import FlagConfigStorage
from src.amplitude_experiment.local.poller import Poller
from src.amplitude_experiment.util.flag_config import get_all_cohort_ids


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

    def start(self):
        with self.lock:
            self.refresh(initial=True)
            self.poller.start()

    def stop(self):
        self.poller.stop()

    def __periodic_refresh(self):
        while True:
            try:
                self.refresh(initial=False)
            except Exception as e:
                self.logger.error("Refresh flag configs failed.", e)
            time.sleep(self.config.flag_config_polling_interval_millis / 1000)

    def refresh(self, initial: bool):
        self.logger.debug("Refreshing flag configs.")
        flag_configs = self.flag_config_api.get_flag_configs()

        flag_keys = {flag['key'] for flag in flag_configs}
        self.flag_config_storage.remove_if(lambda f: f.key not in flag_keys)

        if initial:
            cached_futures = {}
            for flag_config in flag_configs:
                cohort_ids = get_all_cohort_ids(flag_config)
                if not self.cohort_loader or not cohort_ids:
                    self.flag_config_storage.put_flag_config(flag_config)
                    continue
                for cohort_id in cohort_ids:
                    future = self.cohort_loader.load_cached_cohort(cohort_id)
                    future.add_done_callback(lambda _: self.flag_config_storage.put_flag_config(flag_config))
                    cached_futures[cohort_id] = future
            try:
                for future in cached_futures.values():
                    future.result()
            except Exception as e:
                self.logger.warning("Failed to download a cohort from the cache", e)

        futures = {}
        for flag_config in flag_configs:
            cohort_ids = get_all_cohort_ids(flag_config)
            if not self.cohort_loader or not cohort_ids:
                self.flag_config_storage.put_flag_config(flag_config)
                continue
            for cohort_id in cohort_ids:
                future = self.cohort_loader.load_cohort(cohort_id)
                future.add_done_callback(lambda _: self.flag_config_storage.put_flag_config(flag_config))
                futures[cohort_id] = future
        if initial:
            for future in futures.values():
                future.result()

        flag_cohort_ids = {flag['key'] for flag in self.flag_config_storage.get_flag_configs().values()}
        deleted_cohort_ids = set(self.cohort_storage.get_cohort_descriptions().keys()) - flag_cohort_ids
        for deleted_cohort_id in deleted_cohort_ids:
            deleted_cohort_description = self.cohort_storage.get_cohort_description(deleted_cohort_id)
            if deleted_cohort_description:
                self.cohort_storage.delete_cohort(deleted_cohort_description.group_type, deleted_cohort_id)

        self.logger.debug(f"Refreshed {len(flag_configs)} flag configs.")
