import unittest
from src.amplitude_experiment import AmplitudeCookie


class AmplitudeCookieTestCase(unittest.TestCase):
    def test_valid_api_key_return_cookie_name(self):
        self.assertEqual(AmplitudeCookie.cookie_name('1234567'), 'amp_123456')
        self.assertEqual(AmplitudeCookie.cookie_name('123456789011', new_format=True), 'AMP_1234567890')

    def test_invalid_api_key_raise_error(self):
        self.assertRaises(ValueError, AmplitudeCookie.cookie_name, '')

    def test_parse_cookie_with_device_id_only(self):
        user1 = AmplitudeCookie.parse('deviceId...1f1gkeib1.1f1gkeib1.dv.1ir.20q')
        self.assertIsNotNone(user1)
        self.assertEqual(user1.device_id, 'deviceId')
        self.assertIsNone(user1.user_id)

        user2 = AmplitudeCookie.parse('JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjJkZXZpY2VJZCUyMiU3RA==', new_format=True)
        self.assertIsNotNone(user2)
        self.assertEqual(user2.device_id, 'deviceId')
        self.assertIsNone(user2.user_id)

    def test_parse_cookie_with_device_id_and_user_id(self):
        user1 = AmplitudeCookie.parse('deviceId.dGVzdEBhbXBsaXR1ZGUuY29t..1f1gkeib1.1f1gkeib1.dv.1ir.20q')
        self.assertIsNotNone(user1)
        self.assertEqual(user1.device_id, 'deviceId')
        self.assertEqual(user1.user_id, 'test@amplitude.com')

        user2 = AmplitudeCookie.parse('JTdCJTIydXNlcklkJTIyJTNBJTIydGVzdCU0MGFtcGxpdHVkZS5jb20lMjIlMkMlMjJkZXZpY2VJZCUyMiUzQSUyMmRldmljZUlkJTIyJTdE', new_format=True)  # noqa
        self.assertIsNotNone(user1)
        self.assertEqual(user2.device_id, 'deviceId')
        self.assertEqual(user2.user_id, 'test@amplitude.com')

    def test_parse_cookie_with_device_id_and_utf_user_id(self):
        user = AmplitudeCookie.parse('deviceId.Y8O3Pg==..1f1gkeib1.1f1gkeib1.dv.1ir.20q')
        self.assertIsNotNone(user)
        self.assertEqual(user.device_id, 'deviceId')
        self.assertEqual(user.user_id, 'c÷>')

    def test_generate(self):
        self.assertEqual(AmplitudeCookie.generate('deviceId'), 'deviceId..........')
        self.assertEqual(
            AmplitudeCookie.generate('deviceId', new_format=True),
            'JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjJkZXZpY2VJZCUyMiU3RA=='
        )


if __name__ == '__main__':
    unittest.main()
