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


if __name__ == '__main__':
    unittest.main()
