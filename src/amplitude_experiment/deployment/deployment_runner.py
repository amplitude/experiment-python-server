import logging
from typing import Optional
import threading

from ..local.config import LocalEvaluationConfig
from ..cohort.cohort_loader import CohortLoader
from ..cohort.cohort_storage import CohortStorage
from ..flag.flag_config_api import FlagConfigApi
from ..flag.flag_config_storage import FlagConfigStorage
from ..local.poller import Poller
from ..util.flag_config import get_all_cohort_ids_from_flag, get_all_cohort_ids_from_flags


class DeploymentRunner:
    def __init__(
            self,
            config: LocalEvaluationConfig,
            flag_config_api: FlagConfigApi,
            flag_config_storage: FlagConfigStorage,
            cohort_storage: CohortStorage,
            logger: logging.Logger,
            cohort_loader: Optional[CohortLoader] = None,
    ):
        self.config = config
        self.flag_config_api = flag_config_api
        self.flag_config_storage = flag_config_storage
        self.cohort_storage = cohort_storage
        self.cohort_loader = cohort_loader
        self.lock = threading.Lock()
        self.flag_poller = Poller(self.config.flag_config_polling_interval_millis / 1000, self.__periodic_flag_update)
        if self.cohort_loader:
            self.cohort_poller = Poller(self.config.cohort_sync_config.cohort_polling_interval_millis / 1000,
                                        self.__update_cohorts)
        self.logger = logger

    def start(self):
        with self.lock:
            self.__update_flag_configs()
            self.flag_poller.start()
            if self.cohort_loader:
                self.cohort_poller.start()

    def stop(self):
        self.flag_poller.stop()

    def __periodic_flag_update(self):
        try:
            self.__update_flag_configs()
        except Exception as e:
            self.logger.warning(f"Error while updating flags: {e}")

    def __update_flag_configs(self):
        try:
            flag_configs = self.flag_config_api.get_flag_configs()
        except Exception as e:
            self.logger.warning(f'Failed to fetch flag configs: {e}')
            raise e

        flag_keys = {flag.key for flag in flag_configs}
        self.flag_config_storage.remove_if(lambda f: f.key not in flag_keys)

        if not self.cohort_loader:
            for flag_config in flag_configs:
                self.logger.debug(f"Putting non-cohort flag {flag_config.key}")
                self.flag_config_storage.put_flag_config(flag_config)
            return

        new_cohort_ids = set()
        for flag_config in flag_configs:
            new_cohort_ids.update(get_all_cohort_ids_from_flag(flag_config))

        existing_cohort_ids = self.cohort_storage.get_cohort_ids()
        cohort_ids_to_download = new_cohort_ids - existing_cohort_ids

        # download all new cohorts
        try:
            self.cohort_loader.download_cohorts(cohort_ids_to_download).result()
        except Exception as e:
            self.logger.warning(f"Error while downloading cohorts: {e}")

        # get updated set of cohort ids
        updated_cohort_ids = self.cohort_storage.get_cohort_ids()
        # iterate through new flag configs and check if their required cohorts exist
        for flag_config in flag_configs:
            cohort_ids = get_all_cohort_ids_from_flag(flag_config)
            self.logger.debug(f"Storing flag {flag_config.key}")
            self.flag_config_storage.put_flag_config(flag_config)
            missing_cohorts = cohort_ids - updated_cohort_ids
            if missing_cohorts:
                self.logger.warning(f"Flag {flag_config.key} - failed to load cohorts: {missing_cohorts}")

        # delete unused cohorts
        self._delete_unused_cohorts()
        self.logger.debug(f"Refreshed {len(flag_configs)} flag configs.")

    def __update_cohorts(self):
        cohort_ids = get_all_cohort_ids_from_flags(list(self.flag_config_storage.get_flag_configs().values()))
        try:
            self.cohort_loader.download_cohorts(cohort_ids).result()
        except Exception as e:
            self.logger.warning(f"Error while updating cohorts: {e}")

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
