import json
import logging
from threading import Lock
from typing import Any, List, Dict

from amplitude import Amplitude

from .config import LocalEvaluationConfig
from ..flagresult import FlagResult
from ..assignment import Assignment, AssignmentFilter, AssignmentService
from ..assignment.assignment_service import FLAG_TYPE_MUTUAL_EXCLUSION_GROUP, FLAG_TYPE_HOLDOUT_GROUP
from ..user import User
from ..connection_pool import HTTPConnectionPool
from .poller import Poller
from .evaluation.evaluation import evaluate
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

    def evaluate(self, user: User, flag_keys: List[str] = None) -> Dict[str, Variant]:
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
        user_json = str(user)
        self.logger.debug(f"[Experiment] Evaluate: User: {user_json} - Flags: {self.flags}")
        result_json = evaluate(self.flags, user_json)
        self.logger.debug(f"[Experiment] Evaluate Result: {result_json}")
        evaluation_result = json.loads(result_json)
        filter_result = flag_keys is not None
        assignment_result = {}
        for key, value in evaluation_result.items():
            included = not filter_result or key in flag_keys
            if not value.get('isDefaultVariant') and included:
                variants[key] = Variant(value['variant'].get('key'), value['variant'].get('payload'))
            if included or evaluation_result[key]['type'] == FLAG_TYPE_MUTUAL_EXCLUSION_GROUP or \
                    evaluation_result[key]['type'] == FLAG_TYPE_HOLDOUT_GROUP:
                assignment_result[key] = FlagResult(value)
        if self.assignment_service:
            self.assignment_service.track(Assignment(user, assignment_result))
        return variants

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
            response = conn.request('GET', '/sdk/v1/flags', body, headers)
            response_body = response.read().decode("utf8")
            if response.status != 200:
                raise Exception(
                    f"[Experiment] Get flagConfigs - received error response: ${response.status}: ${response_body}")
            self.logger.debug(f"[Experiment] Got flag configs: {response_body}")
            self.lock.acquire()
            self.flags = response_body
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
