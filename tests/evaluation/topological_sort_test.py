import unittest
from typing import Dict, List, Optional

from src.amplitude_experiment.evaluation.types import EvaluationFlag
from src.amplitude_experiment.evaluation.topological_sort import topological_sort, CycleException


class TopologicalSortTestCase(unittest.TestCase):
    def test_empty(self):
        # No flag keys
        flags: Dict[str, EvaluationFlag] = {}
        result = topological_sort(flags)
        self.assertEqual(result, [])

        # With flag keys
        flags = {}
        result = topological_sort(flags, ["1"])
        self.assertEqual(result, [])

    def test_single_flag_no_dependencies(self):
        # No flag keys
        flags = {self._create_flag(1).key: self._create_flag(1)}
        result = topological_sort(flags)
        self.assertEqual(result, [self._create_flag(1)])

        # With flag keys
        flags = {self._create_flag(1).key: self._create_flag(1)}
        result = topological_sort(flags, ["1"])
        self.assertEqual(result, [self._create_flag(1)])

        # With flag keys, no match
        flags = {self._create_flag(1).key: self._create_flag(1)}
        result = topological_sort(flags, ["999"])
        self.assertEqual(result, [])

    def test_single_flag_with_dependencies(self):
        # No flag keys
        flags = {self._create_flag(1, [2]).key: self._create_flag(1, [2])}
        result = topological_sort(flags)
        self.assertEqual(result, [self._create_flag(1, [2])])

        # With flag keys
        flags = {self._create_flag(1, [2]).key: self._create_flag(1, [2])}
        result = topological_sort(flags, ["1"])
        self.assertEqual(result, [self._create_flag(1, [2])])

        # With flag keys, no match
        flags = {self._create_flag(1, [2]).key: self._create_flag(1, [2])}
        result = topological_sort(flags, ["999"])
        self.assertEqual(result, [])

    def test_multiple_flags_no_dependencies(self):
        # No flag keys
        flags = {
            f.key: f for f in [self._create_flag(1), self._create_flag(2)]
        }
        result = topological_sort(flags)
        self.assertEqual(
            result,
            [self._create_flag(1), self._create_flag(2)]
        )

        # With flag keys
        flags = {
            f.key: f for f in [self._create_flag(1), self._create_flag(2)]
        }
        result = topological_sort(flags, ["1", "2"])
        self.assertEqual(
            result,
            [self._create_flag(1), self._create_flag(2)]
        )

        # With flag keys, no match
        flags = {
            f.key: f for f in [self._create_flag(1), self._create_flag(2)]
        }
        result = topological_sort(flags, ["99", "999"])
        self.assertEqual(result, [])

    def test_multiple_flags_with_dependencies(self):
        # No flag keys
        flags = {
            f.key: f for f in [
                self._create_flag(1, [2]),
                self._create_flag(2, [3]),
                self._create_flag(3)
            ]
        }
        result = topological_sort(flags)
        self.assertEqual(
            result,
            [
                self._create_flag(3),
                self._create_flag(2, [3]),
                self._create_flag(1, [2])
            ]
        )

        # With flag keys
        flags = {
            f.key: f for f in [
                self._create_flag(1, [2]),
                self._create_flag(2, [3]),
                self._create_flag(3)
            ]
        }
        result = topological_sort(flags, ["1", "2"])
        self.assertEqual(
            result,
            [
                self._create_flag(3),
                self._create_flag(2, [3]),
                self._create_flag(1, [2])
            ]
        )

        # With flag keys, no match
        flags = {
            f.key: f for f in [
                self._create_flag(1, [2]),
                self._create_flag(2, [3]),
                self._create_flag(3)
            ]
        }
        result = topological_sort(flags, ["99", "999"])
        self.assertEqual(result, [])

    def test_single_flag_cycle(self):
        # No flag keys
        flags = {self._create_flag(1, [1]).key: self._create_flag(1, [1])}
        with self.assertRaisesRegex(CycleException, "Detected a cycle between flags \\['1'\\]"):
            topological_sort(flags)

        # With flag keys
        flags = {self._create_flag(1, [1]).key: self._create_flag(1, [1])}
        with self.assertRaisesRegex(CycleException, "Detected a cycle between flags \\['1'\\]"):
            topological_sort(flags, ["1"])

        # With flag keys, no match
        flags = {self._create_flag(1, [1]).key: self._create_flag(1, [1])}
        result = topological_sort(flags, ["999"])
        self.assertEqual(result, [])

    def test_two_flag_cycle(self):
        # No flag keys
        flags = {
            f.key: f for f in [
                self._create_flag(1, [2]),
                self._create_flag(2, [1])
            ]
        }
        with self.assertRaisesRegex(CycleException, "Detected a cycle between flags \\['1', '2'\\]"):
            topological_sort(flags)

        # With flag keys
        flags = {
            f.key: f for f in [
                self._create_flag(1, [2]),
                self._create_flag(2, [1])
            ]
        }
        with self.assertRaisesRegex(CycleException, "Detected a cycle between flags \\['2', '1'\\]"):
            topological_sort(flags, ["2"])

        # With flag keys, no match
        flags = {
            f.key: f for f in [
                self._create_flag(1, [2]),
                self._create_flag(2, [1])
            ]
        }
        result = topological_sort(flags, ["999"])
        self.assertEqual(result, [])

    def test_multiple_flags_complex_cycle(self):
        flags = {
            f.key: f for f in [
                self._create_flag(3, [1, 2]),
                self._create_flag(1),
                self._create_flag(4, [21, 3]),
                self._create_flag(2),
                self._create_flag(5, [3]),
                self._create_flag(6),
                self._create_flag(7),
                self._create_flag(8, [9]),
                self._create_flag(9),
                self._create_flag(20, [4]),
                self._create_flag(21, [20])
            ]
        }
        with self.assertRaisesRegex(CycleException, "Detected a cycle between flags \\['4', '21', '20'\\]"):
            topological_sort(flags)

    def test_complex_no_cycle_starting_with_leaf(self):
        flags = {
            f.key: f for f in [
                self._create_flag(1, [6, 3]),
                self._create_flag(2, [8, 5, 3, 1]),
                self._create_flag(3, [6, 5]),
                self._create_flag(4, [8, 7]),
                self._create_flag(5, [10, 7]),
                self._create_flag(7, [8]),
                self._create_flag(6, [7, 4]),
                self._create_flag(8),
                self._create_flag(9, [10, 7, 5]),
                self._create_flag(10, [7]),
                self._create_flag(20),
                self._create_flag(21, [20]),
                self._create_flag(30)
            ]
        }
        result = topological_sort(flags)
        self.assertEqual(
            result,
            [
                self._create_flag(8),
                self._create_flag(7, [8]),
                self._create_flag(4, [8, 7]),
                self._create_flag(6, [7, 4]),
                self._create_flag(10, [7]),
                self._create_flag(5, [10, 7]),
                self._create_flag(3, [6, 5]),
                self._create_flag(1, [6, 3]),
                self._create_flag(2, [8, 5, 3, 1]),
                self._create_flag(9, [10, 7, 5]),
                self._create_flag(20),
                self._create_flag(21, [20]),
                self._create_flag(30)
            ]
        )

    @staticmethod
    def _create_flag(key: int, dependencies: Optional[List[int]] = None) -> EvaluationFlag:
        """Helper method to create a flag with given key and dependencies."""
        return EvaluationFlag(
            key=str(key),
            variants={},
            segments=[],
            dependencies=[str(d) for d in dependencies] if dependencies else None
        )


if __name__ == '__main__':
    unittest.main()
