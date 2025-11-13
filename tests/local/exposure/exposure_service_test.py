import unittest
from unittest.mock import MagicMock

from amplitude import Amplitude

from src.amplitude_experiment import Variant
from src.amplitude_experiment import User
from src.amplitude_experiment.exposure import Exposure, ExposureFilter, DAY_MILLIS, to_exposure_events, ExposureService
from src.amplitude_experiment.util import hash_code

user = User(user_id='user', device_id='device', user_properties={'user_prop': True}, country='country')


class ExposureServiceTestCase(unittest.TestCase):

    def test_to_exposure_events(self):
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
        exposure = Exposure(user, results)
        events = to_exposure_events(exposure, DAY_MILLIS)
        # Should exclude default (default=True) only
        # basic, different_value, mutex, holdout, partial_metadata, empty_metadata, empty_variant = 7 events
        self.assertEqual(7, len(events))
        
        # Verify empty_variant is included
        empty_variant_events = [e for e in events if e.event_properties.get('[Experiment] Flag Key') == 'empty_variant']
        self.assertEqual(1, len(empty_variant_events), 'empty_variant should be included in events')
        empty_variant_event = empty_variant_events[0]
        # empty_variant has no key or value, so variant property should not be set
        self.assertNotIn('[Experiment] Variant', empty_variant_event.event_properties)
        self.assertNotIn('metadata', empty_variant_event.event_properties)
        # User properties should be empty for empty_variant
        self.assertEqual({}, empty_variant_event.user_properties['$set'])
        self.assertEqual({}, empty_variant_event.user_properties['$unset'])
        
        for event in events:
            self.assertEqual(user.user_id, event.user_id)
            self.assertEqual(user.device_id, event.device_id)
            self.assertEqual('[Experiment] Exposure', event.event_type)
            
            flag_key = event.event_properties['[Experiment] Flag Key']
            self.assertIn(flag_key, results)
            variant = results[flag_key]
            
            # Validate event properties
            # For empty_variant, there may be no variant property since it has no key or value
            if variant.key:
                self.assertEqual(variant.key, event.event_properties.get('[Experiment] Variant'))
            elif variant.value:
                self.assertEqual(variant.value, event.event_properties.get('[Experiment] Variant'))
            # If variant has no key or value (empty_variant), variant property may not be set
            if variant.metadata:
                self.assertEqual(variant.metadata, event.event_properties.get('metadata'))
            
            # Validate user properties
            user_properties = event.user_properties
            set_properties = user_properties['$set']
            unset_properties = user_properties['$unset']
            
            flag_type = variant.metadata.get('flagType') if variant.metadata else None
            if flag_type == 'mutual-exclusion-group':
                self.assertEqual({}, set_properties)
                self.assertEqual({}, unset_properties)
            else:
                if variant.metadata and variant.metadata.get('default'):
                    self.assertEqual({}, set_properties)
                    self.assertIn(f'[Experiment] {flag_key}', unset_properties)
                else:
                    # For empty_variant (no key or value), no user property should be set
                    if variant.key:
                        self.assertEqual(variant.key, set_properties.get(f'[Experiment] {flag_key}'))
                    elif variant.value:
                        self.assertEqual(variant.value, set_properties.get(f'[Experiment] {flag_key}'))
                    # If no key or value, set_properties should be empty for this flag
                    self.assertEqual({}, unset_properties)
            
            # Validate insert id
            canonicalization = exposure.canonicalize()
            expected = f'{user.user_id} {user.device_id} {hash_code(flag_key + " " + canonicalization)} {int(exposure.timestamp / DAY_MILLIS)}'
            self.assertEqual(expected, event.insert_id)

    def test_tracking_called(self):
        instance = Amplitude('')
        instance.track = MagicMock()
        service = ExposureService(instance, ExposureFilter(2))
        results = {'flag-key-1': Variant(key='on')}
        service.track(Exposure(user, results))
        self.assertTrue(instance.track.called)


if __name__ == '__main__':
    unittest.main()

