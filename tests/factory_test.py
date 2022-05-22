import unittest
from src.amplitude_experiment import Experiment

API_KEY = 'client-DvWljIjiiuqLbyjqdvBaLFfEBrAvGuA3'


class FactoryTestCase(unittest.TestCase):
    def test_singleton_instance(self):
        client1 = Experiment.initialize(API_KEY)
        client2 = Experiment.initialize(API_KEY)
        self.assertEqual(client1, client2)


if __name__ == '__main__':
    unittest.main()
