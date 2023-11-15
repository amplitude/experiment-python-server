import json
import logging
from threading import Lock
from typing import Any, List, Dict, Set

from amplitude import Amplitude

from .config import LocalEvaluationConfig
from .topological_sort import topological_sort
from ..assignment import Assignment, AssignmentFilter, AssignmentService
from ..user import User
from ..connection_pool import HTTPConnectionPool
from .poller import Poller
from .evaluation.evaluation import evaluate
from ..util import deprecated
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
        self.flags = None
        self.poller = Poller(self.config.flag_config_polling_interval_millis / 1000, self.__do_flags)
        self.lock = Lock()

    def start(self):
        """
        Fetch initial flag configurations and start polling for updates. You must call this function to begin
        polling for flag config updates.
        """
        self.__do_flags()
        self.poller.start()

    def evaluate_v2(self, user: User, flag_keys: Set[str] = None) -> Dict[str, Variant]:
        """
         Locally evaluates flag variants for a user.
         Parameters:
                user (User): The user to evaluate
                flag_keys (List[str]): The flags to evaluate with the user. If empty, all flags from the flag cache are evaluated.

            Returns:
                The evaluated variants.
        """
        variants = {}
        if self.flags is None or len(self.flags) == 0:
            return variants
        self.logger.debug(f"[Experiment] Evaluate: user={user} - Flags: {self.flags}")
        context = self.__user_to_evaluation_context(user)
        sorted_flags = topological_sort(self.flags, flag_keys)
        flags_json = json.dumps(sorted_flags)
        context_json = json.dumps(context)
        result_json = evaluate(flags_json, context_json)
        self.logger.debug(f"[Experiment] Evaluate Result: {result_json}")
        evaluation_result = json.loads(result_json)
        error = evaluation_result.get('error')
        if error is not None:
            self.logger.error(f"[Experiment] Evaluation failed: {error}")
            return variants
        result = evaluation_result.get('result')
        if result is None:
            return variants
        for flag_key, variant in result.items():
            variants[flag_key] = Variant(
                key=variant.get('key'),
                value=variant.get('value'),
                payload=variant.get('payload'),
                metadata=variant.get('metadata')
            )
        if self.assignment_service is not None:
            self.assignment_service.track(Assignment(user, variants))
        return variants

    @deprecated("Use evaluate_v2")
    def evaluate(self, user: User, flag_keys: List[str] = None) -> Dict[str, Variant]:
        """
         Locally evaluates flag variants for a user.
         Parameters:
                user (User): The user to evaluate
                flag_keys (List[str]): The flags to evaluate with the user. If empty, all flags from the flag cache are evaluated.

            Returns:
                The evaluated variants.
        """
        flag_keys = set(flag_keys) if flag_keys is not None else None
        variants = self.evaluate_v2(user, flag_keys)
        return self.__filter_default_variants(variants)

    def __do_flags(self):
        conn = self._connection_pool.acquire()
        headers = {
            'Authorization': f"Api-Key {self.api_key}",
            'Content-Type': 'application/json;charset=utf-8',
            'X-Amp-Exp-Library': f"experiment-python-server/{__version__}"
        }
        body = None
        self.logger.debug('[Experiment] Get flag configs')
        try:
            response = conn.request('GET', '/sdk/v2/flags?v=0', body, headers)
            response_body = response.read().decode("utf8")
            if response.status != 200:
                raise Exception(
                    f"[Experiment] Get flagConfigs - received error response: ${response.status}: ${response_body}")
            flags = json.loads(response_body)
            flags_dict = {flag['key']: flag for flag in flags}
            self.logger.debug(f"[Experiment] Got flag configs: {flags}")
            self.lock.acquire()
            self.flags = flags_dict
            self.lock.release()
        finally:
            self._connection_pool.release(conn)

    def __setup_connection_pool(self):
        scheme, _, host = self.config.server_url.split('/', 3)
        timeout = self.config.flag_config_poller_request_timeout_millis / 1000
        self._connection_pool = HTTPConnectionPool(host, max_size=1, idle_timeout=30,
                                                   read_timeout=timeout, scheme=scheme)

    def stop(self) -> None:
        """
        Stop polling for flag configurations. Close resource like connection pool with client
        """
        self.poller.stop()
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

    @staticmethod
    def __user_to_evaluation_context(user: User) -> Dict[str, Any]:
        user_groups = user.groups
        user_group_properties = user.group_properties
        user_dict = user.__dict__.copy()
        user_dict.pop('groups')
        user_dict.pop('group_properties')
        context = {'user': user_dict}
        if user_groups is None:
            return context
        groups = {}
        for group_type in user_groups:
            group_name = groups[group_type]
            if type(group_name) == list and len(group_name) > 0:
                group_name = group_name[0]
            groups[group_type] = {'group_name': group_name}
            group_properties_type = user_group_properties[group_type]
            if group_properties_type is None or type(group_properties_type != dict):
                continue
            group_properties_name = group_properties_type[group_name]
            if group_properties_name is None or type(group_properties_name != dict):
                continue
            groups[group_type].update(group_properties_name)
        context['groups'] = groups
        return context


