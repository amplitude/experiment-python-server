import threading
import time
import unittest
from typing import Optional, Callable
from unittest import mock
from unittest.mock import patch

from amplitude_experiment.cohort.cohort_loader import CohortLoader
from amplitude_experiment.flag import FlagConfigStreamApi
from amplitude_experiment.flag.flag_config_updater import FlagConfigUpdater, FlagConfigUpdaterFallbackRetryWrapper, \
    FlagConfigStreamer


class FlagConfigStreamerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.stream_api = mock.create_autospec(FlagConfigStreamApi)
        cohort_loader = mock.create_autospec(CohortLoader)
        flag_config_storage = mock.Mock()
        cohort_storage = mock.Mock()
        cohort_storage.get_cohort_ids.return_value = set()
        logger = mock.Mock()
        self.streamer = FlagConfigStreamer(self.stream_api, flag_config_storage, cohort_loader, cohort_storage, logger)

        self.err_count = 0

    def on_error(self, msg):
        self.err_count += 1

    def test_start_then_stopped(self):
        with patch.object(self.stream_api, "start") as start_func:
            with patch.object(self.stream_api, "stop") as stop_func:
                self.streamer.start(self.on_error)
                assert start_func.call_count == 1
                assert stop_func.call_count == 0
                assert self.err_count == 0
                self.streamer.stop()
                assert start_func.call_count == 1
                assert stop_func.call_count == 1
                assert self.err_count == 0

    def test_start_then_error_stopped(self):
        with patch.object(self.stream_api, "start") as start_func:
            with patch.object(self.stream_api, "stop") as stop_func:
                self.streamer.start(self.on_error)
                assert start_func.call_count == 1
                assert stop_func.call_count == 0
                assert self.err_count == 0
                start_func.call_args[0][1]("error")
                assert start_func.call_count == 1
                assert stop_func.call_count == 1
                assert self.err_count == 1


class DummyUpdater(FlagConfigUpdater):
    def __init__(self, name):
        self.name = name
        self.fail_time = -1
        self.stopped_event = threading.Event()
        self.start_count = 0
        self.stop_count = 0

    def start(self, on_error: Optional[Callable[[str], None]]):
        self.start_count += 1
        print(self.name + " start")
        self.stopped_event.set()
        stopped_event = threading.Event()
        self.stopped_event = stopped_event

        if self.fail_time == 0:
            print(self.name + " start fail")
            raise Exception()
        if self.fail_time > 0:
            def fail():
                time.sleep(self.fail_time)
                if not stopped_event.is_set():
                    print(self.name + " failed")
                    if on_error:
                        on_error("failed")

            threading.Thread(target=fail).start()

    def stop(self):
        self.stop_count += 1
        print(self.name + " stopped")
        self.stopped_event.set()


class FlagConfigUpdaterFallbackRetryWrapperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy1 = DummyUpdater("dummy1")
        self.dummy2 = DummyUpdater("dummy2")
        self.logger = mock.Mock()
        self.api = FlagConfigUpdaterFallbackRetryWrapper(self.dummy1, self.dummy2, 1000, 0, 500, 0, self.logger)

    def test_main_start_success(self):
        self.api.start(None)
        assert self.dummy1.start_count == 1
        assert self.dummy2.start_count == 0

    def test_main_start_failed_fallback_start_success_main_start_success_on_retry(self):
        self.dummy1.fail_time = 0
        self.api.start(None)
        assert self.dummy1.start_count == 1
        assert self.dummy2.start_count == 1
        self.dummy1.fail_time = -1
        time.sleep(1.1)
        assert self.dummy1.start_count == 2
        assert self.dummy2.start_count == 1
        # No more restarts
        time.sleep(2)
        assert self.dummy1.start_count == 2
        assert self.dummy2.start_count == 1

    def test_main_start_failed_fallback_start_failed(self):
        self.dummy1.fail_time = 0
        self.dummy2.fail_time = 0
        try:
            self.api.start(None)
            raise Exception()
        except:
            pass
        assert self.dummy1.start_count == 1
        assert self.dummy2.start_count == 1
        time.sleep(2)
        # No retry
        assert self.dummy1.start_count == 1
        assert self.dummy2.start_count == 1

    def test_main_start_success_later_failed_fallback_start_success_later_main_retry_success(self):
        self.dummy1.fail_time = 2
        self.api.start(None)
        assert self.dummy1.start_count == 1
        assert self.dummy2.start_count == 0
        time.sleep(2.1)
        # Now main failed
        assert self.dummy1.start_count == 1
        assert self.dummy2.start_count == 1
        self.dummy1.fail_time = -1
        time.sleep(1)
        # Now main failed
        assert self.dummy1.start_count == 2
        assert self.dummy2.start_count == 1
        time.sleep(2)
        # No more retry
        assert self.dummy1.start_count == 2
        assert self.dummy2.start_count == 1

    def test_main_start_success_later_failed_fallback_start_failed_later_fallback_retry_success_later_main_retry_success(self):
        self.dummy1.fail_time = 2
        self.dummy2.fail_time = 0
        self.api.start(None)
        assert self.dummy1.start_count == 1
        assert self.dummy2.start_count == 0
        time.sleep(2.1)
        # Now main failed
        assert self.dummy1.start_count == 1
        assert self.dummy2.start_count == 1
        self.dummy1.fail_time = 0
        time.sleep(0.5)
        # Fallback retried
        assert self.dummy1.start_count == 1
        assert self.dummy2.start_count == 2
        time.sleep(0.5)
        # Main and Fallback retried
        assert self.dummy1.start_count == 2
        assert self.dummy2.start_count == 3
        self.dummy1.fail_time = -1
        self.dummy2.fail_time = -1
        time.sleep(0.5)
        # Fallback retried success
        assert self.dummy1.start_count == 2
        assert self.dummy2.start_count == 4
        time.sleep(0.5)
        # Main retried success
        assert self.dummy1.start_count == 3
        assert self.dummy2.start_count == 4
        time.sleep(2)
        # No more retry
        assert self.dummy1.start_count == 3
        assert self.dummy2.start_count == 4

    def test_main_start_success_later_failed_fallback_start_failed_later_main_retry_success(self):
        self.dummy1.fail_time = 2
        self.dummy2.fail_time = 0
        self.api.start(None)
        assert self.dummy1.start_count == 1
        assert self.dummy2.start_count == 0
        time.sleep(2.1)
        # Now main failed
        assert self.dummy1.start_count == 1
        assert self.dummy2.start_count == 1
        self.dummy1.fail_time = 0
        time.sleep(0.5)
        # Fallback retried
        assert self.dummy1.start_count == 1
        assert self.dummy2.start_count == 2
        time.sleep(0.5)
        # Main and Fallback retried
        assert self.dummy1.start_count == 2
        assert self.dummy2.start_count == 3
        self.dummy1.fail_time = -1
        time.sleep(0.5)
        # Fallback retried still fail
        assert self.dummy1.start_count == 2
        assert self.dummy2.start_count == 4
        time.sleep(0.5)
        # Main retried success, fallback may or may not retry, but no more after main success
        assert self.dummy1.start_count == 3
        assert self.dummy2.start_count <= 5
        time.sleep(2)
        # No more retry
        assert self.dummy1.start_count == 3
        assert self.dummy2.start_count <= 5

    def test_main_start_success_later_failed_fallback_start_failed_later_stopped(self):
        self.dummy1.fail_time = 2
        self.dummy2.fail_time = 0
        self.api.start(None)
        assert self.dummy1.start_count == 1
        assert self.dummy2.start_count == 0
        self.dummy1.fail_time = 0
        time.sleep(2.1)
        # Now main failed
        assert self.dummy1.start_count == 1
        assert self.dummy2.start_count == 1
        self.api.stop()
