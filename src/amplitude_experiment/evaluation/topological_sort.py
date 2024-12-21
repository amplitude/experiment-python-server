from typing import Dict, List, Optional

from .types import EvaluationFlag


class CycleException(Exception):
    """
    Raised when topological sorting encounters a cycle between flag dependencies.
    """

    def __init__(self, path: List[str]):
        self.path = path

    def __str__(self):
        return f"Detected a cycle between flags {self.path}"


def topological_sort(
        flags: Dict[str, EvaluationFlag],
        flag_keys: Optional[List[str]] = None
) -> List[EvaluationFlag]:
    """
    Perform a topological sort on feature flags based on their dependencies.
    """
    available: Dict[str, EvaluationFlag] = flags.copy()
    result: List[EvaluationFlag] = []
    starting_keys = flag_keys if flag_keys is not None else list(available.keys())

    for flag_key in starting_keys:
        traversal = _parent_traversal(flag_key, available)
        if traversal:
            result.extend(traversal)

    return result


def _parent_traversal(
        flag_key: str,
        available: Dict[str, EvaluationFlag],
        path: Optional[List[str]] = None
) -> Optional[List[EvaluationFlag]]:
    """
    Recursively traverse flag dependencies to build topologically sorted list.
    """
    if path is None:
        path = []

    flag = available.get(flag_key)
    if not flag:
        return None

    if not flag.dependencies or len(flag.dependencies) == 0:
        available.pop(flag.key)
        return [flag]

    path.append(flag.key)
    result: List[EvaluationFlag] = []

    for parent_key in flag.dependencies:
        if parent_key in path:
            raise CycleException(path)

        traversal = _parent_traversal(parent_key, available, path)
        if traversal:
            result.extend(traversal)

    result.append(flag)
    path.pop()
    available.pop(flag.key)
    return result
