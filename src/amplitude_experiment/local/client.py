import json
import logging
from threading import Lock
from typing import Any, List, Dict

from .config import LocalEvaluationConfig
from ..user import User
from ..connection_pool import HTTPConnectionPool
from .poller import Poller
from .evaluation.evaluation import evaluate
from ..variant import Variant
from ..version import __version__


class LocalEvaluationClient:
    """Experiment client for evaluating variants for a user locally."""

    def __init__(self, api_key: str, config : LocalEvaluationConfig = None):
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
        self.logger = logging.getLogger("Amplitude")
        self.logger.addHandler(logging.StreamHandler())
        if self.config.debug:
            self.logger.setLevel(logging.DEBUG)
        self.__setup_connection_pool()
        self.rules = {}
        self.poller = Poller(self.config.flag_config_polling_interval_millis / 1000, self.__do_rules)
        self.lock = Lock()

    def start(self):
        """
        Fetch initial flag configurations and start polling for updates. You must call this function to begin
        polling for flag config updates.
        """
        self.__do_rules()
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
        no_flag_keys = flag_keys is None or len(flag_keys) == 0
        rules = []
        for key, value in self.rules.items():
            if no_flag_keys or key in flag_keys:
                rules.append(value)

        rules_json = json.dumps(rules)
        user_json = str(user)
        self.logger.debug(f"[Experiment] Evaluate: User: {user_json} - Rules: {rules_json}")
        result_json = evaluate(rules_json, user_json)
        self.logger.debug(f"[Experiment] Evaluate Result: {result_json}")
        evaluation_result = json.loads(result_json)
        variants = {}
        for key, value in evaluation_result.items():
            if value.get('isDefaultVariant'):
                continue
            variants[key] = Variant(value['variant'].get('key'), value['variant'].get('payload'))
        return variants

    def __do_rules(self):
        conn = self._connection_pool.acquire()
        headers = {
            'Authorization': f"Api-Key {self.api_key}",
            'Content-Type': 'application/json;charset=utf-8',
            'X-Amp-Exp-Library': f"experiment-python-server/{__version__}"
        }
        body = None
        self.logger.debug('[Experiment] Get flag configs')
        try:
            response = conn.request('GET', '/sdk/rules?eval_mode=local', body, headers)
            response_body = response.read().decode("utf8")
            if response.status != 200:
                raise Exception(f"[Experiment] Get flagConfigs - received error response: ${response.status}: ${response_body}")
            self.logger.debug(f"[Experiment] Got flag configs: {response_body}")
            parsed_rules = self.__parse(json.loads(response_body))
            self.lock.acquire()
            self.rules = parsed_rules
            self.lock.release()
        finally:
            self._connection_pool.release(conn)

    def __parse(self, flag_configs_array):
        flag_configs_record = {}
        for value in flag_configs_array:
            flag_configs_record[value.get('flagKey')] = value
        return flag_configs_record

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
