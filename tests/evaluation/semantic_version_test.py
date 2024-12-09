import unittest
from src.amplitude_experiment.evaluation.semantic_version import SemanticVersion
from src.amplitude_experiment.evaluation.types import EvaluationOperator

class SemanticVersionTestCase(unittest.TestCase):
    def test_invalid_versions(self):
        # Just major
        self.assert_invalid_version("10")

        # Trailing dots
        self.assert_invalid_version("10.")
        self.assert_invalid_version("10..")
        self.assert_invalid_version("10.2.")
        self.assert_invalid_version("10.2.33.")
        # Note: Trailing dots on prerelease tags are not handled because prerelease tags
        # are considered strings anyway for comparison

        # Dots in the middle
        self.assert_invalid_version("10..2.33")
        self.assert_invalid_version("102...33")

        # Invalid characters
        self.assert_invalid_version("a.2.3")
        self.assert_invalid_version("23!")
        self.assert_invalid_version("23.#5")
        self.assert_invalid_version("")
        self.assert_invalid_version(None)

        # More numbers
        self.assert_invalid_version("2.3.4.567")
        self.assert_invalid_version("2.3.4.5.6.7")

        # Prerelease if provided should always have major, minor, patch
        self.assert_invalid_version("10.2.alpha")
        self.assert_invalid_version("10.alpha")
        self.assert_invalid_version("alpha-1.2.3")

        # Prerelease should be separated by a hyphen after patch
        self.assert_invalid_version("10.2.3alpha")
        self.assert_invalid_version("10.2.3alpha-1.2.3")

        # Negative numbers
        self.assert_invalid_version("-10.1")
        self.assert_invalid_version("10.-1")

    def test_valid_versions(self):
        self.assert_valid_version("100.2")
        self.assert_valid_version("0.102.39")
        self.assert_valid_version("0.0.0")

        # Versions with leading 0s would be converted to int
        self.assert_valid_version("01.02")
        self.assert_valid_version("001.001100.000900")

        # Prerelease tags
        self.assert_valid_version("10.20.30-alpha")
        self.assert_valid_version("10.20.30-1.x.y")
        self.assert_valid_version("10.20.30-aslkjd")
        self.assert_valid_version("10.20.30-b894")
        self.assert_valid_version("10.20.30-b8c9")

    def test_version_comparison(self):
        # EQUALS case
        self.assert_version_comparison("66.12.23", EvaluationOperator.IS, "66.12.23")
        # Patch if not specified equals 0
        self.assert_version_comparison("5.6", EvaluationOperator.IS, "5.6.0")
        # Leading 0s are not stored when parsed
        self.assert_version_comparison("06.007.0008", EvaluationOperator.IS, "6.7.8")
        # With pre-release
        self.assert_version_comparison("1.23.4-b-1.x.y", EvaluationOperator.IS, "1.23.4-b-1.x.y")

        # DOES NOT EQUAL case
        self.assert_version_comparison("1.23.4-alpha-1.2", EvaluationOperator.IS_NOT, "1.23.4-alpha-1")
        # Trailing 0s aren't stripped
        self.assert_version_comparison("1.2.300", EvaluationOperator.IS_NOT, "1.2.3")
        self.assert_version_comparison("1.20.3", EvaluationOperator.IS_NOT, "1.2.3")

        # LESS THAN case
        # Patch of .1 makes it greater
        self.assert_version_comparison("50.2", EvaluationOperator.VERSION_LESS_THAN, "50.2.1")
        # Minor 9 > minor 20
        self.assert_version_comparison("20.9", EvaluationOperator.VERSION_LESS_THAN, "20.20")
        # Same version with pre-release should be lesser
        self.assert_version_comparison("20.9.4-alpha1", EvaluationOperator.VERSION_LESS_THAN, "20.9.4")
        # Compare prerelease as strings
        self.assert_version_comparison("20.9.4-a-1.2.3", EvaluationOperator.VERSION_LESS_THAN, "20.9.4-a-1.3")
        # Since prerelease is compared as strings a1.23 < a1.5 because 2 < 5
        self.assert_version_comparison("20.9.4-a1.23", EvaluationOperator.VERSION_LESS_THAN, "20.9.4-a1.5")

        # GREATER THAN case
        self.assert_version_comparison("12.30.2", EvaluationOperator.VERSION_GREATER_THAN, "12.4.1")
        # 100 > 1
        self.assert_version_comparison("7.100", EvaluationOperator.VERSION_GREATER_THAN, "7.1")
        # 10 > 9
        self.assert_version_comparison("7.10", EvaluationOperator.VERSION_GREATER_THAN, "7.9")
        # Converts to 7.10.20 > 7.9.1
        self.assert_version_comparison("07.010.0020", EvaluationOperator.VERSION_GREATER_THAN, "7.009.1")
        # Patch comparison comes first
        self.assert_version_comparison("20.5.6-b1.2.x", EvaluationOperator.VERSION_GREATER_THAN, "20.5.5")

    def assert_invalid_version(self, version: str):
        assert SemanticVersion.parse(version) is None

    def assert_valid_version(self, version: str):
        assert SemanticVersion.parse(version) is not None

    def assert_version_comparison(self, v1: str, op: EvaluationOperator, v2: str):
        sv1 = SemanticVersion.parse(v1)
        sv2 = SemanticVersion.parse(v2)

        assert sv1 is not None
        assert sv2 is not None

        if op == EvaluationOperator.IS:
            assert sv1.compare_to(sv2) == 0
        elif op == EvaluationOperator.IS_NOT:
            assert sv1.compare_to(sv2) != 0
        elif op == EvaluationOperator.VERSION_LESS_THAN:
            assert sv1.compare_to(sv2) < 0
        elif op == EvaluationOperator.VERSION_GREATER_THAN:
            assert sv1.compare_to(sv2) > 0
