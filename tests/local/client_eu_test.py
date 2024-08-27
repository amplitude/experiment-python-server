import unittest
from src.amplitude_experiment import LocalEvaluationClient, LocalEvaluationConfig, User, Variant
from src.amplitude_experiment.cohort.cohort_sync_config import CohortSyncConfig
from src.amplitude_experiment.local.config import ServerZone
from dotenv import load_dotenv
import os

SERVER_API_KEY = 'server-Qlp7XiSu6JtP2S3JzA95PnP27duZgQCF'


class LocalEvaluationClientTestCase(unittest.TestCase):
    _local_evaluation_client: LocalEvaluationClient = None

    @classmethod
    def setUpClass(cls) -> None:
        load_dotenv()
        api_key = os.environ['EU_API_KEY']
        secret_key = os.environ['EU_SECRET_KEY']
        cohort_sync_config = CohortSyncConfig(api_key=api_key,
                                              secret_key=secret_key)
        cls._local_evaluation_client = (
            LocalEvaluationClient(SERVER_API_KEY, LocalEvaluationConfig(debug=False, server_zone=ServerZone.EU,
                                                                        cohort_sync_config=cohort_sync_config)))
        cls._local_evaluation_client.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._local_evaluation_client.stop()

    def test_evaluate_with_cohort_eu(self):
        targeted_user = User(user_id='1', device_id='0')
        targeted_variant = (self._local_evaluation_client.evaluate_v2(targeted_user)
                            .get('sdk-local-evaluation-user-cohort'))
        expected_on_variant = Variant(key='on', value='on')
        self.assertEqual(expected_on_variant, targeted_variant)
        non_targeted_user = User(user_id='not_targeted')
        non_targeted_variant = (self._local_evaluation_client.evaluate_v2(non_targeted_user)
                                .get('sdk-local-evaluation-user-cohort'))
        expected_off_variant = Variant(key='off')
        self.assertEqual(non_targeted_variant, expected_off_variant)


if __name__ == '__main__':
    unittest.main()
