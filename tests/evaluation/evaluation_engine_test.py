import unittest
from typing import Any, Dict, List, Optional

from src.amplitude_experiment.evaluation.engine import EvaluationEngine
from src.amplitude_experiment.evaluation.types import (
    EvaluationCondition,
    EvaluationFlag,
    EvaluationOperator,
    EvaluationSegment,
    EvaluationVariant,
)


class EvaluationEngineTestCase(unittest.TestCase):
    """Unit tests for EvaluationEngine covering non-set array matching."""

    def setUp(self):
        self.engine = EvaluationEngine()

    @staticmethod
    def flag_with_condition(op: str, values: List[str]) -> EvaluationFlag:
        return EvaluationFlag(
            key="test-flag",
            variants={"on": EvaluationVariant(key="on", value="on")},
            segments=[
                EvaluationSegment(
                    conditions=[[
                        EvaluationCondition(
                            selector=["context", "user", "user_properties", "test_prop"],
                            op=op,
                            values=values,
                        )
                    ]],
                    variant="on",
                )
            ],
        )

    @staticmethod
    def context_with_prop(value: Any) -> Dict[str, Any]:
        return {"user": {"user_properties": {"test_prop": value}}}

    def evaluate(self, prop_value: Any, op: str, values: List[str]) -> Optional[EvaluationVariant]:
        flag = self.flag_with_condition(op, values)
        context = self.context_with_prop(prop_value)
        return self.engine.evaluate(context, [flag]).get("test-flag")

    def assert_match(self, prop_value: Any, op: str, values: List[str]):
        variant = self.evaluate(prop_value, op, values)
        self.assertIsNotNone(
            variant, f"Expected match for prop={prop_value!r} op={op!r} values={values!r}"
        )
        self.assertEqual(variant.key, "on")

    def assert_no_match(self, prop_value: Any, op: str, values: List[str]):
        variant = self.evaluate(prop_value, op, values)
        self.assertIsNone(
            variant, f"Expected no match for prop={prop_value!r} op={op!r} values={values!r}"
        )

    def test_scalar_string_is_match(self):
        self.assert_match("hello", EvaluationOperator.IS, ["hello"])

    def test_scalar_string_contains_match(self):
        self.assert_match("hello", EvaluationOperator.CONTAINS, ["ell"])

    def test_scalar_string_greater_than_match(self):
        self.assert_match("2", EvaluationOperator.GREATER_THAN, ["1"])

    def test_scalar_string_is_no_match(self):
        self.assert_no_match("world", EvaluationOperator.IS, ["hello"])

    def test_non_string_scalar_greater_than(self):
        self.assert_match(42, EvaluationOperator.GREATER_THAN, ["1"])

    def test_non_string_scalar_is_boolean(self):
        self.assert_match(True, EvaluationOperator.IS, ["true"])

    def test_json_array_string_set_operator(self):
        self.assert_match('["a","b"]', EvaluationOperator.SET_CONTAINS, ["a"])

    def test_json_array_string_non_set_operator(self):
        self.assert_match('["a","b"]', EvaluationOperator.IS, ["a"])

    def test_collection_set_operator(self):
        self.assert_match(["a", "b"], EvaluationOperator.SET_CONTAINS, ["a"])

    def test_collection_non_set_operator(self):
        self.assert_match(["a", "b"], EvaluationOperator.IS, ["a"])

    def test_malformed_json_array_falls_through(self):
        self.assert_match("[broken", EvaluationOperator.IS, ["[broken"])

    def test_empty_json_array_set_operator(self):
        self.assert_no_match("[]", EvaluationOperator.SET_CONTAINS, ["a"])

    def test_empty_json_array_non_set_operator(self):
        # Not in the spec table; locks in any([]) -> False for the non-set path.
        self.assert_no_match("[]", EvaluationOperator.IS, ["a"])

    def test_leading_whitespace_not_parsed_non_set(self):
        self.assert_match(' ["a"]', EvaluationOperator.IS, [' ["a"]'])

    def test_leading_whitespace_not_parsed_set(self):
        self.assert_no_match(' ["a"]', EvaluationOperator.SET_CONTAINS, ["a"])


if __name__ == "__main__":
    unittest.main()
