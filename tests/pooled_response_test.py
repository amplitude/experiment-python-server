import json
import logging
import socket
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from src.amplitude_experiment import RemoteEvaluationClient, RemoteEvaluationConfig, User
from src.amplitude_experiment.cohort.cohort_download_api import DirectCohortDownloadApi
from src.amplitude_experiment.flag.flag_config_api import FlagConfigApiV2


class ResponseServer:
    def __init__(self, responses):
        self.responses = responses
        self.requests = []
        self.lock = threading.Lock()
        owner = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'

            def handle_one_request(self):
                try:
                    super().handle_one_request()
                except ConnectionResetError:
                    self.close_connection = True

            def do_POST(self):
                self.reply()

            def do_GET(self):
                self.reply()

            def reply(self):
                length = int(self.headers.get('Content-Length', '0'))
                if length:
                    self.rfile.read(length)
                with owner.lock:
                    index = len(owner.requests)
                    owner.requests.append((self.path, self.client_address[1]))
                status, body, stall = owner.responses[min(index, len(owner.responses) - 1)]
                self.send_response(status)
                self.send_header('Content-Length', str(len(body) + (99 if stall else 0)))
                self.end_headers()
                try:
                    self.wfile.write(body)
                    self.wfile.flush()
                except BrokenPipeError:
                    return
                if stall:
                    time.sleep(0.3)

            def log_message(self, *_):
                pass

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    @property
    def url(self):
        return f'http://127.0.0.1:{self.server.server_address[1]}'


class PooledResponseTest(unittest.TestCase):
    def remote_client(self, url):
        return RemoteEvaluationClient('test-key', RemoteEvaluationConfig(
            server_url=url, fetch_retries=1, fetch_retry_backoff_min_millis=0,
            fetch_timeout_millis=100, connection_pool_max_size=1))

    def test_remote_error_body_then_retry(self):
        with ResponseServer([(503, b'error', False), (200, b'{}', False)]) as server:
            with self.remote_client(server.url) as client:
                self.assertEqual({}, client.fetch_v2(User(user_id='test-user')))
            self.assertEqual(2, len(server.requests))

    def test_remote_success_reuses_keep_alive_connection(self):
        with ResponseServer([(200, b'{}', False), (200, b'{}', False)]) as server:
            with self.remote_client(server.url) as client:
                self.assertEqual({}, client.fetch_v2(User(user_id='first')))
                self.assertEqual({}, client.fetch_v2(User(user_id='second')))
            self.assertEqual(2, len(server.requests))
            self.assertEqual(server.requests[0][1], server.requests[1][1])

    def test_remote_stalled_error_body_then_retry(self):
        with ResponseServer([(503, b'e', True), (200, b'{}', False)]) as server:
            with self.remote_client(server.url) as client:
                self.assertEqual({}, client.fetch_v2(User(user_id='test-user')))
            self.assertEqual(2, len(server.requests))

    def test_remote_stalled_success_body_then_retry(self):
        with ResponseServer([(200, b'{', True), (200, b'{}', False)]) as server:
            with self.remote_client(server.url) as client:
                self.assertEqual({}, client.fetch_v2(User(user_id='test-user')))
            self.assertEqual(2, len(server.requests))

    def test_remote_serialization_failure_releases_pool_slot(self):
        with self.remote_client('http://127.0.0.1:1') as client:
            with patch.object(User, 'to_json', side_effect=ValueError('bad user')):
                with self.assertRaises(ValueError):
                    client._RemoteEvaluationClient__do_fetch(User(user_id='test-user'))
            conn = client._connection_pool.acquire(blocking=False)
            client._connection_pool.release(conn)

    def test_flag_config_stalled_body_does_not_poison_next_request(self):
        with ResponseServer([(503, b'e', True), (200, b'[]', False)]) as server:
            api = FlagConfigApiV2('test-key', server.url, 100)
            try:
                with self.assertRaises(socket.timeout):
                    api.get_flag_configs()
                self.assertEqual([], api.get_flag_configs())
                self.assertEqual(2, len(server.requests))
            finally:
                api._connection_pool.close()

    def test_cohort_202_body_then_success(self):
        cohort_body = json.dumps({'cohortId': 'cohort', 'lastModified': 1, 'size': 1,
                                  'groupType': 'User', 'memberIds': ['user']}).encode()
        with ResponseServer([(202, b'pending', False), (200, cohort_body, False)]) as server:
            api = DirectCohortDownloadApi('key', 'secret', 100, server.url, logging.getLogger('test'))
            api._connection_pool.max_size = 1
            try:
                first = api._get_cohort_members_request('cohort', None)
                with first as response:
                    self.assertEqual(202, response.status)
                with api._get_cohort_members_request('cohort', None) as response:
                    self.assertEqual(200, response.status)
                    self.assertEqual(['user'], json.loads(response.read())['memberIds'])
                self.assertEqual(2, len(server.requests))
            finally:
                api._connection_pool.close()

    def test_cohort_stalled_success_body_does_not_poison_next_request(self):
        cohort_body = json.dumps({'cohortId': 'cohort', 'lastModified': 1, 'size': 1,
                                  'groupType': 'User', 'memberIds': ['user']}).encode()
        with ResponseServer([(200, b'{', True), (200, cohort_body, False)]) as server:
            api = DirectCohortDownloadApi('key', 'secret', 100, server.url, logging.getLogger('test'))
            api._connection_pool.max_size = 1
            api._connection_pool.read_timeout = 0.1
            try:
                with self.assertRaises(socket.timeout):
                    with api._get_cohort_members_request('cohort', None) as response:
                        response.read()
                with api._get_cohort_members_request('cohort', None) as response:
                    self.assertEqual(['user'], json.loads(response.read())['memberIds'])
                self.assertEqual(2, len(server.requests))
            finally:
                api._connection_pool.close()


if __name__ == '__main__':
    unittest.main()
