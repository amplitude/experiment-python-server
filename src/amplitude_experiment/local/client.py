import json
import logging
from threading import Lock
from typing import Any, List, Dict, Set

from amplitude import Amplitude

from .config import LocalEvaluationConfig
from .topological_sort import topological_sort
from ..assignment import Assignment, AssignmentFilter, AssignmentService
from ..cohort.cohort_description import USER_GROUP_TYPE
from ..cohort.cohort_download_api import DirectCohortDownloadApi
from ..cohort.cohort_loader import CohortLoader
from ..cohort.cohort_storage import InMemoryCohortStorage
from ..deployment.deployment_runner import DeploymentRunner
from ..flag.flag_config_api import FlagConfigApiV2
from ..flag.flag_config_storage import InMemoryFlagConfigStorage
from ..user import User
from ..connection_pool import HTTPConnectionPool
from .poller import Poller
from .evaluation.evaluation import evaluate
from ..util import deprecated
from ..util.flag_config import get_grouped_cohort_ids_from_flags
from ..util.user import user_to_evaluation_context
from ..util.variant import evaluation_variants_json_to_variants
from ..variant import Variant
from ..version import __version__


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
        self.api_key = api_key
        self.config = config or LocalEvaluationConfig()
        self.assignment_service = None
        if config and config.assignment_config:
            instance = Amplitude(config.assignment_config.api_key, config.assignment_config)
            self.assignment_service = AssignmentService(instance, AssignmentFilter(
                config.assignment_config.cache_capacity))
        self.logger = logging.getLogger("Amplitude")
        self.logger.addHandler(logging.StreamHandler())
        if self.config.debug:
            self.logger.setLevel(logging.DEBUG)
        self.__setup_connection_pool()
        self.lock = Lock()
        self.cohort_storage = InMemoryCohortStorage()
        self.flag_config_storage = InMemoryFlagConfigStorage()
        cohort_loader = None
        if self.config.cohort_sync_config:
            cohort_download_api = DirectCohortDownloadApi(self.config.cohort_sync_config.api_key,
                                                          self.config.cohort_sync_config.secret_key,
                                                          self.config.cohort_sync_config.max_cohort_size,
                                                          self.config.debug)
            cohort_loader = CohortLoader(cohort_download_api, self.cohort_storage)
        flag_config_api = FlagConfigApiV2(api_key, self.config.server_url,
                                          self.config.flag_config_poller_request_timeout_millis)
        self.deployment_runner = DeploymentRunner(self.config, flag_config_api, self.flag_config_storage,
                                                  self.cohort_storage, cohort_loader)

    def start(self):
        """
        Fetch initial flag configurations and start polling for updates. You must call this function to begin
        polling for flag config updates.
        """
        self.deployment_runner.start()

    def evaluate_v2(self, user: User, flag_keys: Set[str] = None) -> Dict[str, Variant]:
        """
        Locally evaluates flag variants for a user.

        This function will only evaluate flags for the keys specified in the flag_keys argument. If flag_keys is
        missing or None, all flags are evaluated. This function differs from evaluate as it will return a default
        variant object if the flag was evaluated but the user was not assigned (i.e. off).

            Parameters:
                user (User): The user to evaluate
                flag_keys (List[str]): The flags to evaluate with the user. If empty, all flags are evaluated.

            Returns:
                The evaluated variants.
        """
        flag_configs = self.flag_config_storage.get_flag_configs()
        if flag_configs is None or len(flag_configs) == 0:
            return {}
        self.logger.debug(f"[Experiment] Evaluate: user={user} - Flags: {flag_configs}")
        flag_configs = self.flag_config_storage.get_flag_configs()
        sorted_flags = topological_sort(flag_configs, flag_keys)
        if not sorted_flags:
            return {}
        enriched_user = self.enrich_user(user, flag_configs)
        context = user_to_evaluation_context(enriched_user)
        flags_json = json.dumps(sorted_flags)
        context_json = json.dumps(context)
        result_json = evaluate(flags_json, context_json)
        self.logger.debug(f"[Experiment] Evaluate Result: {result_json}")
        evaluation_result = json.loads(result_json)
        error = evaluation_result.get('error')
        if error is not None:
            self.logger.error(f"[Experiment] Evaluation failed: {error}")
            return {}
        result = evaluation_result.get('result')
        if result is None:
            return {}
        variants = evaluation_variants_json_to_variants(result)
        if self.assignment_service is not None:
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

    def enrich_user(self, user: User, flag_configs: Dict) -> User:
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
