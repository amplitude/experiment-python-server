import random
import time
import unittest
import platform

from src.amplitude_experiment import LocalEvaluationClient, User

API_KEY = 'server-qz35UwzJ5akieoAdIgzM4m9MIiOLXLoz'


def random_boolean():
    return bool(random.getrandbits(1))


def measure(function, *args, **kwargs):
    start = time.time()
    function(*args, **kwargs)
    elapsed = (time.time() - start) * 1000
    return elapsed


def random_string(length):
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(random.choice(letters) for i in range(length))


def random_experiment_user():
    n = 15
    user = User(user_id=random_string(n))
    if random_boolean():
        user.device_id = random_string(n)
    if random_boolean():
        user.platform = random_string(n)
    if random_boolean():
        user.version = random_string(n)
    if random_boolean():
        user.os = random_string(n)
    if random_boolean():
        user.device_manufacturer = random_string(n)
    if random_boolean():
        user.device_model = random_string(n)
    if random_boolean():
        user.device_brand = random_string(n)
    if random_boolean():
        user.user_properties = {
            'test': 'test'
        }
    return user


def random_benchmark_flag():
    n = random.randint(1, 4)
    return f"local-evaluation-benchmark-{n}"


@unittest.skipIf(platform.machine().startswith(('arm', 'aarch64')), "GHA aarch64 too slow")
class BenchmarkTestCase(unittest.TestCase):
    _local_evaluation_client: LocalEvaluationClient = None

    @classmethod
    def setUpClass(cls) -> None:
        cls._local_evaluation_client = LocalEvaluationClient(API_KEY)
        cls._local_evaluation_client.start()
        cls._local_evaluation_client.evaluate(random_experiment_user())

    @classmethod
    def tearDownClass(cls) -> None:
        cls._local_evaluation_client.stop()

    def test_evaluate_benchmark_1_flag_smaller_than_10_ms(self):
        user = random_experiment_user()
        flag = random_benchmark_flag()
        duration = measure(self._local_evaluation_client.evaluate, user, [flag])
        print('took:', duration)
        self.assertTrue(duration < 10)

    def test_evaluate_benchmark_10_flag_smaller_than_10_ms(self):
        total = 0
        for i in range(10):
            user = random_experiment_user()
            flag = random_benchmark_flag()
            duration = measure(self._local_evaluation_client.evaluate, user, [flag])
            total += duration
        print('took:', total)
        self.assertTrue(total < 20)

    def test_evaluate_benchmark_100_flag_smaller_than_100_ms(self):
        total = 0
        for i in range(100):
            user = random_experiment_user()
            flag = random_benchmark_flag()
            duration = measure(self._local_evaluation_client.evaluate, user, [flag])
            total += duration
        print('took:', total)
        self.assertTrue(total < 100)

    def test_evaluate_benchmark_1000_flag_smaller_than_1000_ms(self):
        total = 0
        for i in range(1000):
            user = random_experiment_user()
            flag = random_benchmark_flag()
            duration = measure(self._local_evaluation_client.evaluate, user, [flag])
            total += duration
        print('took:', total)
        self.assertTrue(total < 1000)


if __name__ == '__main__':
    unittest.main()
