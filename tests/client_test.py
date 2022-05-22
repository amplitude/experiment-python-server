import unittest

from src.amplitude_experiment import Client, Variant, User, Config

API_KEY = 'client-DvWljIjiiuqLbyjqdvBaLFfEBrAvGuA3'
SERVER_URL = 'https://api.lab.amplitude.com/sdk/vardata'


class ClientTestCase(unittest.TestCase):

    def test_initialize_raise_error(self):
        self.assertRaises(ValueError, Client, "")

    def test_fetch(self):
        client = Client(API_KEY)
        expected_variant = Variant('on', 'payload')
        user = User(user_id='test_user')
        variants = client.fetch(user)
        variant_name = 'sdk-ci-test'
        self.assertIn(variant_name, variants)
        self.assertEqual(expected_variant, variants.get(variant_name))


if __name__ == '__main__':
    unittest.main()
