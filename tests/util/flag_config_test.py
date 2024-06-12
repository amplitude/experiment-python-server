import unittest

from src.amplitude_experiment.util.flag_config import (
    get_all_cohort_ids_from_flags,
    get_grouped_cohort_ids_from_flags,
    get_all_cohort_ids_from_flag,
    get_grouped_cohort_ids_from_flag,
)


class CohortUtilsTestCase(unittest.TestCase):

    def setUp(self):
        self.flags = [
            {
                'key': 'flag-1',
                'metadata': {
                    'deployed': True,
                    'evaluationMode': 'local',
                    'flagType': 'release',
                    'flagVersion': 1
                },
                'segments': [
                    {
                        'conditions': [
                            [
                                {
                                    'op': 'set contains any',
                                    'selector': ['context', 'user', 'cohort_ids'],
                                    'values': ['cohort1', 'cohort2']
                                }
                            ]
                        ],
                        'metadata': {'segmentName': 'Segment A'},
                        'variant': 'on'
                    },
                    {
                        'metadata': {'segmentName': 'All Other Users'},
                        'variant': 'off'
                    }
                ],
                'variants': {
                    'off': {
                        'key': 'off',
                        'metadata': {'default': True}
                    },
                    'on': {
                        'key': 'on',
                        'value': 'on'
                    }
                }
            },
            {
                'key': 'flag-2',
                'metadata': {
                    'deployed': True,
                    'evaluationMode': 'local',
                    'flagType': 'release',
                    'flagVersion': 2
                },
                'segments': [
                    {
                        'conditions': [
                            [
                                {
                                    'op': 'set contains any',
                                    'selector': ['context', 'user', 'cohort_ids'],
                                    'values': ['cohort3', 'cohort4', 'cohort5', 'cohort6']
                                }
                            ]
                        ],
                        'metadata': {'segmentName': 'Segment B'},
                        'variant': 'on'
                    },
                    {
                        'metadata': {'segmentName': 'All Other Users'},
                        'variant': 'off'
                    }
                ],
                'variants': {
                    'off': {
                        'key': 'off',
                        'metadata': {'default': True}
                    },
                    'on': {
                        'key': 'on',
                        'value': 'on'
                    }
                }
            },
            {
                'key': 'flag-3',
                'metadata': {
                    'deployed': True,
                    'evaluationMode': 'local',
                    'flagType': 'release',
                    'flagVersion': 3
                },
                'segments': [
                    {
                        'conditions': [
                            [
                                {
                                    'op': 'set contains any',
                                    'selector': ['context', 'groups', 'group_name', 'cohort_ids'],
                                    'values': ['cohort7', 'cohort8']
                                }
                            ]
                        ],
                        'metadata': {'segmentName': 'Segment C'},
                        'variant': 'on'
                    },
                    {
                        'metadata': {'segmentName': 'All Other Groups'},
                        'variant': 'off'
                    }
                ],
                'variants': {
                    'off': {
                        'key': 'off',
                        'metadata': {'default': True}
                    },
                    'on': {
                        'key': 'on',
                        'value': 'on'
                    }
                }
            }
        ]

    def test_get_all_cohort_ids(self):
        expected_cohort_ids = {'cohort1', 'cohort2', 'cohort3', 'cohort4', 'cohort5', 'cohort6', 'cohort7', 'cohort8'}
        for flag in self.flags:
            cohort_ids = get_all_cohort_ids_from_flag(flag)
            self.assertTrue(cohort_ids.issubset(expected_cohort_ids))

    def test_get_grouped_cohort_ids_for_flag(self):
        expected_grouped_cohort_ids = {
            'User': {'cohort1', 'cohort2', 'cohort3', 'cohort4', 'cohort5', 'cohort6'},
            'group_name': {'cohort7', 'cohort8'}
        }
        for flag in self.flags:
            grouped_cohort_ids = get_grouped_cohort_ids_from_flag(flag)
            for key, values in grouped_cohort_ids.items():
                self.assertTrue(key in expected_grouped_cohort_ids)
                self.assertTrue(values.issubset(expected_grouped_cohort_ids[key]))

    def test_get_all_cohort_ids_from_flags(self):
        expected_cohort_ids = {'cohort1', 'cohort2', 'cohort3', 'cohort4', 'cohort5', 'cohort6', 'cohort7', 'cohort8'}
        cohort_ids = get_all_cohort_ids_from_flags(self.flags)
        self.assertEqual(cohort_ids, expected_cohort_ids)

    def test_get_grouped_cohort_ids_for_flag_from_flags(self):
        expected_grouped_cohort_ids = {
            'User': {'cohort1', 'cohort2', 'cohort3', 'cohort4', 'cohort5', 'cohort6'},
            'group_name': {'cohort7', 'cohort8'}
        }
        grouped_cohort_ids = get_grouped_cohort_ids_from_flags(self.flags)
        self.assertEqual(grouped_cohort_ids, expected_grouped_cohort_ids)


if __name__ == '__main__':
    unittest.main()
