import unittest
from unittest.mock import MagicMock

from amplitude import Amplitude

from src.amplitude_experiment import Variant
from src.amplitude_experiment import User
from src.amplitude_experiment.assignment import AssignmentFilter, Assignment, DAY_MILLIS, to_event, AssignmentService
from src.amplitude_experiment.util import hash_code

user = User(user_id='user', device_id='device')


class AssignmentServiceTestCase(unittest.TestCase):

    def test_to_event(self):
        basic = Variant(key='control', value='control', metadata={
            'segmentName': 'All Other Users',
            'flagType': 'experiment',
            'flagVersion': 10,
            'default': False
        })
        different_value = Variant(key='on', value='control', metadata={
            'segmentName': 'All Other Users',
            'flagType': 'experiment',
            'flagVersion': 10,
            'default': False
        })
        default = Variant(key='off', value=None, metadata={
            'segmentName': 'All Other Users',
            'flagType': 'experiment',
            'flagVersion': 10,
            'default': True
        })
        mutex = Variant(key='slot-1', value='slot-1', metadata={
            'segmentName': 'All Other Users',
            'flagType': 'mutual-exclusion-group',
            'flagVersion': 10,
            'default': False
        })
        holdout = Variant(key='holdout', value='holdout', metadata={
            'segmentName': 'All Other Users',
            'flagType': 'holdout-group',
            'flagVersion': 10,
            'default': False
        })
        partial_metadata = Variant(key='on', value='on', metadata={
            'segmentName': 'All Other Users',
            'flagType': 'release',
        })
        empty_metadata = Variant(key='on', value='on')
        empty_variant = Variant()
        results = {
            'basic': basic,
            'different_value': different_value,
            'default': default,
            'mutex': mutex,
            'holdout': holdout,
            'partial_metadata': partial_metadata,
            'empty_metadata': empty_metadata,
            'empty_variant': empty_variant,
        }
        assignment = Assignment(user, results)
        event = to_event(assignment)
        self.assertEqual(user.user_id, event.user_id)
        self.assertEqual(user.device_id, event.device_id)
        self.assertEqual('[Experiment] Assignment', event.event_type)
        # Validate event properties
        event_properties = event.event_properties
        self.assertEqual('control', event_properties['basic.variant'])
        self.assertEqual('v10 rule:All Other Users', event_properties['basic.details'])
        self.assertEqual('on', event_properties['different_value.variant'])
        self.assertEqual('v10 rule:All Other Users', event_properties['different_value.details'])
        self.assertEqual('off', event_properties['default.variant'])
        self.assertEqual('v10 rule:All Other Users', event_properties['default.details'])
        self.assertEqual('slot-1', event_properties['mutex.variant'])
        self.assertEqual('v10 rule:All Other Users', event_properties['mutex.details'])
        self.assertEqual('holdout', event_properties['holdout.variant'])
        self.assertEqual('v10 rule:All Other Users', event_properties['holdout.details'])
        self.assertEqual('on', event_properties['partial_metadata.variant'])
        self.assertEqual('on', event_properties['empty_metadata.variant'])
        # Validate user properties
        user_properties = event.user_properties
        set_properties = user_properties['$set']
        self.assertEqual('control', set_properties['[Experiment] basic'])
        self.assertEqual('on', set_properties['[Experiment] different_value'])
        self.assertEqual('holdout', set_properties['[Experiment] holdout'])
        self.assertEqual('on', set_properties['[Experiment] partial_metadata'])
        self.assertEqual('on', set_properties['[Experiment] empty_metadata'])
        unset_properties = user_properties['$unset']
        self.assertEqual('-', unset_properties['[Experiment] default'])

        # Validate insert id
        canonicalization = 'user device basic control default off different_value on empty_metadata on holdout ' \
                           'holdout mutex slot-1 partial_metadata on '
        expected = f'user device {hash_code(canonicalization)} {int(assignment.timestamp / DAY_MILLIS)}'
        self.assertEqual(expected, event.insert_id)

    def test_tracking_called(self):
        instance = Amplitude('')
        instance.track = MagicMock()
        service = AssignmentService(instance, AssignmentFilter(2))
        results = {'flag-key-1': Variant(key='on')}
        service.track(Assignment(user, results))
        self.assertTrue(instance.track.called)
