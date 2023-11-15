import unittest

from src.amplitude_experiment import RemoteEvaluationClient, Variant, User, RemoteEvaluationConfig

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
        with RemoteEvaluationClient(API_KEY, RemoteEvaluationConfig(debug=False, fetch_retries=1, fetch_timeout_millis=1)) as client:
            user = User(user_id='test_user')
            variants = client.fetch(user)
            self.assertEqual({}, variants)


if __name__ == '__main__':
    unittest.main()
