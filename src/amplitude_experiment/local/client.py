from threading import Lock
from typing import Any, List, Dict, Set

from amplitude import Amplitude

from .config import LocalEvaluationConfig
from .evaluate_options import EvaluateOptions
from ..assignment import Assignment, AssignmentFilter, AssignmentService
from ..exposure import Exposure, ExposureFilter, ExposureService
from ..cohort.cohort import USER_GROUP_TYPE
from ..cohort.cohort_download_api import DirectCohortDownloadApi
from ..cohort.cohort_loader import CohortLoader
from ..cohort.cohort_storage import InMemoryCohortStorage
from ..deployment.deployment_runner import DeploymentRunner
from ..flag.flag_config_api import FlagConfigApiV2, FlagConfigStreamApi
from ..flag.flag_config_storage import InMemoryFlagConfigStorage
from ..user import User
from ..connection_pool import HTTPConnectionPool
from ..evaluation.engine import EvaluationEngine
from ..evaluation.topological_sort import topological_sort
from ..util import deprecated
from ..util.flag_config import get_grouped_cohort_ids_from_flags, get_all_cohort_ids_from_flag
from ..util.user import user_to_evaluation_context
from ..variant import Variant


class LocalEvaluationClient:
    """Experiment client for evaluating variants for a user locally."""

    def __init__(self, api_key: str, config: LocalEvaluationConfig = None):
        """
        Creates a new Experiment LocalEvaluationClient instance.
            Parameters:
                api_key (str): The environment API Key
                config (LocalEvaluationConfig): Config Object

            Returns:
                Experiment Client instance.
        """

        if not api_key:
            raise ValueError("Experiment API key is empty")
        self.engine = EvaluationEngine()
        self.api_key = api_key
        self.config = config or LocalEvaluationConfig()
        self.assignment_service = None
        if config and config.assignment_config:
            instance = Amplitude(config.assignment_config.api_key, config.assignment_config)
            self.assignment_service = AssignmentService(instance, AssignmentFilter(
                config.assignment_config.cache_capacity), config.assignment_config.send_evaluated_props)
        # Exposure service is always instantiated, using deployment key if no api key provided
        self.exposure_service = None
        if config and config.exposure_config:
            exposure_config = config.exposure_config
            exposure_instance = Amplitude(exposure_config.api_key, exposure_config)
            self.exposure_service = ExposureService(exposure_instance, ExposureFilter(exposure_config.cache_capacity))
        self.logger = self.config.logger
        self.__setup_connection_pool()
        self.lock = Lock()
        self.cohort_storage = InMemoryCohortStorage()
        self.flag_config_storage = InMemoryFlagConfigStorage()
        cohort_loader = None
        if self.config.cohort_sync_config:
            cohort_download_api = DirectCohortDownloadApi(self.config.cohort_sync_config.api_key,
                                                          self.config.cohort_sync_config.secret_key,
                                                          self.config.cohort_sync_config.max_cohort_size,
                                                          self.config.cohort_sync_config.cohort_server_url,
                                                          self.logger)

            cohort_loader = CohortLoader(cohort_download_api, self.cohort_storage)
        flag_config_api = FlagConfigApiV2(api_key, self.config.server_url,
                                          self.config.flag_config_poller_request_timeout_millis)
        flag_config_stream_api = None
        if self.config.stream_updates:
            flag_config_stream_api = FlagConfigStreamApi(api_key, self.config.stream_server_url, self.config.stream_flag_conn_timeout)

        self.deployment_runner = DeploymentRunner(self.config, flag_config_api, flag_config_stream_api,
                                                  self.flag_config_storage, self.cohort_storage, self.logger,
                                                  cohort_loader)

    def start(self):
        """
        Fetch initial flag configurations and start polling for updates. You must call this function to begin
        polling for flag config updates.
        """
        self.deployment_runner.start()

    def evaluate_v2(self, user: User, flag_keys: Set[str] = None, options: EvaluateOptions = None) -> Dict[str, Variant]:
        """
        Locally evaluates flag variants for a user.

        This function will only evaluate flags for the keys specified in the flag_keys argument. If flag_keys is
        missing or None, all flags are evaluated. This function differs from evaluate as it will return a default
        variant object if the flag was evaluated but the user was not assigned (i.e. off).

            Parameters:
                user (User): The user to evaluate
                flag_keys (Set[str]): The flags to evaluate with the user. If empty, all flags are evaluated.
                options (EvaluateOptions): Optional evaluation options.

            Returns:
                The evaluated variants.
        """
        
        flag_configs = self.flag_config_storage.get_flag_configs()
        if flag_configs is None or len(flag_configs) == 0:
            return {}
        self.logger.debug(f"[Experiment] Evaluate: user={user} - Flags: {flag_configs}")
        sorted_flags = topological_sort(flag_configs, flag_keys and list(flag_keys))
        if not sorted_flags:
            return {}

        # Check if all required cohorts are in storage, if not log a warning
        self._required_cohorts_in_storage(sorted_flags)
        if self.config.cohort_sync_config:
            user = self._enrich_user_with_cohorts(user, flag_configs)

        context = user_to_evaluation_context(user)
        result = self.engine.evaluate(context, sorted_flags)
        variants = {
            k: Variant(
                key=v.key,
                value=v.value,
                payload=v.payload,
                metadata=v.metadata
            ) for k, v in result.items()
        }
        self.logger.debug(f"[Experiment] Evaluate Result: {variants}")
        if self.exposure_service is not None and options and options.tracks_exposure is True:
            self.exposure_service.track(Exposure(user, variants))
        if self.assignment_service is not None:
            # @deprecated Assignment tracking is deprecated. Use ExposureService with Exposure tracking instead.
            self.assignment_service.track(Assignment(user, variants))
        return variants

    @deprecated("Use evaluate_v2")
    def evaluate(self, user: User, flag_keys: List[str] = None) -> Dict[str, Variant]:
        """
        Locally evaluates flag variants for a user.

        This function will only evaluate flags for the keys specified in the flag_keys argument. If flag_keys is
        missing, all flags are evaluated.

            Parameters:
                user (User): The user to evaluate
                flag_keys (List[str]): The flags to evaluate with the user. If empty, all flags are evaluated.

            Returns:
                The evaluated variants.
        """
        flag_keys = set(flag_keys) if flag_keys is not None else None
        variants = self.evaluate_v2(user, flag_keys)
        return self.__filter_default_variants(variants)

    def __setup_connection_pool(self):
        scheme, _, host = self.config.server_url.split('/', 3)
        timeout = self.config.flag_config_poller_request_timeout_millis / 1000
        self._connection_pool = HTTPConnectionPool(host, max_size=1, idle_timeout=30,
                                                   read_timeout=timeout, scheme=scheme)

    def stop(self) -> None:
        """
        Stop polling for flag configurations. Close resource like connection pool with client
        """
        self.deployment_runner.stop()
        self._connection_pool.close()

    def __enter__(self) -> 'LocalEvaluationClient':
        return self

    def __exit__(self, *exit_info: Any) -> None:
        self.stop()

    @staticmethod
    def __filter_default_variants(variants: Dict[str, Variant]) -> Dict[str, Variant]:
        def is_default_variant(variant: Variant) -> bool:
            default = False if variant.metadata.get('default') is None else variant.metadata.get('default')
            deployed = True if variant.metadata.get('deployed') is None else variant.metadata.get('deployed')
            return default or not deployed

        return {key: variant for key, variant in variants.items() if not is_default_variant(variant)}

    def _required_cohorts_in_storage(self, flag_configs: List) -> None:
        stored_cohort_ids = self.cohort_storage.get_cohort_ids()
        for flag in flag_configs:
            flag_cohort_ids = get_all_cohort_ids_from_flag(flag)
            missing_cohorts = flag_cohort_ids - stored_cohort_ids
            if missing_cohorts:
                message = (
                    f"Evaluating flag {flag.key} dependent on cohorts {flag_cohort_ids} "
                    f"without {missing_cohorts} in storage"
                    if self.config.cohort_sync_config
                    else f"Evaluating flag {flag.key} dependent on cohorts {flag_cohort_ids} without "
                         f"cohort syncing configured"
                )
                self.logger.warning(message)

    def _enrich_user_with_cohorts(self, user: User, flag_configs: Dict) -> User:
        grouped_cohort_ids = get_grouped_cohort_ids_from_flags(list(flag_configs.values()))

        if USER_GROUP_TYPE in grouped_cohort_ids:
            user_cohort_ids = grouped_cohort_ids[USER_GROUP_TYPE]
            if user_cohort_ids and user.user_id:
                user.cohort_ids = list(self.cohort_storage.get_cohorts_for_user(user.user_id, user_cohort_ids))

        if user.groups:
            for group_type, group_names in user.groups.items():
                group_name = group_names[0] if group_names else None
                if not group_name:
                    continue
                cohort_ids = grouped_cohort_ids.get(group_type, [])
                if not cohort_ids:
                    continue
                user.add_group_cohort_ids(
                    group_type,
                    group_name,
                    list(self.cohort_storage.get_cohorts_for_group(group_type, group_name, cohort_ids))
                )
        return user
