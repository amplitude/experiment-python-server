import unittest
from src.amplitude_experiment import Experiment

API_KEY = 'client-DvWljIjiiuqLbyjqdvBaLFfEBrAvGuA3'


class FactoryTestCase(unittest.TestCase):
    def test_singleton_remote_instance(self):
        client1 = Experiment.initialize_remote(API_KEY)
        client2 = Experiment.initialize_remote(API_KEY)
        self.assertEqual(client1, client2)
        client1.close()

    def test_singleton_local_instance(self):
        client1 = Experiment.initialize_local(API_KEY)
        client2 = Experiment.initialize_local(API_KEY)
        self.assertEqual(client1, client2)
        client1.stop()


if __name__ == '__main__':
    unittest.main()
