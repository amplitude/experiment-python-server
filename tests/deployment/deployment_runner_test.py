import unittest
from unittest import mock

from src.amplitude_experiment import LocalEvaluationConfig, LocalEvaluationClient, User
from src.amplitude_experiment.cohort.cohort_loader import CohortLoader
from src.amplitude_experiment.cohort.cohort_sync_config import CohortSyncConfig
from src.amplitude_experiment.flag.flag_config_api import FlagConfigApi
from src.amplitude_experiment.deployment.deployment_runner import DeploymentRunner

COHORT_ID = '1234'


class DeploymentRunnerTest(unittest.TestCase):

    def setUp(self):
        self.flag = {
            "key": "flag",
            "variants": {},
            "segments": [
                {
                    "conditions": [
                        [
                            {
                                "selector": ["context", "user", "cohort_ids"],
                                "op": "set contains any",
                                "values": [COHORT_ID],
                            }
                        ]
                    ],
                }
            ]
        }

    def test_start_throws_if_first_flag_config_load_fails(self):
        flag_api = mock.create_autospec(FlagConfigApi)
        cohort_download_api = mock.Mock()
        flag_config_storage = mock.Mock()
        cohort_storage = mock.Mock()
        cohort_loader = CohortLoader(cohort_download_api, cohort_storage)
        runner = DeploymentRunner(
            LocalEvaluationConfig(),
            flag_api,
            flag_config_storage,
            cohort_storage,
            cohort_loader
        )
        flag_api.get_flag_configs.side_effect = RuntimeError("test")
        with self.assertRaises(RuntimeError):
            runner.start()

    def test_start_throws_if_first_cohort_load_fails(self):
        flag_api = mock.create_autospec(FlagConfigApi)
        cohort_download_api = mock.Mock()
        flag_config_storage = mock.Mock()
        cohort_storage = mock.Mock()
        cohort_loader = CohortLoader(cohort_download_api, cohort_storage)
        runner = DeploymentRunner(
            LocalEvaluationConfig(),
            flag_api, flag_config_storage,
            cohort_storage,
            cohort_loader
        )
        flag_api.get_flag_configs.return_value = [self.flag]
        cohort_download_api.get_cohort_description.side_effect = RuntimeError("test")

        with self.assertRaises(RuntimeError):
            runner.start()


if __name__ == '__main__':
    unittest.main()
