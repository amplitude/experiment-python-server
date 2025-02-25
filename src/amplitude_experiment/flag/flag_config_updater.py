import logging
import threading
import time
from typing import List, Callable, Optional

from ..evaluation.types import EvaluationFlag
from ..local.config import LocalEvaluationConfig
from ..cohort.cohort_storage import CohortStorage
from ..flag.flag_config_api import FlagConfigApi, FlagConfigStreamApi
from ..flag.flag_config_storage import FlagConfigStorage
from ..local.poller import Poller
from ..cohort.cohort_loader import CohortLoader
from ..util.flag_config import get_all_cohort_ids_from_flag
from ..util.updater import get_duration_with_jitter


class FlagConfigUpdater:
    def start(self, on_error: Optional[Callable[[str], None]]):
        pass

    def stop(self):
        pass


class FlagConfigUpdaterBase:
    def __init__(self,
                 flag_config_storage: FlagConfigStorage,
                 cohort_loader: CohortLoader,
                 cohort_storage: CohortStorage,
                 logger: logging.Logger):
        self.flag_config_storage = flag_config_storage
        self.cohort_loader = cohort_loader
        self.cohort_storage = cohort_storage
        self.logger = logger

    def update(self, flag_configs: List[EvaluationFlag]):
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


class FlagConfigPoller(FlagConfigUpdaterBase, FlagConfigUpdater):
    def __init__(self, flag_config_api: FlagConfigApi, flag_config_storage: FlagConfigStorage,
                 cohort_loader: CohortLoader,
                 cohort_storage: CohortStorage, config: LocalEvaluationConfig,
                 logger: logging.Logger):
        super().__init__(flag_config_storage, cohort_loader, cohort_storage, logger)

        self.flag_config_api = flag_config_api
        self.flag_poller = Poller(config.flag_config_polling_interval_millis / 1000, self.__periodic_flag_update)
        self.logger = logger

        self.on_error = None

    def start(self, on_error: Optional[Callable[[str], None]]):
        self.stop()
        try:
            self.__update_flag_configs()
        except Exception as e:
            self.logger.warning(f"Error while updating flags: {e}")
            raise e
        self.on_error = on_error
        self.flag_poller.start()

    def stop(self):
        self.flag_poller.stop()

    def __periodic_flag_update(self):
        try:
            self.__update_flag_configs()
        except Exception as e:
            self.logger.warning(f"Error while updating flags: {e}")
            self.stop()
            if self.on_error:
                self.on_error(e)

    def __update_flag_configs(self):
        try:
            flag_configs = self.flag_config_api.get_flag_configs()
        except Exception as e:
            self.logger.warning(f'Failed to fetch flag configs: {e}')
            raise e

        super().update(flag_configs)


class FlagConfigStreamer(FlagConfigUpdaterBase, FlagConfigUpdater):
    def __init__(self, flag_config_stream_api: FlagConfigStreamApi, flag_config_storage: FlagConfigStorage,
                 cohort_loader: CohortLoader,
                 cohort_storage: CohortStorage,
                 logger: logging.Logger):
        super().__init__(flag_config_storage, cohort_loader, cohort_storage, logger)

        self.flag_config_stream_api = flag_config_stream_api
        self.logger = logger

    def start(self, on_error: Optional[Callable[[str], None]]):
        def _on_error(err):
            self.flag_config_stream_api.stop()
            if on_error:
                on_error(err)

        self.flag_config_stream_api.start(super().update, _on_error)

    def stop(self):
        self.flag_config_stream_api.stop()


class FlagConfigUpdaterFallbackRetryWrapper(FlagConfigUpdater):
    def __init__(self, main_updater: FlagConfigUpdater, fallback_updater: Optional[FlagConfigUpdater],
                 retry_delay_millis: int, max_jitter_millis: int,
                 fallback_start_retry_delay_millis: int, fallback_start_retry_max_jitter_millis: int,
                 logger: logging.Logger):
        super().__init__()

        self.main_updater = main_updater
        self.fallback_updater = fallback_updater
        self.retry_delay_millis = retry_delay_millis
        self.max_jitter_millis = max_jitter_millis
        self.fallback_start_retry_delay_millis = fallback_start_retry_delay_millis
        self.fallback_start_retry_max_jitter_millis = fallback_start_retry_max_jitter_millis
        self.logger = logger

        self.main_retry_stopper = threading.Event()
        self.fallback_retry_stopper = threading.Event()

        self.lock = threading.RLock()

    def start(self, on_error: Optional[Callable[[str], None]]):
        with self.lock:
            def _fallback_on_error(err: str):
                pass

            def _main_on_error(err: str):
                self.start_main_retry(_main_on_error)
                try:
                    if self.fallback_updater is not None:
                        self.fallback_updater.start(_fallback_on_error)
                except:
                    self.start_fallback_retry(_fallback_on_error)

            try:
                self.main_updater.start(_main_on_error)
                if self.fallback_updater is not None:
                    self.fallback_updater.stop()
                self.stop_main_retry()
                self.stop_fallback_retry()
            except Exception as e:
                if self.fallback_updater is not None:
                    self.fallback_updater.start(_fallback_on_error)
                    self.start_main_retry(_main_on_error)
                else:
                    raise e

    def stop(self):
        with self.lock:
            self.main_retry_stopper.set()
            self.fallback_retry_stopper.set()
            self.main_updater.stop()
            if self.fallback_updater is not None:
                self.fallback_updater.stop()

    def start_main_retry(self, main_on_error: Callable[[str], None]):
        with self.lock:
            # Schedule main retry indefinitely. Only stop on some signal.
            if self.main_retry_stopper:
                self.main_retry_stopper.set()

            stopper = threading.Event()

            def retry_main():
                while True:
                    time.sleep(get_duration_with_jitter(self.retry_delay_millis, self.max_jitter_millis) / 1000)
                    with self.lock:
                        if stopper.is_set():
                            break
                        try:
                            self.main_updater.start(main_on_error)
                            stopper.set()
                            self.stop_fallback_retry()
                            if self.fallback_updater is not None:
                                self.fallback_updater.stop()
                            break
                        except:
                            pass

            threading.Thread(target=retry_main).start()
            self.main_retry_stopper = stopper

    def start_fallback_retry(self, fallback_on_error: Callable[[str], None]):
        with self.lock:
            # Schedule fallback retry indefinitely. Only stop on some signal.
            if self.fallback_retry_stopper:
                self.fallback_retry_stopper.set()

            if self.fallback_updater is None:
                return

            stopper = threading.Event()

            def retry_fallback():
                while True:
                    time.sleep(get_duration_with_jitter(self.fallback_start_retry_delay_millis,
                                                        self.fallback_start_retry_max_jitter_millis) / 1000)
                    with self.lock:
                        if stopper.is_set():
                            break
                        try:
                            if self.fallback_updater is not None:
                                self.fallback_updater.start(fallback_on_error)
                            stopper.set()
                            break
                        except:
                            pass

            threading.Thread(target=retry_fallback).start()
            self.fallback_retry_stopper = stopper

    def stop_main_retry(self):
        self.main_retry_stopper.set()

    def stop_fallback_retry(self):
        self.fallback_retry_stopper.set()
