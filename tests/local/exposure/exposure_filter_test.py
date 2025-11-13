import time
import unittest

from src.amplitude_experiment import Variant
from src.amplitude_experiment import User
from src.amplitude_experiment.exposure import Exposure, ExposureFilter


class ExposureFilterTestCase(unittest.TestCase):

    def test_single_exposure(self):
        exposure_filter = ExposureFilter(100)
        user = User(user_id='user', device_id='device')
        results = {
            'flag-key-1': Variant(key='on', value='on'),
            'flag-key-2': Variant(key='control', value='control'),
        }
        exposure = Exposure(user, results)
        self.assertTrue(exposure_filter.should_track(exposure))

    def test_duplicate_exposures(self):
        exposure_filter = ExposureFilter(100)
        user = User(user_id='user', device_id='device')
        results = {
            'flag-key-1': Variant(key='on', value='on'),
            'flag-key-2': Variant(key='control', value='control'),
        }
        exposure1 = Exposure(user, results)
        exposure2 = Exposure(user, results)
        self.assertTrue(exposure_filter.should_track(exposure1))
        self.assertFalse(exposure_filter.should_track(exposure2))

    def test_same_user_different_results(self):
        exposure_filter = ExposureFilter(100)
        user = User(user_id='user', device_id='device')
        results1 = {
            'flag-key-1': Variant(key='on', value='on'),
            'flag-key-2': Variant(key='control', value='control'),
        }
        results2 = {
            'flag-key-1': Variant(key='control', value='control'),
            'flag-key-2': Variant(key='on', value='on'),
        }
        exposure1 = Exposure(user, results1)
        exposure2 = Exposure(user, results2)
        self.assertTrue(exposure_filter.should_track(exposure1))
        self.assertTrue(exposure_filter.should_track(exposure2))

    def test_same_results_different_users(self):
        exposure_filter = ExposureFilter(100)
        user1 = User(user_id='user', device_id='device')
        user2 = User(user_id='different user', device_id='device')
        results = {
            'flag-key-1': Variant(key='on', value='on'),
            'flag-key-2': Variant(key='control', value='control'),
        }
        exposure1 = Exposure(user1, results)
        exposure2 = Exposure(user2, results)
        self.assertTrue(exposure_filter.should_track(exposure1))
        self.assertTrue(exposure_filter.should_track(exposure2))

    def test_empty_results(self):
        exposure_filter = ExposureFilter(100)
        user1 = User(user_id='user', device_id='device')
        user2 = User(user_id='different user', device_id='device')
        exposure1 = Exposure(user1, {})
        exposure2 = Exposure(user1, {})
        exposure3 = Exposure(user2, {})
        self.assertFalse(exposure_filter.should_track(exposure1))
        self.assertFalse(exposure_filter.should_track(exposure2))
        self.assertFalse(exposure_filter.should_track(exposure3))

    def test_duplicate_exposures_with_different_ordering(self):
        exposure_filter = ExposureFilter(100)
        user = User(user_id='user', device_id='device')
        results1 = {
            'flag-key-1': Variant(key='on', value='on'),
            'flag-key-2': Variant(key='control', value='control'),
        }
        results2 = {
            'flag-key-2': Variant(key='control', value='control'),
            'flag-key-1': Variant(key='on', value='on'),
        }
        exposure1 = Exposure(user, results1)
        exposure2 = Exposure(user, results2)
        self.assertTrue(exposure_filter.should_track(exposure1))
        self.assertFalse(exposure_filter.should_track(exposure2))

    def test_lru_replacement(self):
        exposure_filter = ExposureFilter(2)
        user1 = User(user_id='user1', device_id='device')
        user2 = User(user_id='user2', device_id='device')
        user3 = User(user_id='user3', device_id='device')
        results = {
            'flag-key-1': Variant(key='on', value='on'),
            'flag-key-2': Variant(key='control', value='control'),
        }
        exposure1 = Exposure(user1, results)
        exposure2 = Exposure(user2, results)
        exposure3 = Exposure(user3, results)
        self.assertTrue(exposure_filter.should_track(exposure1))
        self.assertTrue(exposure_filter.should_track(exposure2))
        self.assertTrue(exposure_filter.should_track(exposure3))
        self.assertTrue(exposure_filter.should_track(exposure1))

    def test_lru_expiration(self):
        exposure_filter = ExposureFilter(100, 1000)
        user1 = User(user_id='user1', device_id='device')
        user2 = User(user_id='user2', device_id='device')
        results = {
            'flag-key-1': Variant(key='on', value='on'),
            'flag-key-2': Variant(key='control', value='control'),
        }
        exposure1 = Exposure(user1, results)
        exposure2 = Exposure(user2, results)
        # exposure1 should be evicted
        self.assertTrue(exposure_filter.should_track(exposure1))
        self.assertFalse(exposure_filter.should_track(exposure1))
        time.sleep(1.1)
        self.assertTrue(exposure_filter.should_track(exposure1))
        # exposure2 should not be evicted
        self.assertTrue(exposure_filter.should_track(exposure2))
        self.assertFalse(exposure_filter.should_track(exposure2))
        time.sleep(0.95)
        self.assertFalse(exposure_filter.should_track(exposure2))


if __name__ == '__main__':
    unittest.main()

