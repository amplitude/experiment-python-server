import unittest
from unittest.mock import MagicMock

from amplitude import Amplitude

from src.amplitude_experiment import User, FlagResult
from src.amplitude_experiment.assignment import AssignmentFilter, Assignment, DAY_MILLIS, to_event, AssignmentService

user = User(user_id='user', device_id='device')


class AssignmentServiceTestCase(unittest.TestCase):

    def test_to_event(self):
        results = {}
        result1 = FlagResult({'variant': {'key': 'on'}, 'isDefaultVariant': False})
        result2 = FlagResult({'variant': {'key': 'control'}, 'isDefaultVariant': True})
        results['flag-key-1'] = result1
        results['flag-key-2'] = result2
        assignment = Assignment(user, results)
        event = to_event(assignment)
        self.assertEqual(user.user_id, event.user_id)
        self.assertEqual(user.device_id, event.device_id)
        self.assertEqual('[Experiment] Assignment', event.event_type)
        event_properties = event.event_properties
        self.assertEqual(2, len(event_properties))
        self.assertEqual('on', event_properties['flag-key-1.variant'])
        self.assertEqual('control', event_properties['flag-key-2.variant'])
        user_properties = event.user_properties
        self.assertEqual(2, len(user_properties))
        self.assertEqual(1, len(user_properties['$set']))
        self.assertEqual(1, len(user_properties['$unset']))
        canonicalization = 'user device flag-key-1 on flag-key-2 control '
        expected = f'user device {hash(canonicalization)} {int(assignment.timestamp / DAY_MILLIS)}'
        self.assertEqual(expected, event.insert_id)

    def test_tracking_called(self):
        instance = Amplitude('')
        instance.track = MagicMock()
        service = AssignmentService(instance, AssignmentFilter(2))
        service.track(Assignment(user, {}))
        self.assertTrue(instance.track.called)
