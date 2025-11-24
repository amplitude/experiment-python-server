import json
import unittest
from unittest import mock

from parameterized import parameterized

from src.amplitude_experiment import RemoteEvaluationClient, Variant, User, RemoteEvaluationConfig
from src.amplitude_experiment.exception import FetchException
from src.amplitude_experiment.remote.fetch_options import FetchOptions

API_KEY = 'client-DvWljIjiiuqLbyjqdvBaLFfEBrAvGuA3'
SERVER_URL = 'https://api.lab.amplitude.com/sdk/vardata'


class RemoteEvaluationClientTestCase(unittest.TestCase):

    def setUp(self):
        self.client = None

    def test_initialize_raise_error(self):
        self.assertRaises(ValueError, RemoteEvaluationClient, "")

    def test_fetch(self):
        with RemoteEvaluationClient(API_KEY) as client:
            expected_variant = Variant(key='on', value='on', payload='payload')
            user = User(user_id='test_user')
            variants = client.fetch(user)
            variant_name = 'sdk-ci-test'
            self.assertIn(variant_name, variants)
            self.assertEqual(expected_variant, variants.get(variant_name))

    def callback_for_async(self, user, variants):
        expected_variant = Variant('on', 'payload')
        variant_name = 'sdk-ci-test'
        self.assertIn(variant_name, variants)
        self.assertEqual(expected_variant, variants.get(variant_name))
        self.client.close()

    def test_fetch_async(self):
        self.client = RemoteEvaluationClient(API_KEY, RemoteEvaluationConfig(debug=False))
        user = User(user_id='test_user')
        self.client.fetch_async(user, self.callback_for_async)

    def test_fetch_failed_with_retry(self):
        with RemoteEvaluationClient(API_KEY, RemoteEvaluationConfig(debug=False, fetch_retries=1,
                                                                    fetch_timeout_millis=1)) as client:
            user = User(user_id='test_user')
            variants = client.fetch(user)
            self.assertEqual({}, variants)

    def test_fetch_with_fetch_options(self):
        with RemoteEvaluationClient(API_KEY) as client:
            user = User(user_id='test_user')

            mock_conn = mock.MagicMock()
            client._connection_pool.acquire = lambda: mock_conn
            mock_conn.request.return_value = mock.MagicMock(status=200)
            mock_conn.request.return_value.read.return_value = json.dumps({
                'sdk-ci-test': {
                    'key': 'on'
                }
            }).encode('utf8')

            variants = client.fetch_v2(user, FetchOptions(tracksAssignment=False, tracksExposure=True))
            self.assertIn('sdk-ci-test', variants)
            mock_conn.request.assert_called_once_with('POST', '/sdk/v2/vardata?v=0', mock.ANY, {
                'Authorization': f"Api-Key {API_KEY}",
                'Content-Type': 'application/json;charset=utf-8',
                'X-Amp-Exp-Track': 'no-track',
                'X-Amp-Exp-Exposure-Track': 'track'
            })

            mock_conn.request.reset_mock()

            variants = client.fetch_v2(user, FetchOptions(tracksAssignment=True, tracksExposure=False))
            self.assertIn('sdk-ci-test', variants)
            mock_conn.request.assert_called_once_with('POST', '/sdk/v2/vardata?v=0', mock.ANY, {
                'Authorization': f"Api-Key {API_KEY}",
                'Content-Type': 'application/json;charset=utf-8',
                'X-Amp-Exp-Track': 'track',
                'X-Amp-Exp-Exposure-Track': 'no-track'
            })

    @parameterized.expand([
        (300, "Fetch Exception 300", True),
        (400, "Fetch Exception 400", False),
        (429, "Fetch Exception 429", True),
        (500, "Fetch Exception 500", True),
        (000, "Other Exception", True),
    ])
    @mock.patch("src.amplitude_experiment.remote.client.RemoteEvaluationClient._RemoteEvaluationClient__retry_fetch")
    @mock.patch("src.amplitude_experiment.remote.client.RemoteEvaluationClient._RemoteEvaluationClient__do_fetch")
    def test_fetch_retry_with_response(self, response_code, error_message, should_call_retry, mock_do_fetch,
                                       mock_retry_fetch):
        if response_code == 000:
            mock_do_fetch.side_effect = Exception(error_message)
        else:
            mock_do_fetch.side_effect = FetchException(response_code, error_message)
        instance = RemoteEvaluationClient(API_KEY, RemoteEvaluationConfig(fetch_retries=1))
        user = User(user_id='test_user')
        instance.fetch_v2(user)
        mock_do_fetch.assert_called_once_with(user, None)
        self.assertEqual(should_call_retry, mock_retry_fetch.called)


if __name__ == '__main__':
    unittest.main()
