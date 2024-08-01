import unittest
from unittest import mock
from unittest.mock import patch
import logging

from src.amplitude_experiment import LocalEvaluationConfig
from src.amplitude_experiment.cohort.cohort_loader import CohortLoader
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
        cohort_storage.get_cohort_ids.return_value = set()
        logger = mock.create_autospec(logging.Logger)
        cohort_loader = CohortLoader(cohort_download_api, cohort_storage)
        runner = DeploymentRunner(
            LocalEvaluationConfig(),
            flag_api,
            flag_config_storage,
            cohort_storage,
            logger,
            cohort_loader,
        )
        flag_api.get_flag_configs.side_effect = RuntimeError("test")
        with self.assertRaises(RuntimeError):
            runner.start()

    def test_start_does_not_throw_if_cohort_load_fails(self):
        flag_api = mock.create_autospec(FlagConfigApi)
        cohort_download_api = mock.Mock()
        flag_config_storage = mock.Mock()
        cohort_storage = mock.Mock()
        cohort_storage.get_cohort_ids.return_value = set()
        logger = mock.create_autospec(logging.Logger)
        cohort_loader = CohortLoader(cohort_download_api, cohort_storage)
        runner = DeploymentRunner(
            LocalEvaluationConfig(),
            flag_api, flag_config_storage,
            cohort_storage,
            logger,
            cohort_loader,
        )

        # Mock methods as needed
        with patch.object(runner, '_delete_unused_cohorts'):
            flag_api.get_flag_configs.return_value = [self.flag]
            cohort_download_api.get_cohort.side_effect = RuntimeError("test")

            # Simply call the method and let the test pass if no exception is raised
            try:
                runner.start()
            except Exception as e:
                self.fail(f"runner.start() raised an exception unexpectedly: {e}")


if __name__ == '__main__':
    unittest.main()
