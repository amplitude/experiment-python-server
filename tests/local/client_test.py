import time
import unittest
from src.amplitude_experiment import LocalEvaluationClient, LocalEvaluationConfig, User, Variant
from src.amplitude_experiment.assignment import AssignmentConfig

API_KEY = 'server-qz35UwzJ5akieoAdIgzM4m9MIiOLXLoz'
test_user = User(user_id='test_user')
test_user_2 = User(user_id='user_id', device_id='device_id')


class LocalEvaluationClientTestCase(unittest.TestCase):
    _local_evaluation_client: LocalEvaluationClient = None

    @classmethod
    def setUpClass(cls) -> None:
        cls._local_evaluation_client = LocalEvaluationClient(API_KEY, LocalEvaluationConfig(debug=False))
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

    def test_evaluate_with_dependencies_success(self):
        variants = self._local_evaluation_client.evaluate(test_user_2)
        expected_variant = Variant('control', None)
        self.assertEqual(expected_variant, variants.get('sdk-ci-local-dependencies-test'))

    def test_evaluate_with_dependencies_and_flag_keys_success(self):
        variants = self._local_evaluation_client.evaluate(test_user_2, ['sdk-ci-local-dependencies-test'])
        expected_variant = Variant('control', None)
        self.assertEqual(expected_variant, variants.get('sdk-ci-local-dependencies-test'))

    def test_evaluate_with_dependencies_and_flag_keys_not_exist_no_variant(self):
        variants = self._local_evaluation_client.evaluate(test_user_2, ['does-not-exist'])
        expected_variant = None
        self.assertEqual(expected_variant, variants.get('sdk-ci-local-dependencies-test'))

    def test_evaluate_with_dependencies_variant_holdout(self):
        variants = self._local_evaluation_client.evaluate(test_user_2)
        expected_variant = None
        self.assertEqual(expected_variant, variants.get('sdk-local-evaluation-ci-test-holdout'))


if __name__ == '__main__':
    unittest.main()
