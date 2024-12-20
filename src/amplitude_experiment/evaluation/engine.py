from typing import Any, Callable, List, Optional, Set, Union, Dict
import json
import re

from .murmur3 import hash32x86
from .select import select
from .types import EvaluationOperator, EvaluationFlag, EvaluationVariant, EvaluationSegment, EvaluationCondition
from .semantic_version import SemanticVersion


class EvaluationEngine:
    """Feature flag evaluation engine."""

    def evaluate(
            self,
            context: Dict[str, Any],
            flags: List[EvaluationFlag]
    ) -> Dict[str, EvaluationVariant]:
        """Evaluate a list of feature flags against a context."""
        results: Dict[str, EvaluationVariant] = {}
        target = {
            'context': context,
            'result': results
        }

        for flag in flags:
            variant = self.evaluate_flag(target, flag)
            if variant:
                results[flag.key] = variant

        return results

    def evaluate_flag(
            self,
            target: Dict[str, Any],
            flag: EvaluationFlag
    ) -> Optional[EvaluationVariant]:
        """Evaluate a single feature flag."""
        result = None
        for segment in flag.segments:
            result = self.evaluate_segment(target, flag, segment)
            if result:
                # Merge all metadata into the result
                metadata = {}
                if flag.metadata:
                    metadata.update(flag.metadata)
                if segment.metadata:
                    metadata.update(segment.metadata)
                if result.metadata:
                    metadata.update(result.metadata)
                result = EvaluationVariant(
                    key=result.key,
                    value=result.value,
                    payload=result.payload,
                    metadata=metadata
                )
                break
        return result

    def evaluate_segment(
            self,
            target: Dict[str, Any],
            flag: EvaluationFlag,
            segment: EvaluationSegment
    ) -> Optional[EvaluationVariant]:
        """Evaluate a segment of a feature flag."""
        if not segment.conditions:
            # Null conditions always match
            variant_key = self.bucket(target, segment)
            if variant_key is not None:
                return flag.variants.get(variant_key)
            return None

        match = self.evaluate_conditions(target, segment.conditions)

        # On match, bucket the user
        if match:
            variant_key = self.bucket(target, segment)
            if variant_key is not None:
                return flag.variants.get(variant_key)
            return None

        return None

    def evaluate_conditions(
            self,
            target: Dict[str, Any],
            conditions: List[List[EvaluationCondition]]
    ) -> bool:
        """Evaluate conditions using OR/AND logic."""
        # Outer list logic is "or" (||)
        for inner_conditions in conditions:
            match = True

            for condition in inner_conditions:
                match = self.match_condition(target, condition)
                if not match:
                    break

            if match:
                return True

        return False

    def match_condition(
            self,
            target: Dict[str, Any],
            condition: EvaluationCondition
    ) -> bool:
        """Match a single condition."""
        prop_value = select(target, condition.selector)

        # We need special matching for null properties and set type prop values
        # and operators. All other values are matched as strings, since the
        # filter values are always strings.
        if not prop_value:
            return self.match_null(condition.op, condition.values)
        elif self.is_set_operator(condition.op):
            prop_value_string_list = self.coerce_string_array(prop_value)
            if not prop_value_string_list:
                return False
            return self.match_set(prop_value_string_list, condition.op, condition.values)
        else:
            prop_value_string = self.coerce_string(prop_value)
            if prop_value_string is not None:
                return self.match_string(
                    prop_value_string,
                    condition.op,
                    condition.values
                )
            return False

    def get_hash(self, key: str) -> int:
        """Generate a hash value from a key."""
        return hash32x86(key)

    def bucket(
            self,
            target: Dict[str, Any],
            segment: EvaluationSegment
    ) -> Optional[str]:
        """Bucket a target into a variant based on segment configuration."""
        if not segment.bucket:
            # A null bucket means the segment is fully rolled out. Select the
            # default variant.
            return segment.variant

        # Select the bucketing value
        bucketing_value = self.coerce_string(
            select(target, segment.bucket.selector)
        )
        if not bucketing_value or len(bucketing_value) == 0:
            # A null or empty bucketing value cannot be bucketed. Select the
            # default variant.
            return segment.variant

        # Salt and hash the value, and compute the allocation and distribution
        # values
        key_to_hash = f"{segment.bucket.salt}/{bucketing_value}"
        hash_value = self.get_hash(key_to_hash)
        allocation_value = hash_value % 100
        distribution_value = hash_value // 100

        for allocation in segment.bucket.allocations:
            allocation_start = allocation.range[0]
            allocation_end = allocation.range[1]

            if allocation_start <= allocation_value < allocation_end:

                for distribution in allocation.distributions:
                    distribution_start = distribution.range[0]
                    distribution_end = distribution.range[1]

                    if distribution_start <= distribution_value < distribution_end:

                        return distribution.variant

        return segment.variant

    def match_null(self, op: str, filter_values: List[str]) -> bool:
        """Match null values against filter values."""
        contains_none = self.contains_none(filter_values)

        if op in {
            EvaluationOperator.IS,
            EvaluationOperator.CONTAINS,
            EvaluationOperator.LESS_THAN,
            EvaluationOperator.LESS_THAN_EQUALS,
            EvaluationOperator.GREATER_THAN,
            EvaluationOperator.GREATER_THAN_EQUALS,
            EvaluationOperator.VERSION_LESS_THAN,
            EvaluationOperator.VERSION_LESS_THAN_EQUALS,
            EvaluationOperator.VERSION_GREATER_THAN,
            EvaluationOperator.VERSION_GREATER_THAN_EQUALS,
            EvaluationOperator.SET_IS,
            EvaluationOperator.SET_CONTAINS,
            EvaluationOperator.SET_CONTAINS_ANY,
        }:
            return contains_none
        elif op in {
            EvaluationOperator.IS_NOT,
            EvaluationOperator.DOES_NOT_CONTAIN,
            EvaluationOperator.SET_DOES_NOT_CONTAIN,
            EvaluationOperator.SET_DOES_NOT_CONTAIN_ANY,
        }:
            return not contains_none
        return False

    def match_set(self, prop_values: List[str], op: str, filter_values: List[str]) -> bool:
        """Match set values against filter values."""
        if op == EvaluationOperator.SET_IS:
            return self.set_equals(prop_values, filter_values)
        elif op == EvaluationOperator.SET_IS_NOT:
            return not self.set_equals(prop_values, filter_values)
        elif op == EvaluationOperator.SET_CONTAINS:
            return self.matches_set_contains_all(prop_values, filter_values)
        elif op == EvaluationOperator.SET_DOES_NOT_CONTAIN:
            return not self.matches_set_contains_all(prop_values, filter_values)
        elif op == EvaluationOperator.SET_CONTAINS_ANY:
            return self.matches_set_contains_any(prop_values, filter_values)
        elif op == EvaluationOperator.SET_DOES_NOT_CONTAIN_ANY:
            return not self.matches_set_contains_any(prop_values, filter_values)
        return False

    def match_string(self, prop_value: str, op: str, filter_values: List[str]) -> bool:
        """Match string values against filter values."""
        if op == EvaluationOperator.IS:
            return self.matches_is(prop_value, filter_values)
        elif op == EvaluationOperator.IS_NOT:
            return not self.matches_is(prop_value, filter_values)
        elif op == EvaluationOperator.CONTAINS:
            return self.matches_contains(prop_value, filter_values)
        elif op == EvaluationOperator.DOES_NOT_CONTAIN:
            return not self.matches_contains(prop_value, filter_values)
        elif op in {
            EvaluationOperator.LESS_THAN,
            EvaluationOperator.LESS_THAN_EQUALS,
            EvaluationOperator.GREATER_THAN,
            EvaluationOperator.GREATER_THAN_EQUALS,
        }:
            return self.matches_comparable(
                prop_value,
                op,
                filter_values,
                lambda x: self.parse_number(x),
                self.comparator
            )
        elif op in {
            EvaluationOperator.VERSION_LESS_THAN,
            EvaluationOperator.VERSION_LESS_THAN_EQUALS,
            EvaluationOperator.VERSION_GREATER_THAN,
            EvaluationOperator.VERSION_GREATER_THAN_EQUALS,
        }:
            return self.matches_comparable(
                prop_value,
                op,
                filter_values,
                lambda x: SemanticVersion.parse(x),
                self.version_comparator
            )
        elif op == EvaluationOperator.REGEX_MATCH:
            return self.matches_regex(prop_value, filter_values)
        elif op == EvaluationOperator.REGEX_DOES_NOT_MATCH:
            return not self.matches_regex(prop_value, filter_values)
        return False

    def matches_is(self, prop_value: str, filter_values: List[str]) -> bool:
        """Match exact string values."""
        if self.contains_booleans(filter_values):
            lower = prop_value.lower()
            if lower in ('true', 'false'):
                return any(value.lower() == lower for value in filter_values)
        return any(prop_value == value for value in filter_values)

    def matches_contains(self, prop_value: str, filter_values: List[str]) -> bool:
        """Match substring values."""
        prop_value_lower = prop_value.lower()
        return any(filter_value.lower() in prop_value_lower for filter_value in filter_values)

    def matches_comparable(
            self,
            prop_value: str,
            op: str,
            filter_values: List[str],
            type_transformer: Callable[[str], Any],
            type_comparator: Callable[[Any, str, Any], bool]
    ) -> bool:
        """Match values after transforming them to comparable types."""
        # Transform property value
        transformed_prop = type_transformer(prop_value)

        # Transform and filter out invalid values
        transformed_filters = []
        for filter_val in filter_values:
            transformed = type_transformer(filter_val)
            if transformed is not None:
                transformed_filters.append(transformed)

        # If either transformation failed, fall back to string comparison
        if transformed_prop is None or not transformed_filters:
            return any(self.comparator(prop_value, op, filter_value)
                       for filter_value in filter_values)

        # Compare using transformed values
        return any(type_comparator(transformed_prop, op, filter_value)
                   for filter_value in transformed_filters)

    def comparator(
            self,
            prop_value: Union[str, int],
            op: str,
            filter_value: Union[str, int]
    ) -> bool:
        """Compare values using comparison operators."""
        if op in (EvaluationOperator.LESS_THAN, EvaluationOperator.VERSION_LESS_THAN):
            return prop_value < filter_value
        elif op in (EvaluationOperator.LESS_THAN_EQUALS, EvaluationOperator.VERSION_LESS_THAN_EQUALS):
            return prop_value <= filter_value
        elif op in (EvaluationOperator.GREATER_THAN, EvaluationOperator.VERSION_GREATER_THAN):
            return prop_value > filter_value
        elif op in (EvaluationOperator.GREATER_THAN_EQUALS, EvaluationOperator.VERSION_GREATER_THAN_EQUALS):
            return prop_value >= filter_value
        return False

    def version_comparator(self, prop_value: SemanticVersion, op: str, filter_value: SemanticVersion) -> bool:
        """Compare semantic versions using comparison operators."""
        compare_to = prop_value.compare_to(filter_value)
        if op in (EvaluationOperator.LESS_THAN, EvaluationOperator.VERSION_LESS_THAN):
            return compare_to < 0
        elif op in (EvaluationOperator.LESS_THAN_EQUALS, EvaluationOperator.VERSION_LESS_THAN_EQUALS):
            return compare_to <= 0
        elif op in (EvaluationOperator.GREATER_THAN, EvaluationOperator.VERSION_GREATER_THAN):
            return compare_to > 0
        elif op in (EvaluationOperator.GREATER_THAN_EQUALS, EvaluationOperator.VERSION_GREATER_THAN_EQUALS):
            return compare_to >= 0
        return False

    def matches_regex(self, prop_value: str, filter_values: List[str]) -> bool:
        """Match values using regex patterns."""
        return any(bool(re.search(filter_value, prop_value)) for filter_value in filter_values)

    def contains_none(self, filter_values: List[str]) -> bool:
        """Check if filter values contain '(none)'."""
        return any(filter_value == "(none)" for filter_value in filter_values)

    def contains_booleans(self, filter_values: List[str]) -> bool:
        """Check if filter values contain boolean strings."""
        return any(filter_value.lower() in ('true', 'false') for filter_value in filter_values)

    def parse_number(self, value: str) -> Optional[float]:
        """Parse string to number, return None if invalid."""
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def coerce_string(self, value: Any) -> Optional[str]:
        """Coerce value to string, handling special cases."""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return str(value)

    def coerce_string_array(self, value: Any) -> Optional[List[str]]:
        """Coerce value to string array, handling special cases."""
        if isinstance(value, list):
            return [s for s in map(self.coerce_string, value) if s is not None]

        string_value = str(value)
        try:
            parsed_value = json.loads(string_value)
            if isinstance(parsed_value, list):
                return [s for s in map(self.coerce_string, value) if s is not None]

            s = self.coerce_string(string_value)
            return [s] if s is not None else None
        except json.JSONDecodeError:
            s = self.coerce_string(string_value)
            return [s] if s is not None else None

    def is_set_operator(self, op: str) -> bool:
        """Check if operator is a set operator."""
        return op in {
            EvaluationOperator.SET_IS,
            EvaluationOperator.SET_IS_NOT,
            EvaluationOperator.SET_CONTAINS,
            EvaluationOperator.SET_DOES_NOT_CONTAIN,
            EvaluationOperator.SET_CONTAINS_ANY,
            EvaluationOperator.SET_DOES_NOT_CONTAIN_ANY,
        }

    def set_equals(self, xa: List[str], ya: List[str]) -> bool:
        """Check if two string lists are equal as sets."""
        xs: Set[str] = set(xa)
        ys: Set[str] = set(ya)
        return len(xs) == len(ys) and all(y in xs for y in ys)

    def matches_set_contains_all(self, prop_values: List[str], filter_values: List[str]) -> bool:
        """Check if prop values contain all filter values."""
        if len(prop_values) < len(filter_values):
            return False
        return all(self.matches_is(filter_value, prop_values) for filter_value in filter_values)

    def matches_set_contains_any(self, prop_values: List[str], filter_values: List[str]) -> bool:
        """Check if prop values contain any filter values."""
        return any(self.matches_is(filter_value, prop_values) for filter_value in filter_values)
