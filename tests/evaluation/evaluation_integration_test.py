import unittest
from typing import Dict, Optional, Any, List
import requests

from src.amplitude_experiment.evaluation.engine import EvaluationEngine
from src.amplitude_experiment.evaluation.types import EvaluationFlag


class EvaluationIntegrationTestCase(unittest.TestCase):
    """Integration tests for the EvaluationEngine."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests."""
        cls.deployment_key = "server-NgJxxvg8OGwwBsWVXqyxQbdiflbhvugy"
        cls.engine = EvaluationEngine()
        cls.flags = cls.get_flags(cls.deployment_key)

    def test_off(self):
        """Test off state."""
        user = self.user_context("user_id", "device_id")
        result = self.engine.evaluate(user, self.flags)["test-off"]
        self.assertEqual(result.key, "off")

    def test_on(self):
        """Test on state."""
        user = self.user_context("user_id", "device_id")
        result = self.engine.evaluate(user, self.flags)["test-on"]
        self.assertEqual(result.key, "on")

    def test_individual_inclusions_match(self):
        """Test individual inclusions matching."""
        # Match user ID
        user = self.user_context("user_id")
        result = self.engine.evaluate(user, self.flags)["test-individual-inclusions"]
        self.assertEqual(result.key, "on")
        self.assertEqual(result.metadata.get("segmentName"), "individual-inclusions")

        # Match device ID
        user = self.user_context(None, "device_id")
        result = self.engine.evaluate(user, self.flags)["test-individual-inclusions"]
        self.assertEqual(result.key, "on")
        self.assertEqual(result.metadata.get("segmentName"), "individual-inclusions")

        # Doesn't match user ID
        user = self.user_context("not_user_id")
        result = self.engine.evaluate(user, self.flags)["test-individual-inclusions"]
        self.assertEqual(result.key, "off")

        # Doesn't match device ID
        user = self.user_context(None, "not_device_id")
        result = self.engine.evaluate(user, self.flags)["test-individual-inclusions"]
        self.assertEqual(result.key, "off")

    def test_flag_dependencies_on(self):
        """Test flag dependencies in on state."""
        user = self.user_context("user_id", "device_id")
        result = self.engine.evaluate(user, self.flags)["test-flag-dependencies-on"]
        self.assertEqual(result.key, "on")

    def test_flag_dependencies_off(self):
        """Test flag dependencies in off state."""
        user = self.user_context("user_id", "device_id")
        result = self.engine.evaluate(user, self.flags)["test-flag-dependencies-off"]
        self.assertEqual(result.key, "off")
        self.assertEqual(result.metadata.get("segmentName"), "flag-dependencies")

    def test_sticky_bucketing(self):
        """Test sticky bucketing behavior."""
        # On
        user = self.user_context("user_id", "device_id", None, {
            "[Experiment] test-sticky-bucketing": "on"
        })
        result = self.engine.evaluate(user, self.flags)["test-sticky-bucketing"]
        self.assertEqual(result.key, "on")
        self.assertEqual(result.metadata.get("segmentName"), "sticky-bucketing")

        # Off
        user = self.user_context("user_id", "device_id", None, {
            "[Experiment] test-sticky-bucketing": "off"
        })
        result = self.engine.evaluate(user, self.flags)["test-sticky-bucketing"]
        self.assertEqual(result.key, "off")
        self.assertEqual(result.metadata.get("segmentName"), "All Other Users")

        # Non-variant
        user = self.user_context("user_id", "device_id", None, {
            "[Experiment] test-sticky-bucketing": "not-a-variant"
        })
        result = self.engine.evaluate(user, self.flags)["test-sticky-bucketing"]
        self.assertEqual(result.key, "off")
        self.assertEqual(result.metadata.get("segmentName"), "All Other Users")

    def test_experiment(self):
        """Test experiment behavior."""
        user = self.user_context("user_id", "device_id")
        result = self.engine.evaluate(user, self.flags)["test-experiment"]
        self.assertEqual(result.key, "on")
        self.assertEqual(result.metadata.get("experimentKey"), "exp-1")

    def test_flag(self):
        """Test flag behavior."""
        user = self.user_context("user_id", "device_id")
        result = self.engine.evaluate(user, self.flags)["test-flag"]
        self.assertEqual(result.key, "on")
        self.assertIsNone(result.metadata.get("experimentKey"))

    def test_multiple_conditions_and_values(self):
        """Test multiple conditions and values."""
        # All match
        user = self.user_context("user_id", "device_id", None, {
            "key-1": "value-1",
            "key-2": "value-2",
            "key-3": "value-3"
        })
        result = self.engine.evaluate(user, self.flags)["test-multiple-conditions-and-values"]
        self.assertEqual(result.key, "on")

        # Some match
        user = self.user_context("user_id", "device_id", None, {
            "key-1": "value-1",
            "key-2": "value-2"
        })
        result = self.engine.evaluate(user, self.flags)["test-multiple-conditions-and-values"]
        self.assertEqual(result.key, "off")

    def test_amplitude_property_targeting(self):
        """Test amplitude property targeting."""
        user = self.user_context("user_id")
        result = self.engine.evaluate(user, self.flags)["test-amplitude-property-targeting"]
        self.assertEqual(result.key, "on")

    def test_cohort_targeting(self):
        """Test cohort targeting."""
        user = self.user_context(None, None, None, None, ["u0qtvwla", "12345678"])
        result = self.engine.evaluate(user, self.flags)["test-cohort-targeting"]
        self.assertEqual(result.key, "on")

        user = self.user_context(None, None, None, None, ["12345678", "87654321"])
        result = self.engine.evaluate(user, self.flags)["test-cohort-targeting"]
        self.assertEqual(result.key, "off")

    def test_group_name_targeting(self):
        """Test group name targeting."""
        user = self.group_context("org name", "amplitude")
        result = self.engine.evaluate(user, self.flags)["test-group-name-targeting"]
        self.assertEqual(result.key, "on")

    def test_group_property_targeting(self):
        """Test group property targeting."""
        user = self.group_context("org name", "amplitude", {
            "org plan": "enterprise2"
        })
        result = self.engine.evaluate(user, self.flags)["test-group-property-targeting"]
        self.assertEqual(result.key, "on")

    def test_amplitude_id_bucketing(self):
        """Test amplitude ID bucketing."""
        user = self.user_context(None, None, "1234567890")
        result = self.engine.evaluate(user, self.flags)["test-amplitude-id-bucketing"]
        self.assertEqual(result.key, "on")

    def test_user_id_bucketing(self):
        """Test user ID bucketing."""
        user = self.user_context("user_id")
        result = self.engine.evaluate(user, self.flags)["test-user-id-bucketing"]
        self.assertEqual(result.key, "on")

    def test_device_id_bucketing(self):
        """Test device ID bucketing."""
        user = self.user_context(None, "device_id")
        result = self.engine.evaluate(user, self.flags)["test-device-id-bucketing"]
        self.assertEqual(result.key, "on")

    def test_custom_user_property_bucketing(self):
        """Test custom user property bucketing."""
        user = self.user_context(None, None, None, {"key": "value"})
        result = self.engine.evaluate(user, self.flags)["test-custom-user-property-bucketing"]
        self.assertEqual(result.key, "on")

    def test_group_name_bucketing(self):
        """Test group name bucketing."""
        user = self.group_context("org name", "amplitude")
        result = self.engine.evaluate(user, self.flags)["test-group-name-bucketing"]
        self.assertEqual(result.key, "on")

    def test_group_property_bucketing(self):
        """Test group property bucketing."""
        user = self.group_context("org name", "amplitude", {
            "org plan": "enterprise2"
        })
        result = self.engine.evaluate(user, self.flags)["test-group-name-bucketing"]
        self.assertEqual(result.key, "on")

    def test_1_percent_allocation(self):
        """Test 1% allocation."""
        on_count = 0
        for i in range(10000):
            user = self.user_context(None, str(i + 1))
            result = self.engine.evaluate(user, self.flags)["test-1-percent-allocation"]
            if result.key == "on":
                on_count += 1
        self.assertEqual(on_count, 107)

    def test_50_percent_allocation(self):
        """Test 50% allocation."""
        on_count = 0
        for i in range(10000):
            user = self.user_context(None, str(i + 1))
            result = self.engine.evaluate(user, self.flags)["test-50-percent-allocation"]
            if result.key == "on":
                on_count += 1
        self.assertEqual(on_count, 5009)

    def test_99_percent_allocation(self):
        """Test 99% allocation."""
        on_count = 0
        for i in range(10000):
            user = self.user_context(None, str(i + 1))
            result = self.engine.evaluate(user, self.flags)["test-99-percent-allocation"]
            if result.key == "on":
                on_count += 1
        self.assertEqual(on_count, 9900)

    def test_amplitude_id_bucketing(self):
        """Test amplitude ID bucketing."""
        user = self.user_context(None, None, "1234567890")
        result = self.engine.evaluate(user, self.flags)["test-amplitude-id-bucketing"]
        self.assertEqual(result.key, "on")

    def test_user_id_bucketing(self):
        """Test user ID bucketing."""
        user = self.user_context("user_id")
        result = self.engine.evaluate(user, self.flags)["test-user-id-bucketing"]
        self.assertEqual(result.key, "on")

    def test_device_id_bucketing(self):
        """Test device ID bucketing."""
        user = self.user_context(None, "device_id")
        result = self.engine.evaluate(user, self.flags)["test-device-id-bucketing"]
        self.assertEqual(result.key, "on")

    def test_custom_user_property_bucketing(self):
        """Test custom user property bucketing."""
        user = self.user_context(None, None, None, {"key": "value"})
        result = self.engine.evaluate(user, self.flags)["test-custom-user-property-bucketing"]
        self.assertEqual(result.key, "on")

    def test_group_name_bucketing(self):
        """Test group name bucketing."""
        user = self.group_context("org name", "amplitude")
        result = self.engine.evaluate(user, self.flags)["test-group-name-bucketing"]
        self.assertEqual(result.key, "on")

    def test_group_property_bucketing(self):
        """Test group property bucketing."""
        user = self.group_context("org name", "amplitude", {
            "org plan": "enterprise2"
        })
        result = self.engine.evaluate(user, self.flags)["test-group-name-bucketing"]
        self.assertEqual(result.key, "on")

    def test_1_percent_allocation(self):
        """Test 1% allocation."""
        on_count = 0
        for i in range(10000):
            user = self.user_context(None, str(i + 1))
            result = self.engine.evaluate(user, self.flags)["test-1-percent-allocation"]
            if result.key == "on":
                on_count += 1
        self.assertEqual(on_count, 107)

    def test_50_percent_allocation(self):
        """Test 50% allocation."""
        on_count = 0
        for i in range(10000):
            user = self.user_context(None, str(i + 1))
            result = self.engine.evaluate(user, self.flags)["test-50-percent-allocation"]
            if result.key == "on":
                on_count += 1
        self.assertEqual(on_count, 5009)

    def test_99_percent_allocation(self):
        """Test 99% allocation."""
        on_count = 0
        for i in range(10000):
            user = self.user_context(None, str(i + 1))
            result = self.engine.evaluate(user, self.flags)["test-99-percent-allocation"]
            if result.key == "on":
                on_count += 1
        self.assertEqual(on_count, 9900)

    def test_1_percent_distribution(self):
        """Test 1% distribution."""
        control_count = 0
        treatment_count = 0
        for i in range(10000):
            user = self.user_context(None, str(i + 1))
            result = self.engine.evaluate(user, self.flags)["test-1-percent-distribution"]
            if result.key == "control":
                control_count += 1
            elif result.key == "treatment":
                treatment_count += 1
        self.assertEqual(control_count, 106)
        self.assertEqual(treatment_count, 9894)

    def test_50_percent_distribution(self):
        """Test 50% distribution."""
        control_count = 0
        treatment_count = 0
        for i in range(10000):
            user = self.user_context(None, str(i + 1))
            result = self.engine.evaluate(user, self.flags)["test-50-percent-distribution"]
            if result.key == "control":
                control_count += 1
            elif result.key == "treatment":
                treatment_count += 1
        self.assertEqual(control_count, 4990)
        self.assertEqual(treatment_count, 5010)

    def test_99_percent_distribution(self):
        """Test 99% distribution."""
        control_count = 0
        treatment_count = 0
        for i in range(10000):
            user = self.user_context(None, str(i + 1))
            result = self.engine.evaluate(user, self.flags)["test-99-percent-distribution"]
            if result.key == "control":
                control_count += 1
            elif result.key == "treatment":
                treatment_count += 1
        self.assertEqual(control_count, 9909)
        self.assertEqual(treatment_count, 91)

    def test_multiple_distributions(self):
        """Test multiple distributions."""
        a_count = 0
        b_count = 0
        c_count = 0
        d_count = 0
        for i in range(10000):
            user = self.user_context(None, str(i + 1))
            result = self.engine.evaluate(user, self.flags)["test-multiple-distributions"]
            if result.key == "a":
                a_count += 1
            elif result.key == "b":
                b_count += 1
            elif result.key == "c":
                c_count += 1
            elif result.key == "d":
                d_count += 1
        self.assertEqual(a_count, 2444)
        self.assertEqual(b_count, 2634)
        self.assertEqual(c_count, 2447)
        self.assertEqual(d_count, 2475)

    def test_is(self):
        """Test 'is' operator."""
        user = self.user_context(None, None, None, {"key": "value"})
        result = self.engine.evaluate(user, self.flags)["test-is"]
        self.assertEqual(result.key, "on")

    def test_is_not(self):
        """Test 'is not' operator."""
        user = self.user_context(None, None, None, {"key": "value"})
        result = self.engine.evaluate(user, self.flags)["test-is-not"]
        self.assertEqual(result.key, "on")

    def test_contains(self):
        """Test 'contains' operator."""
        user = self.user_context(None, None, None, {"key": "value"})
        result = self.engine.evaluate(user, self.flags)["test-contains"]
        self.assertEqual(result.key, "on")

    def test_does_not_contain(self):
        """Test 'does not contain' operator."""
        user = self.user_context(None, None, None, {"key": "value"})
        result = self.engine.evaluate(user, self.flags)["test-does-not-contain"]
        self.assertEqual(result.key, "on")

    def test_less(self):
        """Test 'less than' operator."""
        user = self.user_context(None, None, None, {"key": "-1"})
        result = self.engine.evaluate(user, self.flags)["test-less"]
        self.assertEqual(result.key, "on")

    def test_less_or_equal(self):
        """Test 'less than or equal' operator."""
        user = self.user_context(None, None, None, {"key": "0"})
        result = self.engine.evaluate(user, self.flags)["test-less-or-equal"]
        self.assertEqual(result.key, "on")

    def test_greater(self):
        """Test 'greater than' operator."""
        user = self.user_context(None, None, None, {"key": "1"})
        result = self.engine.evaluate(user, self.flags)["test-greater"]
        self.assertEqual(result.key, "on")

    def test_greater_or_equal(self):
        """Test 'greater than or equal' operator."""
        user = self.user_context(None, None, None, {"key": "0"})
        result = self.engine.evaluate(user, self.flags)["test-greater-or-equal"]
        self.assertEqual(result.key, "on")

    def test_version_less(self):
        """Test version 'less than' operator."""
        user = self.freeform_user_context({"version": "1.9.0"})
        result = self.engine.evaluate(user, self.flags)["test-version-less"]
        self.assertEqual(result.key, "on")

    def test_version_less_or_equal(self):
        """Test version 'less than or equal' operator."""
        user = self.freeform_user_context({"version": "1.10.0"})
        result = self.engine.evaluate(user, self.flags)["test-version-less-or-equal"]
        self.assertEqual(result.key, "on")

    def test_version_greater(self):
        """Test version 'greater than' operator."""
        user = self.freeform_user_context({"version": "1.10.0"})
        result = self.engine.evaluate(user, self.flags)["test-version-greater"]
        self.assertEqual(result.key, "on")

    def test_version_greater_or_equal(self):
        """Test version 'greater than or equal' operator."""
        user = self.freeform_user_context({"version": "1.9.0"})
        result = self.engine.evaluate(user, self.flags)["test-version-greater-or-equal"]
        self.assertEqual(result.key, "on")

    def test_set_is(self):
        """Test 'set is' operator."""
        user = self.user_context(None, None, None, {"key": ["1", "2", "3"]})
        result = self.engine.evaluate(user, self.flags)["test-set-is"]
        self.assertEqual(result.key, "on")

    def test_set_is_not(self):
        """Test 'set is not' operator."""
        user = self.user_context(None, None, None, {"key": ["1", "2"]})
        result = self.engine.evaluate(user, self.flags)["test-set-is-not"]
        self.assertEqual(result.key, "on")

    def test_set_contains(self):
        """Test 'set contains' operator."""
        user = self.user_context(None, None, None, {"key": ["1", "2", "3", "4"]})
        result = self.engine.evaluate(user, self.flags)["test-set-contains"]
        self.assertEqual(result.key, "on")

    def test_set_does_not_contain(self):
        """Test 'set does not contain' operator."""
        user = self.user_context(None, None, None, {"key": ["1", "2", "4"]})
        result = self.engine.evaluate(user, self.flags)["test-set-does-not-contain"]
        self.assertEqual(result.key, "on")

    def test_set_contains_any(self):
        """Test 'set contains any' operator."""
        user = self.user_context(None, None, None, None, ["u0qtvwla", "12345678"])
        result = self.engine.evaluate(user, self.flags)["test-set-contains-any"]
        self.assertEqual(result.key, "on")

    def test_set_does_not_contain_any(self):
        """Test 'set does not contain any' operator."""
        user = self.user_context(None, None, None, None, ["12345678", "87654321"])
        result = self.engine.evaluate(user, self.flags)["test-set-does-not-contain-any"]
        self.assertEqual(result.key, "on")

    def test_glob_match(self):
        """Test glob match operator."""
        user = self.user_context(None, None, None, {"key": "/path/1/2/3/end"})
        result = self.engine.evaluate(user, self.flags)["test-glob-match"]
        self.assertEqual(result.key, "on")

    def test_glob_does_not_match(self):
        """Test glob does not match operator."""
        user = self.user_context(None, None, None, {"key": "/path/1/2/3"})
        result = self.engine.evaluate(user, self.flags)["test-glob-does-not-match"]
        self.assertEqual(result.key, "on")

    def test_is_with_booleans(self):
        """Test 'is' operator with boolean values."""
        user = self.user_context(None, None, None, {
            "true": "TRUE",
            "false": "FALSE"
        })
        result = self.engine.evaluate(user, self.flags)["test-is-with-booleans"]
        self.assertEqual(result.key, "on")

        user = self.user_context(None, None, None, {
            "true": "True",
            "false": "False"
        })
        result = self.engine.evaluate(user, self.flags)["test-is-with-booleans"]
        self.assertEqual(result.key, "on")

        user = self.user_context(None, None, None, {
            "true": "true",
            "false": "false"
        })
        result = self.engine.evaluate(user, self.flags)["test-is-with-booleans"]
        self.assertEqual(result.key, "on")

    @staticmethod
    def freeform_user_context(user: Dict[str, Any]) -> Dict[str, Any]:
        """Create a freeform user context dictionary."""
        return {"user": user}

    @staticmethod
    def user_context(
            user_id: Optional[str] = None,
            device_id: Optional[str] = None,
            amplitude_id: Optional[str] = None,
            user_properties: Optional[Dict[str, Any]] = None,
            cohort_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a user context dictionary."""
        return {
            "user": {
                "user_id": user_id,
                "device_id": device_id,
                "amplitude_id": amplitude_id,
                "user_properties": user_properties,
                "cohort_ids": cohort_ids
            }
        }

    @staticmethod
    def group_context(
            group_type: str,
            group_name: str,
            group_properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a group context dictionary."""
        return {
            "groups": {
                group_type: {
                    "group_name": group_name,
                    "group_properties": group_properties
                }
            }
        }

    @staticmethod
    def get_flags(deployment_key: str) -> List[EvaluationFlag]:
        """Fetch flags from the server and convert to EvaluationFlag objects."""
        server_url = "https://api.lab.amplitude.com"
        response = requests.get(
            f"{server_url}/sdk/v2/flags?eval_mode=remote",
            headers={"Authorization": f"Api-Key {deployment_key}"}
        )

        if response.status_code != 200:
            raise Exception(f"Response error {response.status_code}")

        return EvaluationFlag.schema().load(response.json(), many=True)


if __name__ == "__main__":
    unittest.main()
