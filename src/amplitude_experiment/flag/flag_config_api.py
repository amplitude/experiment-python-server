import json
import threading
from http.client import HTTPResponse, HTTPConnection, HTTPSConnection
from typing import List, Optional, Callable, Mapping, Union, Tuple

import sseclient

from ..connection_pool import HTTPConnectionPool
from ..util.updater import get_duration_with_jitter
from ..evaluation.types import EvaluationFlag
from ..version import __version__

class FlagConfigApi:
    def get_flag_configs(self) -> List[EvaluationFlag]:
        pass


class FlagConfigApiV2(FlagConfigApi):
    def __init__(self, deployment_key: str, server_url: str, flag_config_poller_request_timeout_millis: int):
        self.deployment_key = deployment_key
        self.server_url = server_url
        self.flag_config_poller_request_timeout_millis = flag_config_poller_request_timeout_millis
        self.__setup_connection_pool()

    def get_flag_configs(self) -> List[EvaluationFlag]:
        return self._get_flag_configs()

    def _get_flag_configs(self) -> List[EvaluationFlag]:
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
            response_json = json.loads(response_body)
            return EvaluationFlag.schema().load(response_json, many=True)
        finally:
            self._connection_pool.release(conn)

    def __setup_connection_pool(self):
        scheme, _, host = self.server_url.split('/', 3)
        timeout = self.flag_config_poller_request_timeout_millis / 1000
        self._connection_pool = HTTPConnectionPool(host, max_size=1, idle_timeout=30,
                                                   read_timeout=timeout, scheme=scheme)


DEFAULT_STREAM_API_KEEP_ALIVE_TIMEOUT_MILLIS = 17000
DEFAULT_STREAM_MAX_CONN_DURATION_MILLIS = 15 * 60 * 1000
DEFAULT_STREAM_MAX_JITTER_MILLIS = 5000


class EventSource:
    def __init__(self, server_url: str, path: str, headers: Mapping[str, str], conn_timeout_millis: int,
                 max_conn_duration_millis: int = DEFAULT_STREAM_MAX_CONN_DURATION_MILLIS,
                 max_jitter_millis: int = DEFAULT_STREAM_MAX_JITTER_MILLIS,
                 keep_alive_timeout_millis: int = DEFAULT_STREAM_API_KEEP_ALIVE_TIMEOUT_MILLIS):
        self.keep_alive_timer: Optional[threading.Timer] = None
        self.server_url = server_url
        self.path = path
        self.headers = headers
        self.conn_timeout_millis = conn_timeout_millis
        self.max_conn_duration_millis = max_conn_duration_millis
        self.max_jitter_millis = max_jitter_millis
        self.keep_alive_timeout_millis = keep_alive_timeout_millis

        self.sse: Optional[sseclient.SSEClient] = None
        self.conn: Optional[HTTPConnection | HTTPSConnection] = None
        self.thread: Optional[threading.Thread] = None
        self._stopped = False
        self.lock = threading.RLock()

    def start(self, on_update: Callable[[str], None], on_error: Callable[[str], None]):
        with self.lock:
            if self.sse is not None:
                self.sse.close()
            if self.conn is not None:
                self.conn.close()

            self.conn, response = self._get_conn()
            if response.status != 200:
                on_error(f"[Experiment] Stream flagConfigs - received error response: ${response.status}: ${response.read().decode('utf-8')}")
                return

            self.sse = sseclient.SSEClient(response, char_enc='utf-8')
            self._stopped = False
            self.thread = threading.Thread(target=self._run, args=[on_update, on_error])
            self.thread.start()
            self.reset_keep_alive_timer(on_error)

    def stop(self):
        with self.lock:
            self._stopped = True
            if self.sse:
                self.sse.close()
            if self.conn:
                self.conn.close()
            if self.keep_alive_timer:
                self.keep_alive_timer.cancel()
            self.sse = None
            self.conn = None
            # No way to stop self.thread, on self.conn.close(),
            # the loop in thread will raise exception, which will terminate the thread.

    def reset_keep_alive_timer(self, on_error: Callable[[str], None]):
        with self.lock:
            if self.keep_alive_timer:
                self.keep_alive_timer.cancel()
            self.keep_alive_timer = threading.Timer(self.keep_alive_timeout_millis / 1000, self.keep_alive_timed_out,
                                                    args=[on_error])
            self.keep_alive_timer.start()

    def keep_alive_timed_out(self, on_error: Callable[[str], None]):
        with self.lock:
            if not self._stopped:
                self.stop()
                on_error("[Experiment] Stream flagConfigs - Keep alive timed out")

    def _run(self, on_update: Callable[[str], None], on_error: Callable[[str], None]):
        try:
            for event in self.sse.events():
                with self.lock:
                    if self._stopped:
                        return
                    self.reset_keep_alive_timer(on_error)
                if event.data == ' ':
                    continue
                on_update(event.data)
        except TimeoutError:
            # Due to connection max time reached, open another one.
            with self.lock:
                if self._stopped:
                    return
                self.stop()
                self.start(on_update, on_error)
        except Exception as e:
            # Closing connection can result in exception here as a way to stop generator.
            with self.lock:
                if self._stopped:
                    return
            on_error("[Experiment] Stream flagConfigs - Unexpected exception" + str(e))

    def _get_conn(self) -> Tuple[Union[HTTPConnection, HTTPSConnection], HTTPResponse]:
        scheme, _, host = self.server_url.split('/', 3)
        connection = HTTPConnection if scheme == 'http:' else HTTPSConnection

        body = None

        conn = connection(host, timeout=get_duration_with_jitter(self.max_conn_duration_millis, self.max_jitter_millis) / 1000)
        try:
            conn.request('GET', self.path, body, self.headers)
            response = conn.getresponse()
        except Exception as e:
            conn.close()
            raise e

        return conn, response


class FlagConfigStreamApi:
    def __init__(self,
                 deployment_key: str,
                 server_url: str,
                 conn_timeout_millis: int,
                 max_conn_duration_millis: int = DEFAULT_STREAM_MAX_CONN_DURATION_MILLIS,
                 max_jitter_millis: int = DEFAULT_STREAM_MAX_JITTER_MILLIS):
        self.deployment_key = deployment_key
        self.server_url = server_url
        self.conn_timeout_millis = conn_timeout_millis
        self.max_conn_duration_millis = max_conn_duration_millis
        self.max_jitter_millis = max_jitter_millis

        self.lock = threading.RLock()

        headers = {
            'Authorization': f"Api-Key {self.deployment_key}",
            'Content-Type': 'application/json;charset=utf-8',
            'X-Amp-Exp-Library': f"experiment-python-server/{__version__}"
        }

        self.eventsource = EventSource(self.server_url, "/sdk/stream/v1/flags", headers, conn_timeout_millis)

    def start(self, on_update: Callable[[List[EvaluationFlag]], None], on_error: Callable[[str], None]):
        with self.lock:
            init_finished_event = threading.Event()
            init_error_event = threading.Event()
            init_updated_event = threading.Event()

            def _on_update(data):
                response_json = json.loads(data)
                flags = EvaluationFlag.schema().load(response_json, many=True)
                if init_finished_event.is_set():
                    on_update(flags)
                else:
                    init_finished_event.set()
                    on_update(flags)
                    init_updated_event.set()

            def _on_error(data):
                if init_finished_event.is_set():
                    on_error(data)
                else:
                    init_error_event.set()
                    init_finished_event.set()
                    on_error(data)

            t = threading.Thread(target=self.eventsource.start, args=[_on_update, _on_error])
            t.start()
            init_finished_event.wait(self.conn_timeout_millis / 1000)
            if t.is_alive() or not init_finished_event.is_set() or init_error_event.is_set():
                self.stop()
                on_error("stream connection timeout error")
                return

            # Wait for first update callback to finish before returning.
            init_updated_event.wait()

    def stop(self):
        with self.lock:
            threading.Thread(target=lambda: self.eventsource.stop()).start()
