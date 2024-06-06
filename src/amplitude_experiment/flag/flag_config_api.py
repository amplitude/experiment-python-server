import json
from typing import List

from ..version import __version__

from src.amplitude_experiment.connection_pool import HTTPConnectionPool


class FlagConfigApi:
    def get_flag_configs(self) -> List:
        pass


class FlagConfigApiV2(FlagConfigApi):
    def __init__(self, deployment_key: str, server_url: str, flag_config_poller_request_timeout_millis: int):
        self.deployment_key = deployment_key
        self.server_url = server_url
        self.flag_config_poller_request_timeout_millis = flag_config_poller_request_timeout_millis

    def get_flag_configs(self) -> List:
        return self._get_flag_configs()

    def _get_flag_configs(self) -> List:
        conn = self._connection_pool.acquire()
        headers = {
            'Authorization': f"Api-Key {self.deployment_key}",
            'Content-Type': 'application/json;charset=utf-8',
            'X-Amp-Exp-Library': f"experiment-python-server/{__version__}"
        }
        body = None
        try:
            response = conn.request('GET', '/sdk/v2/flags?v=0', body, headers)
            response_body = response.read().decode("utf8")
            if response.status != 200:
                raise Exception(
                    f"[Experiment] Get flagConfigs - received error response: ${response.status}: ${response_body}")
            flags = json.loads(response_body)
            return flags
        finally:
            self._connection_pool.release(conn)

    def __setup_connection_pool(self):
        scheme, _, host = self.server_url.split('/', 3)
        timeout = self.flag_config_poller_request_timeout_millis / 1000
        self._connection_pool = HTTPConnectionPool(host, max_size=1, idle_timeout=30,
                                                   read_timeout=timeout, scheme=scheme)
