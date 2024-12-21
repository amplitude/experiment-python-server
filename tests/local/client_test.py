import re
import unittest
from unittest import mock

from src.amplitude_experiment import LocalEvaluationClient, LocalEvaluationConfig, User, Variant
from src.amplitude_experiment.cohort.cohort_sync_config import CohortSyncConfig
from dotenv import load_dotenv
import os


SERVER_API_KEY = 'server-qz35UwzJ5akieoAdIgzM4m9MIiOLXLoz'
test_user = User(user_id='test_user')
test_user_2 = User(user_id='user_id', device_id='device_id')


class LocalEvaluationClientTestCase(unittest.TestCase):
    _local_evaluation_client: LocalEvaluationClient = None
    _stream_update: bool = False

    @classmethod
    def setUpClass(cls) -> None:
        load_dotenv()
        api_key = os.environ['API_KEY']
        secret_key = os.environ['SECRET_KEY']
        cohort_sync_config = CohortSyncConfig(api_key=api_key,
                                              secret_key=secret_key)
        cls._local_evaluation_client = (
            LocalEvaluationClient(SERVER_API_KEY, LocalEvaluationConfig(debug=False,
                                                                        cohort_sync_config=cohort_sync_config,
                                                                        stream_updates=cls._stream_update)))
        cls._local_evaluation_client.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._local_evaluation_client.stop()

    def test_initialize_raise_error(self):
        self.assertRaises(ValueError, LocalEvaluationClient, "")

    def test_evaluate_all_flags_success(self):
        variants = self._local_evaluation_client.evaluate(test_user)
        expected_variant = Variant(key='on', value='on', payload='payload')
        self.assertEqual(expected_variant, variants.get('sdk-local-evaluation-ci-test'))

    def test_evaluate_one_flag_success(self):
        variants = self._local_evaluation_client.evaluate(test_user, ['sdk-local-evaluation-ci-test'])
        expected_variant = Variant(key='on', value='on', payload='payload')
        self.assertEqual(expected_variant, variants.get('sdk-local-evaluation-ci-test'))

    def test_invalid_api_key_throw_exception(self):
        invalid_local_api_key = 'client-DvWljIjiiuqLbyjqdvBaLFfEBrAvGuA3'
        with LocalEvaluationClient(invalid_local_api_key) as test_client:
            self.assertRaises(Exception, test_client.start, "[Experiment] Get flagConfigs - received error response")

    def test_evaluate_with_dependencies_success(self):
        variants = self._local_evaluation_client.evaluate(test_user_2)
        expected_variant = Variant(key='control', value='control')
        self.assertEqual(expected_variant, variants.get('sdk-ci-local-dependencies-test'))

    def test_evaluate_with_dependencies_and_flag_keys_success(self):
        variants = self._local_evaluation_client.evaluate(test_user_2, ['sdk-ci-local-dependencies-test'])
        expected_variant = Variant(key='control', value='control')
        self.assertEqual(expected_variant, variants.get('sdk-ci-local-dependencies-test'))

    def test_evaluate_with_dependencies_and_flag_keys_not_exist_no_variant(self):
        variants = self._local_evaluation_client.evaluate(test_user_2, ['does-not-exist'])
        expected_variant = None
        self.assertEqual(expected_variant, variants.get('sdk-ci-local-dependencies-test'))

    def test_evaluate_with_dependencies_variant_holdout(self):
        variants = self._local_evaluation_client.evaluate(test_user_2)
        expected_variant = None
        self.assertEqual(expected_variant, variants.get('sdk-local-evaluation-ci-test-holdout'))

    def test_evaluate_with_cohort(self):
        targeted_user = User(user_id='12345', device_id='device_id')
        targeted_variant = (self._local_evaluation_client.evaluate_v2(targeted_user,
                                                                      {'sdk-local-evaluation-user-cohort-ci-test'})
                            .get('sdk-local-evaluation-user-cohort-ci-test'))
        expected_on_variant = Variant(key='on', value='on')
        self.assertEqual(expected_on_variant, targeted_variant)
        non_targeted_user = User(user_id='not_targeted')
        non_targeted_variant = (self._local_evaluation_client.evaluate_v2(non_targeted_user)
                                .get('sdk-local-evaluation-user-cohort-ci-test'))
        expected_off_variant = Variant(key='off')
        self.assertEqual(expected_off_variant, non_targeted_variant)

    def test_evaluate_with_group_cohort(self):
        targeted_user = User(user_id='12345', device_id='device_id', groups={'org id': ['1']})
        targeted_variant = (self._local_evaluation_client.evaluate_v2(targeted_user,
                                                                      {'sdk-local-evaluation-group-cohort-ci-test'})
                            .get('sdk-local-evaluation-group-cohort-ci-test'))
        expected_on_variant = Variant(key='on', value='on')
        self.assertEqual(expected_on_variant, targeted_variant)
        non_targeted_user = User(user_id='12345', device_id='device_id', groups={'org id': ['not_targeted']})
        non_targeted_variant = (self._local_evaluation_client.evaluate_v2(non_targeted_user)
                                .get('sdk-local-evaluation-group-cohort-ci-test'))
        expected_off_variant = Variant(key='off')
        self.assertEqual(expected_off_variant, non_targeted_variant)

    def test_evaluation_cohorts_not_in_storage_with_sync_config(self):
        with mock.patch.object(self._local_evaluation_client.cohort_storage, 'put_cohort', return_value=None):
            self._local_evaluation_client.cohort_storage.get_cohort_ids = mock.Mock(return_value=set())
            targeted_user = User(user_id='12345')

            with self.assertLogs(self._local_evaluation_client.logger, level='WARNING') as log:
                self._local_evaluation_client.evaluate_v2(targeted_user, {'sdk-local-evaluation-user-cohort-ci-test'})
                log_message = (
                    "WARNING:Amplitude:Evaluating flag sdk-local-evaluation-user-cohort-ci-test dependent on cohorts "
                    "{.*} without {.*} in storage"
                )
                self.assertTrue(any(re.match(log_message, message) for message in log.output))


class LocalEvaluationClientStreamingTestCase(LocalEvaluationClientTestCase):
    _stream_update: bool = True


if __name__ == '__main__':
    unittest.main()
