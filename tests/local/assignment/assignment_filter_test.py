import time
import unittest

from src.amplitude_experiment import Variant
from src.amplitude_experiment import User
from src.amplitude_experiment.assignment import Assignment, AssignmentFilter


class AssignmentFilterTestCase(unittest.TestCase):

    def test_single_assignment(self):
        assignment_filter = AssignmentFilter(100)
        user = User(user_id='user', device_id='device')
        results = {
            'flag-key-1': Variant(key='on', value='on'),
            'flag-key-2': Variant(key='control', value='control'),
        }
        assignment = Assignment(user, results)
        self.assertTrue(assignment_filter.should_track(assignment))

    def test_duplicate_assignments(self):
        assignment_filter = AssignmentFilter(100)
        user = User(user_id='user', device_id='device')
        results = {
            'flag-key-1': Variant(key='on', value='on'),
            'flag-key-2': Variant(key='control', value='control'),
        }
        assignment1 = Assignment(user, results)
        assignment2 = Assignment(user, results)
        self.assertTrue(assignment_filter.should_track(assignment1))
        self.assertFalse(assignment_filter.should_track(assignment2))

    def test_same_user_different_results(self):
        assignment_filter = AssignmentFilter(100)
        user = User(user_id='user', device_id='device')
        results1 = {
            'flag-key-1': Variant(key='on', value='on'),
            'flag-key-2': Variant(key='control', value='control'),
        }
        results2 = {
            'flag-key-1': Variant(key='control', value='control'),
            'flag-key-2': Variant(key='on', value='on'),
        }
        assignment1 = Assignment(user, results1)
        assignment2 = Assignment(user, results2)
        self.assertTrue(assignment_filter.should_track(assignment1))
        self.assertTrue(assignment_filter.should_track(assignment2))

    def test_same_results_different_users(self):
        assignment_filter = AssignmentFilter(100)
        user1 = User(user_id='user', device_id='device')
        user2 = User(user_id='different user', device_id='device')
        results = {
            'flag-key-1': Variant(key='on', value='on'),
            'flag-key-2': Variant(key='control', value='control'),
        }
        assignment1 = Assignment(user1, results)
        assignment2 = Assignment(user2, results)
        self.assertTrue(assignment_filter.should_track(assignment1))
        self.assertTrue(assignment_filter.should_track(assignment2))

    def test_empty_results(self):
        assignment_filter = AssignmentFilter(100)
        user1 = User(user_id='user', device_id='device')
        user2 = User(user_id='different user', device_id='device')
        assignment1 = Assignment(user1, {})
        assignment2 = Assignment(user1, {})
        assignment3 = Assignment(user2, {})
        self.assertFalse(assignment_filter.should_track(assignment1))
        self.assertFalse(assignment_filter.should_track(assignment2))
        self.assertFalse(assignment_filter.should_track(assignment3))

    def test_duplicate_assignments_with_different_ordering(self):
        assignment_filter = AssignmentFilter(100)
        user = User(user_id='user', device_id='device')
        results1 = {
            'flag-key-1': Variant(key='on', value='on'),
            'flag-key-2': Variant(key='control', value='control'),
        }
        results2 = {
            'flag-key-2': Variant(key='control', value='control'),
            'flag-key-1': Variant(key='on', value='on'),
        }
        assignment1 = Assignment(user, results1)
        assignment2 = Assignment(user, results2)
        self.assertTrue(assignment_filter.should_track(assignment1))
        self.assertFalse(assignment_filter.should_track(assignment2))

    def test_lru_replacement(self):
        assignment_filter = AssignmentFilter(2)
        user1 = User(user_id='user1', device_id='device')
        user2 = User(user_id='user2', device_id='device')
        user3 = User(user_id='user3', device_id='device')
        results = {
            'flag-key-1': Variant(key='on', value='on'),
            'flag-key-2': Variant(key='control', value='control'),
        }
        assignment1 = Assignment(user1, results)
        assignment2 = Assignment(user2, results)
        assignment3 = Assignment(user3, results)
        self.assertTrue(assignment_filter.should_track(assignment1))
        self.assertTrue(assignment_filter.should_track(assignment2))
        self.assertTrue(assignment_filter.should_track(assignment3))
        self.assertTrue(assignment_filter.should_track(assignment1))

    def test_lru_expiration(self):
        assignment_filter = AssignmentFilter(100, 1000)
        user1 = User(user_id='user1', device_id='device')
        user2 = User(user_id='user2', device_id='device')
        results = {
            'flag-key-1': Variant(key='on', value='on'),
            'flag-key-2': Variant(key='control', value='control'),
        }
        assignment1 = Assignment(user1, results)
        assignment2 = Assignment(user2, results)
        # assignment1 should be evicted
        self.assertTrue(assignment_filter.should_track(assignment1))
        self.assertFalse(assignment_filter.should_track(assignment1))
        time.sleep(1.1)
        self.assertTrue(assignment_filter.should_track(assignment1))
        # assignment2 should not be evicted
        self.assertTrue(assignment_filter.should_track(assignment2))
        self.assertFalse(assignment_filter.should_track(assignment2))
        time.sleep(0.95)
        self.assertFalse(assignment_filter.should_track(assignment2))
