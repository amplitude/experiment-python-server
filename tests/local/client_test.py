import re
import unittest
from unittest import mock

from src.amplitude_experiment import LocalEvaluationClient, LocalEvaluationConfig, User, Variant
from src.amplitude_experiment.cohort.cohort_sync_config import CohortSyncConfig
from src.amplitude_experiment.local.evaluate_options import EvaluateOptions
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

    def test_evaluate_v2_with_tracks_exposure_tracks_non_default_variants(self):
        # Mock the amplitude client's track method
        with mock.patch.object(self._local_evaluation_client.exposure_service.amplitude, 'track') as mock_track:
            # Perform evaluation with tracks_exposure=True
            options = EvaluateOptions(tracks_exposure=True)
            variants = self._local_evaluation_client.evaluate_v2(test_user, None, options)
            
            # Verify that track was called
            self.assertTrue(mock_track.called, 'Amplitude track should be called when tracks_exposure is True')
            
            # Count non-default variants
            non_default_variants = {
                flag_key: variant for flag_key, variant in variants.items()
                if not (variant.metadata and variant.metadata.get('default'))
            }
            
            # Get all tracked events
            tracked_events = [call[0][0] for call in mock_track.call_args_list]
            
            # Verify that we have one event per non-default variant
            self.assertEqual(len(tracked_events), len(non_default_variants),
                           f'Expected {len(non_default_variants)} exposure events, got {len(tracked_events)}')
            
            # Verify each event has the correct structure
            tracked_flag_keys = set()
            for event in tracked_events:
                self.assertEqual(event.event_type, '[Experiment] Exposure')
                self.assertEqual(event.user_id, test_user.user_id)
                flag_key = event.event_properties.get('[Experiment] Flag Key')
                self.assertIsNotNone(flag_key, 'Event should have flag key')
                tracked_flag_keys.add(flag_key)
                # Verify the variant is not default
                variant = variants.get(flag_key)
                self.assertIsNotNone(variant, f'Variant for {flag_key} should exist')
                self.assertFalse(variant.metadata and variant.metadata.get('default'),
                               f'Variant for {flag_key} should not be default')
            
            # Verify all non-default variants were tracked
            self.assertEqual(tracked_flag_keys, set(non_default_variants.keys()),
                           'All non-default variants should be tracked')


class LocalEvaluationClientStreamingTestCase(LocalEvaluationClientTestCase):
    _stream_update: bool = True


if __name__ == '__main__':
    unittest.main()
