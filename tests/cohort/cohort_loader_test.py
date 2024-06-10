import unittest
from unittest.mock import MagicMock

from src.amplitude_experiment.cohort.cohort_description import CohortDescription
from src.amplitude_experiment.cohort.cohort_loader import CohortLoader
from src.amplitude_experiment.cohort.cohort_storage import InMemoryCohortStorage


class CohortLoaderTest(unittest.TestCase):
    def setUp(self):
        self.api = MagicMock()
        self.storage = InMemoryCohortStorage()
        self.loader = CohortLoader(self.api, self.storage)

    def test_load_success(self):
        self.api.get_cohort_description.side_effect = [cohort_description("a"), cohort_description("b")]
        self.api.get_cohort_members.side_effect = [{"1"}, {"1", "2"}]

        # Submitting tasks asynchronously
        future_a = self.loader.load_cohort("a")
        future_b = self.loader.load_cohort("b")

        # Asserting after tasks complete
        future_a.result()
        future_b.result()

        storage_description_a = self.storage.get_cohort_description("a")
        storage_description_b = self.storage.get_cohort_description("b")
        self.assertEqual(cohort_description("a"), storage_description_a)
        self.assertEqual(cohort_description("b"), storage_description_b)

        storage_user1_cohorts = self.storage.get_cohorts_for_user("1", {"a", "b"})
        storage_user2_cohorts = self.storage.get_cohorts_for_user("2", {"a", "b"})
        self.assertEqual({"a", "b"}, storage_user1_cohorts)
        self.assertEqual({"b"}, storage_user2_cohorts)

    def test_filter_cohorts_already_computed_equivalent_cohorts_are_filtered(self):
        self.storage.put_cohort(cohort_description("a", last_computed=0), set())
        self.storage.put_cohort(cohort_description("b", last_computed=0), set())
        self.api.get_cohort_description.side_effect = [
            cohort_description("a", last_computed=0),
            cohort_description("b", last_computed=1)
        ]
        self.api.get_cohort_members.side_effect = [{"1", "2"}]

        self.loader.load_cohort("a").result()
        self.loader.load_cohort("b").result()

        storage_description_a = self.storage.get_cohort_description("a")
        storage_description_b = self.storage.get_cohort_description("b")
        self.assertEqual(cohort_description("a", last_computed=0), storage_description_a)
        self.assertEqual(cohort_description("b", last_computed=1), storage_description_b)

        storage_user1_cohorts = self.storage.get_cohorts_for_user("1", {"a", "b"})
        storage_user2_cohorts = self.storage.get_cohorts_for_user("2", {"a", "b"})
        self.assertEqual({"b"}, storage_user1_cohorts)
        self.assertEqual({"b"}, storage_user2_cohorts)

    def test_load_download_failure_throws(self):
        self.api.get_cohort_description.side_effect = [
            cohort_description("a"),
            cohort_description("b"),
            cohort_description("c")
        ]
        self.api.get_cohort_members.side_effect = [{"1"}, Exception("Connection timed out"), {"1"}]

        self.loader.load_cohort("a").result()
        with self.assertRaises(Exception):
            self.loader.load_cohort("b").result()
        self.loader.load_cohort("c").result()

        self.assertEqual({"a", "c"}, self.storage.get_cohorts_for_user("1", {"a", "b", "c"}))


def cohort_description(cohort_id, last_computed=0, size=0):
    return CohortDescription(id=cohort_id, last_computed=last_computed, size=size)


if __name__ == "__main__":
    unittest.main()
