import unittest
from src.amplitude_experiment import AmplitudeCookie


class AmplitudeCookieTestCase(unittest.TestCase):
    def test_valid_api_key_return_cookie_name(self):
        self.assertEqual(AmplitudeCookie.cookie_name('1234567'), 'amp_123456')

    def test_invalid_api_key_raise_error(self):
        self.assertRaises(ValueError, AmplitudeCookie.cookie_name, '')

    def test_parse_cookie_with_device_id_only(self):
        user = AmplitudeCookie.parse('deviceId...1f1gkeib1.1f1gkeib1.dv.1ir.20q')
        self.assertIsNotNone(user)
        self.assertEqual(user.device_id, 'deviceId')
        self.assertIsNone(user.user_id)

    def test_parse_cookie_with_device_id_and_user_id(self):
        user = AmplitudeCookie.parse('deviceId.dGVzdEBhbXBsaXR1ZGUuY29t..1f1gkeib1.1f1gkeib1.dv.1ir.20q')
        self.assertIsNotNone(user)
        self.assertEqual(user.device_id, 'deviceId')
        self.assertEqual(user.user_id, 'test@amplitude.com')

    def test_parse_cookie_with_device_id_and_utf_user_id(self):
        user = AmplitudeCookie.parse('deviceId.Y8O3Pg==..1f1gkeib1.1f1gkeib1.dv.1ir.20q')
        self.assertIsNotNone(user)
        self.assertEqual(user.device_id, 'deviceId')
        self.assertEqual(user.user_id, 'c÷>')

    def test_generate(self):
        self.assertEqual(AmplitudeCookie.generate('deviceId'), 'deviceId..........')

    def test_new_format_valid_api_key_return_cookie_name(self):
        self.assertEqual(AmplitudeCookie.cookie_name('1234567'), 'amp_123456')

    def test_new_format_invalid_api_key_raise_error(self):
        self.assertRaises(ValueError, AmplitudeCookie.cookie_name, '')

    def test_new_format_parse_cookie_with_device_id_only(self):
        user = AmplitudeCookie.parse('JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjJzb21lRGV2aWNlSWQlMjIlN0Q=', new_format=True)
        self.assertIsNotNone(user)
        self.assertEqual(user.device_id, 'someDeviceId')
        self.assertIsNone(user.user_id)

    def test_new_format_parse_cookie_with_device_id_and_user_id(self):
        user = AmplitudeCookie.parse('JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjJzb21lRGV2aWNlSWQlMjIlMkMlMjJ1c2VySWQlMjIlM0ElMjJleGFtcGxlJTQwYW1wbGl0dWRlLmNvbSUyMiU3RA==', new_format=True)
        self.assertIsNotNone(user)
        self.assertEqual(user.device_id, 'someDeviceId')
        self.assertEqual(user.user_id, 'example@amplitude.com')

    def test_new_format_parse_cookie_with_device_id_and_utf_user_id(self):
        user = AmplitudeCookie.parse('JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjJzb21lRGV2aWNlSWQlMjIlMkMlMjJ1c2VySWQlMjIlM0ElMjJjJUMzJUI3JTNFJTIyJTdE', new_format=True)
        self.assertIsNotNone(user)
        self.assertEqual(user.device_id, 'someDeviceId')
        self.assertEqual(user.user_id, 'c÷>')

    def test_new_format_generate(self):
        self.assertEqual(AmplitudeCookie.generate('someDeviceId', new_format=True), 'JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjAlMjJzb21lRGV2aWNlSWQlMjIlN0Q=')


if __name__ == '__main__':
    unittest.main()
