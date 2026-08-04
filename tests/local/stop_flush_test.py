import time
import unittest
from concurrent.futures import Future
from unittest.mock import MagicMock

from src.amplitude_experiment import LocalEvaluationClient, LocalEvaluationConfig
from src.amplitude_experiment.assignment import AssignmentConfig
from src.amplitude_experiment.exposure.exposure_config import ExposureConfig

API_KEY = 'server-api-key'


def completed_future() -> Future:
    future = Future()
    future.set_result(None)
    return future


class LocalEvaluationClientStopTestCase(unittest.TestCase):

    def _client_with_event_services(self) -> LocalEvaluationClient:
        config = LocalEvaluationConfig(
            assignment_config=AssignmentConfig(api_key='analytics-api-key'),
            exposure_config=ExposureConfig(api_key='analytics-api-key'),
        )
        return LocalEvaluationClient(API_KEY, config)

    def test_stop_flushes_then_shuts_down_assignment_and_exposure(self):
        client = self._client_with_event_services()
        assignment_amplitude = MagicMock()
        assignment_amplitude.flush.return_value = [completed_future()]
        exposure_amplitude = MagicMock()
        exposure_amplitude.flush.return_value = [None]
        client.assignment_service.amplitude = assignment_amplitude
        client.exposure_service.amplitude = exposure_amplitude

        client.stop()

        assignment_amplitude.flush.assert_called_once()
        exposure_amplitude.flush.assert_called_once()
        assignment_amplitude.shutdown.assert_called_once()
        exposure_amplitude.shutdown.assert_called_once()

    def test_stop_timeout_bounds_wait_on_pending_events(self):
        client = self._client_with_event_services()
        never_completes = Future()
        assignment_amplitude = MagicMock()
        assignment_amplitude.flush.return_value = [never_completes]
        client.assignment_service.amplitude = assignment_amplitude
        client.exposure_service.amplitude = MagicMock(flush=MagicMock(return_value=[]))

        start = time.monotonic()
        client.stop(timeout=0.2)
        elapsed = time.monotonic() - start

        self.assertLess(elapsed, 2)
        assignment_amplitude.shutdown.assert_called_once()

    def test_stop_without_event_services(self):
        client = LocalEvaluationClient(API_KEY, LocalEvaluationConfig())
        client.stop()

    def test_context_manager_exit_flushes(self):
        client = self._client_with_event_services()
        exposure_amplitude = MagicMock()
        exposure_amplitude.flush.return_value = [completed_future()]
        client.assignment_service.amplitude = MagicMock(flush=MagicMock(return_value=[]))
        client.exposure_service.amplitude = exposure_amplitude

        with client:
            pass

        exposure_amplitude.flush.assert_called_once()
        exposure_amplitude.shutdown.assert_called_once()


if __name__ == '__main__':
    unittest.main()
