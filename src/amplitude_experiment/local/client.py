import json
import logging
from typing import Any, List

from .config import LocalEvaluationConfig
from ..user import User
from ..connection_pool import HTTPConnectionPool
from .poller import Poller
from .evaluation.evaluation import evaluate
from ..variant import Variant


class LocalEvaluationClient:
    def __init__(self, api_key, config=None):
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

    def start(self):
        self.__do_rules()
        self.poller.start()

    def evaluate(self, user: User, flag_keys: List[str] = None):
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
            'Content-Type': 'application/json;charset=utf-8'
        }
        body = None
        self.logger.debug('[Experiment] Get flag configs')
        try:
            response = conn.request('POST', '/sdk/rules?eval_mode=local', body, headers)
            response_body = response.read().decode("utf8")
            if response.status != 200:
                raise Exception(f"flagConfigs - received error response: ${response.status}: ${response_body}")
            self.logger.debug(f"[Experiment] Got flag configs: {response_body}")
            self.rules = self.__parse(json.loads(response_body))
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

    def close(self) -> None:
        """
        Close resource like connection pool with client
        """
        self.poller.stop()
        self._connection_pool.close()

    def __enter__(self) -> 'LocalEvaluationClient':
        return self

    def __exit__(self, *exit_info: Any) -> None:
        self.close()
