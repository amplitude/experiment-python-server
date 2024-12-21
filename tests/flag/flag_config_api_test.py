import json
import logging
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

from amplitude_experiment.evaluation.types import EvaluationFlag

from amplitude_experiment.flag.flag_config_api import FlagConfigStreamApi


def response(code: int, body: dict = None):
    mock_response = MagicMock()
    mock_response.status = code
    if body is not None:
        mock_response.read.return_value = json.dumps(body).encode()
    return mock_response


BARE_FLAG = [{
    "key": "flag",
    "variants": {},
    "segments": [
        {
            "conditions": [
                [
                    {
                        "selector": ["context", "user", "cohort_ids"],
                        "op": "set contains any",
                        "values": ["COHORT_ID"],
                    }
                ]
            ],
        }
    ]
}]


class FlagConfigStreamApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.api = FlagConfigStreamApi("deployment_key", "server_url", 2000, 5000, 0)
        self.success_count = 0
        self.error_count = 0
    def on_success(self, data):
        self.success_count += (1 if data[0].key == "flag" else 0)
    def on_error(self, data):
        self.error_count += 1

    def test_connect_and_get_data_success(self):
        with patch.object(self.api.eventsource, 'start') as es:
            assert self.success_count == 0
            threading.Thread(target=self.api.start, args=[self.on_success, self.on_error]).start()
            time.sleep(1)
            es.call_args[0][0](json.dumps(BARE_FLAG))
            assert self.success_count == 1
            assert self.error_count == 0

    def test_connect_timeout(self):
        with patch.object(self.api.eventsource, 'start') as es:
            assert self.success_count == 0
            assert self.error_count == 0
            threading.Thread(target=lambda: self.api.start(self.on_success, self.on_error)).start()
            time.sleep(3)
            assert self.success_count == 0
            assert self.error_count == 1

    def test_connect_error(self):
        with patch.object(self.api.eventsource, 'start') as es:
            assert self.success_count == 0
            assert self.error_count == 0
            threading.Thread(target=lambda: self.api.start(self.on_success, self.on_error)).start()
            time.sleep(1)
            es.call_args[0][1]('error')
            assert self.success_count == 0
            assert self.error_count == 1

    def test_connect_success_but_error_later(self):
        with patch.object(self.api.eventsource, 'start') as es:
            assert self.success_count == 0
            assert self.error_count == 0
            threading.Thread(target=lambda: self.api.start(self.on_success, self.on_error)).start()
            time.sleep(1)
            es.call_args[0][0](json.dumps(BARE_FLAG))
            assert self.success_count == 1
            assert self.error_count == 0
            es.call_args[0][1]('error')
            assert self.success_count == 1
            assert self.error_count == 1


if __name__ == '__main__':
    unittest.main()
