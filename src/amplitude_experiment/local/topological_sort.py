from typing import Dict, Set, Any, List, Optional


class CycleException(Exception):
    """
    Raised when topological sorting encounters a cycle between flag dependencies.
    """

    def __init__(self, path: Set[str]):
        self.path = path

    def __str__(self):
        return f"Detected a cycle between flags {self.path}"


def topological_sort(
        flags: Dict[str, Dict[str, Any]],
        keys: List[str] = None,
        ordered: bool = False
) -> List[Dict[str, Any]]:
    available = flags.copy()
    result = []
    starting_keys = keys if keys is not None and len(keys) > 0 else list(flags.keys())
    # Used for testing to ensure consistency.
    if ordered and (keys is None or len(keys) == 0):
        starting_keys.sort()
    for flag_key in starting_keys:
        traversal = __parent_traversal(flag_key, available, set())
        if traversal is not None:
            result.extend(traversal)
    return result


def __parent_traversal(
        flag_key: str,
        available: Dict[str, Dict[str, Any]],
        path: Set[str]
) -> Optional[List[Dict[str, Any]]]:
    flag = available.get(flag_key)
    if flag is None:
        return None
    dependencies = flag.get('dependencies')
    if dependencies is None or len(dependencies) == 0:
        available.pop(flag_key)
        return [flag]
    path.add(flag_key)
    result = []
    for parent_key in dependencies:
        if parent_key in path:
            raise CycleException(path)
        traversal = __parent_traversal(parent_key, available, path)
        if traversal is not None:
            result.extend(traversal)
    result.append(flag)
    path.remove(flag_key)
    available.pop(flag_key)
    return result
