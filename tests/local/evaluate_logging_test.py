import logging
import unittest
from unittest.mock import patch

from src.amplitude_experiment import LocalEvaluationClient, LocalEvaluationConfig, User
from src.amplitude_experiment.evaluation.types import EvaluationFlag

API_KEY = 'server-api-key'


def always_on_flag(key: str) -> EvaluationFlag:
    return EvaluationFlag.from_dict({
        'key': key,
        'variants': {'on': {'key': 'on', 'value': 'on'}},
        'segments': [{'variant': 'on'}],
    })


def forbidden_repr(self) -> str:
    raise AssertionError('a flag config was rendered to text')


class LocalEvaluationClientEvaluateLoggingTestCase(unittest.TestCase):

    def _client(self, debug: bool) -> LocalEvaluationClient:
        # Never started: no poller thread, no network call.
        logger = logging.getLogger(f'evaluate-logging-test-{debug}')
        logger.setLevel(logging.DEBUG if debug else logging.WARNING)
        client = LocalEvaluationClient(API_KEY, LocalEvaluationConfig(logger=logger))
        client.flag_config_storage.put_flag_config(always_on_flag('flag-a'))
        client.flag_config_storage.put_flag_config(always_on_flag('flag-b'))
        return client

    def test_evaluate_does_not_render_flag_configs_when_debug_is_disabled(self):
        client = self._client(debug=False)

        with patch.object(EvaluationFlag, '__repr__', forbidden_repr):
            variants = client.evaluate_v2(User(user_id='user'), {'flag-a'})

        self.assertEqual('on', variants['flag-a'].value)

    def test_evaluate_logs_flag_configs_and_result_when_debug_is_enabled(self):
        client = self._client(debug=True)

        with self.assertLogs(client.logger, logging.DEBUG) as logs:
            client.evaluate_v2(User(user_id='user'), {'flag-a'})

        self.assertEqual(2, len(logs.output))
        self.assertIn('Evaluate: user={"device_id": null, "user_id": "user"', logs.output[0])
        self.assertIn("EvaluationFlag(key='flag-b'", logs.output[0])
        self.assertIn("Evaluate Result: {'flag-a': ", logs.output[1])


if __name__ == '__main__':
    unittest.main()
