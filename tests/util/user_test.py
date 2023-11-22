import unittest

from src.amplitude_experiment import User
from src.amplitude_experiment.util.user import user_to_evaluation_context


def test_user_to_evaluation_context(self):
    user = User(
        device_id='device_id',
        user_id='user_id',
        country='country',
        city='city',
        language='language',
        platform='platform',
        version='version',
        user_properties={'k': 'v'},
        groups={'type': 'name'},
        group_properties={'type': {'name': {'gk': 'gv'}}},
    )
    context = user_to_evaluation_context(user)
    self.assertEqual({
        'user': {
            'device_id': 'device_id',
            'user_id': 'user_id',
            'country': 'country',
            'city': 'city',
            'language': 'language',
            'platform': 'platform',
            'version': 'version',
            'user_properties': {'k': 'v'},
        },
        'groups': {
            'type': {
                'group_name': 'name',
                'group_properties': {'gk': 'gv'}
            }
        }
    }, context)


def test_user_to_evaluation_context_only_user(self):
    user = User(
        device_id='device_id',
        user_id='user_id',
        country='country',
        city='city',
        language='language',
        platform='platform',
        version='version',
        user_properties={'k': 'v'},
    )
    context = user_to_evaluation_context(user)
    self.assertEqual({
        'user': {
            'device_id': 'device_id',
            'user_id': 'user_id',
            'country': 'country',
            'city': 'city',
            'language': 'language',
            'platform': 'platform',
            'version': 'version',
            'user_properties': {'k': 'v'},
        },
    }, context)


def test_user_to_evaluation_context_only_groups(self):
    user = User(
        groups={'type': 'name'},
        group_properties={'type': {'name': {'gk': 'gv'}}},
    )
    context = user_to_evaluation_context(user)
    self.assertEqual({
        'groups': {
            'type': {
                'group_name': 'name',
                'group_properties': {'gk': 'gv'}
            }
        }
    }, context)


def test_user_to_evaluation_context_only_groups_no_group_props(self):
    user = User(
        groups={'type': 'name'},
    )
    context = user_to_evaluation_context(user)
    self.assertEqual({
        'groups': {
            'type': {
                'group_name': 'name',
            }
        }
    }, context)


if __name__ == '__main__':
    unittest.main()