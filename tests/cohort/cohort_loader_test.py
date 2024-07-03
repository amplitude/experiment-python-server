import logging
import unittest
from unittest import mock
from unittest.mock import MagicMock

from src.amplitude_experiment.cohort.cohort import Cohort
from src.amplitude_experiment.cohort.cohort_loader import CohortLoader
from src.amplitude_experiment.cohort.cohort_storage import InMemoryCohortStorage

class CohortLoaderTest(unittest.TestCase):
    def setUp(self):
        self.api = MagicMock()
        self.storage = InMemoryCohortStorage()
        self.loader = CohortLoader(self.api, self.storage, mock.create_autospec(logging.Logger))

    def test_load_success(self):
        self.api.get_cohort.side_effect = [
            Cohort(id="a", last_modified=0, size=1, member_ids={"1"}),
            Cohort(id="b", last_modified=0, size=2, member_ids={"1", "2"})
        ]

        future_a = self.loader.load_cohort("a")
        future_b = self.loader.load_cohort("b")

        future_a.result()
        future_b.result()

        storage_description_a = self.storage.get_cohort("a")
        storage_description_b = self.storage.get_cohort("b")
        self.assertEqual(Cohort(id="a", last_modified=0, size=1, member_ids={"1"}), storage_description_a)
        self.assertEqual(Cohort(id="b", last_modified=0, size=2, member_ids={"1", "2"}), storage_description_b)

        storage_user1_cohorts = self.storage.get_cohorts_for_user("1", {"a", "b"})
        storage_user2_cohorts = self.storage.get_cohorts_for_user("2", {"a", "b"})
        self.assertEqual({"a", "b"}, storage_user1_cohorts)
        self.assertEqual({"b"}, storage_user2_cohorts)

    def test_filter_cohorts_already_computed_equivalent_cohorts_are_filtered(self):
        self.storage.put_cohort(Cohort("a", last_modified=0, size=0, member_ids=set()))
        self.storage.put_cohort(Cohort("b", last_modified=0, size=0, member_ids=set()))
        self.api.get_cohort.side_effect = [
            Cohort(id="a", last_modified=0, size=0, member_ids=set()),
            Cohort(id="b", last_modified=1, size=2, member_ids={"1", "2"})
        ]

        self.loader.load_cohort("a").result()
        self.loader.load_cohort("b").result()

        storage_description_a = self.storage.get_cohort("a")
        storage_description_b = self.storage.get_cohort("b")
        self.assertEqual(Cohort(id="a", last_modified=0, size=0, member_ids=set()), storage_description_a)
        self.assertEqual(Cohort(id="b", last_modified=1, size=2, member_ids={"1", "2"}), storage_description_b)

        storage_user1_cohorts = self.storage.get_cohorts_for_user("1", {"a", "b"})
        storage_user2_cohorts = self.storage.get_cohorts_for_user("2", {"a", "b"})
        self.assertEqual({"b"}, storage_user1_cohorts)
        self.assertEqual({"b"}, storage_user2_cohorts)

    def test_load_download_failure_throws(self):
        self.api.get_cohort.side_effect = [
            Cohort(id="a", last_modified=0, size=1, member_ids={"1"}),
            Exception("Connection timed out"),
            Cohort(id="c", last_modified=0, size=1, member_ids={"1"})
        ]

        self.loader.load_cohort("a").result()
        with self.assertRaises(Exception):
            self.loader.load_cohort("b").result()
        self.loader.load_cohort("c").result()

        self.assertEqual({"a", "c"}, self.storage.get_cohorts_for_user("1", {"a", "b", "c"}))

if __name__ == "__main__":
    unittest.main()
