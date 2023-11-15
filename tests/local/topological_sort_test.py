import unittest

from typing import Dict, Any, List

from amplitude_experiment.local.topological_sort import topological_sort, CycleException


class TopologicalSortTestCase(unittest.TestCase):

    def test_empty(self):
        flags = []
        # no flag keys
        result = sort(flags)
        self.assertEqual(result, [])
        # with flag keys
        result = sort(flags, [1])
        self.assertEqual(result, [])

    def test_single_flag_no_dependencies(self):
        flags = [flag(1, [])]
        # no flag keys
        result = sort(flags)
        self.assertEqual(result, flags)
        # with flag keys
        result = sort(flags, [1])
        self.assertEqual(result, flags)
        # with flag keys, no match
        result = sort(flags, [999])
        self.assertEqual(result, [])

    def test_single_flag_with_dependencies(self):
        flags = [flag(1, [2])]
        # no flag keys
        result = sort(flags)
        self.assertEqual(result, flags)
        # with flag keys
        result = sort(flags, [1])
        self.assertEqual(result, flags)
        # with flag keys, no match
        result = sort(flags, [999])
        self.assertEqual(result, [])

    def test_multiple_flags_no_dependencies(self):
        flags = [flag(1, []), flag(2, [])]
        # no flag keys
        result = sort(flags)
        self.assertEqual(result, flags)
        # with flag keys
        result = sort(flags, [1, 2])
        self.assertEqual(result, flags)
        # with flag keys, no match
        result = sort(flags, [99, 999])
        self.assertEqual(result, [])

    def test_multiple_flags_with_dependencies(self):
        flags = [flag(1, [2]), flag(2, [3]), flag(3, [])]
        # no flag keys
        result = sort(flags)
        self.assertEqual(result, [flag(3, []), flag(2, [3]), flag(1, [2])])
        # with flag keys
        result = sort(flags, [1, 2])
        self.assertEqual(result, [flag(3, []), flag(2, [3]), flag(1, [2])])
        # with flag keys, no match
        result = sort(flags, [99, 999])
        self.assertEqual(result, [])

    def test_single_flag_cycle(self):
        flags = [flag(1, [1])]
        # no flag keys
        try:
            sort(flags)
            self.fail('Expected topological sort to fail.')
        except CycleException as e:
            self.assertEqual(e.path, {'1'})
        # with flag keys
        try:
            sort(flags, [1])
            self.fail('Expected topological sort to fail.')
        except CycleException as e:
            self.assertEqual(e.path, {'1'})
        # with flag keys, no match
        try:
            result = sort(flags, [999])
            self.assertEqual(result, [])
        except CycleException as e:
            self.fail(f"Did not expect exception {e}")

    def test_two_flag_cycle(self):
        flags = [flag(1, [2]), flag(2, [1])]
        # no flag keys
        try:
            sort(flags)
            self.fail('Expected topological sort to fail.')
        except CycleException as e:
            self.assertEqual(e.path, {'1', '2'})
        # with flag keys
        try:
            sort(flags, [1, 2])
            self.fail('Expected topological sort to fail.')
        except CycleException as e:
            self.assertEqual(e.path, {'1', '2'})
        # with flag keys, no match
        try:
            result = sort(flags, [999])
            self.assertEqual(result, [])
        except CycleException as e:
            self.fail(f"Did not expect exception {e}")

    def test_multiple_flags_complex_cycle(self):
        flags = [
            flag(3, [1, 2]),
            flag(1, []),
            flag(4, [21, 3]),
            flag(2, []),
            flag(5, [3]),
            flag(6, []),
            flag(7, []),
            flag(8, [9]),
            flag(9, []),
            flag(20, [4]),
            flag(21, [20]),
        ]
        try:
            # use specific ordering
            sort(flags, [3, 1, 4, 2, 5, 6, 7, 8, 9, 20, 21])
        except CycleException as e:
            self.assertEqual({'4', '21', '20'}, e.path)

    def test_multiple_flags_complex_no_cycle_start_at_leaf(self):
        flags = [
            flag(1, [6, 3]),
            flag(2, [8, 5, 3, 1]),
            flag(3, [6, 5]),
            flag(4, [8, 7]),
            flag(5, [10, 7]),
            flag(7, [8]),
            flag(6, [7, 4]),
            flag(8, []),
            flag(9, [10, 7, 5]),
            flag(10, [7]),
            flag(20, []),
            flag(21, [20]),
            flag(30, []),
        ]
        result = sort(flags, [1, 2, 3, 4, 5, 7, 6, 8, 9, 10, 20, 21, 30])
        expected = [
            flag(8, []),
            flag(7, [8]),
            flag(4, [8, 7]),
            flag(6, [7, 4]),
            flag(10, [7]),
            flag(5, [10, 7]),
            flag(3, [6, 5]),
            flag(1, [6, 3]),
            flag(2, [8, 5, 3, 1]),
            flag(9, [10, 7, 5]),
            flag(20, []),
            flag(21, [20]),
            flag(30, []),
        ]
        self.assertEqual(expected, result)

    def test_multiple_flags_complex_no_cycle_start_at_middle(self):
        flags = [
            flag(6, [7, 4]),
            flag(1, [6, 3]),
            flag(2, [8, 5, 3, 1]),
            flag(3, [6, 5]),
            flag(4, [8, 7]),
            flag(5, [10, 7]),
            flag(7, [8]),
            flag(8, []),
            flag(9, [10, 7, 5]),
            flag(10, [7]),
            flag(20, []),
            flag(21, [20]),
            flag(30, []),
        ]
        result = sort(flags, [6, 1, 2, 3, 4, 5, 7, 8, 9, 10, 20, 21, 30])
        expected = [
            flag(8, []),
            flag(7, [8]),
            flag(4, [8, 7]),
            flag(6, [7, 4]),
            flag(10, [7]),
            flag(5, [10, 7]),
            flag(3, [6, 5]),
            flag(1, [6, 3]),
            flag(2, [8, 5, 3, 1]),
            flag(9, [10, 7, 5]),
            flag(20, []),
            flag(21, [20]),
            flag(30, []),
        ]
        self.assertEqual(expected, result)

    def test_multiple_flags_complex_no_cycle_start_at_root(self):
        flags = [
            flag(8, []),
            flag(1, [6, 3]),
            flag(2, [8, 5, 3, 1]),
            flag(3, [6, 5]),
            flag(4, [8, 7]),
            flag(5, [10, 7]),
            flag(6, [7, 4]),
            flag(7, [8]),
            flag(9, [10, 7, 5]),
            flag(10, [7]),
            flag(20, []),
            flag(21, [20]),
            flag(30, []),
        ]
        result = sort(flags, [8, 1, 2, 3, 4, 5, 6, 7, 9, 10, 20, 21, 30])
        expected = [
            flag(8, []),
            flag(7, [8]),
            flag(4, [8, 7]),
            flag(6, [7, 4]),
            flag(10, [7]),
            flag(5, [10, 7]),
            flag(3, [6, 5]),
            flag(1, [6, 3]),
            flag(2, [8, 5, 3, 1]),
            flag(9, [10, 7, 5]),
            flag(20, []),
            flag(21, [20]),
            flag(30, []),
        ]
        self.assertEqual(expected, result)


def sort(flags: List[Dict[str, Any]], flag_keys: List[int] = None) -> List[Dict[str, Any]]:
    flag_key_strings = [str(k) for k in flag_keys] if flag_keys is not None else None
    flags_dict = {f['key']: f for f in flags}
    return topological_sort(flags_dict, flag_key_strings, True)


def flag(key: int, dependencies: List[int]) -> Dict[str, Any]:
    return {'key': str(key), 'dependencies': [str(d) for d in dependencies]}
