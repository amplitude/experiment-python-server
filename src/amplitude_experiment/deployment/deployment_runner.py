import logging
from typing import Optional
import threading

from ..flag.flag_config_updater import FlagConfigPoller, FlagConfigStreamer, FlagConfigUpdaterFallbackRetryWrapper
from ..local.config import LocalEvaluationConfig
from ..cohort.cohort_loader import CohortLoader
from ..cohort.cohort_storage import CohortStorage
from ..flag.flag_config_api import FlagConfigApi, FlagConfigStreamApi
from ..flag.flag_config_storage import FlagConfigStorage
from ..local.poller import Poller
from ..util.flag_config import get_all_cohort_ids_from_flags

DEFAULT_STREAM_UPDATER_RETRY_DELAY_MILLIS = 15000
DEFAULT_STREAM_UPDATER_RETRY_DELAY_MAX_JITTER_MILLIS = 1000


class DeploymentRunner:
    def __init__(
            self,
            config: LocalEvaluationConfig,
            flag_config_api: FlagConfigApi,
            flag_config_stream_api: Optional[FlagConfigStreamApi],
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
        self.flag_updater = FlagConfigUpdaterFallbackRetryWrapper(
            FlagConfigPoller(flag_config_api, flag_config_storage, cohort_loader, cohort_storage, config, logger),
            None,
            0, 0, config.flag_config_polling_interval_millis, 0,
            logger
            )
        if flag_config_stream_api:
            self.flag_updater = FlagConfigUpdaterFallbackRetryWrapper(
                FlagConfigStreamer(flag_config_stream_api, flag_config_storage, cohort_loader, cohort_storage, logger),
                self.flag_updater,
                DEFAULT_STREAM_UPDATER_RETRY_DELAY_MILLIS, DEFAULT_STREAM_UPDATER_RETRY_DELAY_MAX_JITTER_MILLIS,
                config.flag_config_polling_interval_millis, 0,
                logger
            )

        self.cohort_poller = None
        if self.cohort_loader:
            self.cohort_poller = Poller(self.config.cohort_sync_config.cohort_polling_interval_millis / 1000,
                                        self.__update_cohorts)
        self.logger = logger

    def start(self):
        with self.lock:
            self.flag_updater.start(None)
            if self.cohort_loader:
                self.cohort_poller.start()

    def stop(self):
        self.flag_updater.stop()
        if self.cohort_poller:
            self.cohort_poller.stop()

    def __update_cohorts(self):
        cohort_ids = get_all_cohort_ids_from_flags(list(self.flag_config_storage.get_flag_configs().values()))
        try:
            self.cohort_loader.download_cohorts(cohort_ids).result()
        except Exception as e:
            self.logger.warning(f"Error while updating cohorts: {e}")
