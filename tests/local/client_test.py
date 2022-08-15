import unittest
from src.amplitude_experiment import LocalEvaluationClient, LocalEvaluationConfig, User, Variant

API_KEY = 'server-qz35UwzJ5akieoAdIgzM4m9MIiOLXLoz'
test_user = User(user_id='test_user')


class LocalEvaluationClientTestCase(unittest.TestCase):
    _local_evaluation_client: LocalEvaluationClient = None

    @classmethod
    def setUpClass(cls) -> None:
        cls._local_evaluation_client = LocalEvaluationClient(API_KEY, LocalEvaluationConfig(debug=True))
        cls._local_evaluation_client.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._local_evaluation_client.stop()

    def test_initialize_raise_error(self):
        self.assertRaises(ValueError, LocalEvaluationClient, "")

    def test_evaluate_all_flags_success(self):
        variants = self._local_evaluation_client.evaluate(test_user)
        expected_variant = Variant('on', 'payload')
        self.assertEqual(expected_variant, variants.get('sdk-local-evaluation-ci-test'))

    def test_evaluate_one_flag_success(self):
        variants = self._local_evaluation_client.evaluate(test_user, ['sdk-local-evaluation-ci-test'])
        expected_variant = Variant('on', 'payload')
        self.assertEqual(expected_variant, variants.get('sdk-local-evaluation-ci-test'))

    def test_invalid_api_key_throw_exception(self):
        invalid_local_api_key = 'client-DvWljIjiiuqLbyjqdvBaLFfEBrAvGuA3'
        with LocalEvaluationClient(invalid_local_api_key) as test_client:
            self.assertRaises(Exception, test_client.start, "[Experiment] Get flagConfigs - received error response")


if __name__ == '__main__':
    unittest.main()
