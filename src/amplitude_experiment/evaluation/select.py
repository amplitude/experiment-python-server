from dataclasses import is_dataclass
from typing import Any, List, Optional
from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class Selectable(Protocol):
    """Protocol for objects that can be selected from using a selector path."""
    def __getitem__(self, key: str) -> Any:
        ...

    def get(self, key: str, default: Any = None) -> Any:
        ...


def selectable(cls):
    """
    Decorator to make dataclasses selectable using dict-like access.
    Must be applied after @dataclass.
    """
    if not is_dataclass(cls):
        raise TypeError("selectable decorator must be used with dataclasses")

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    cls.__getitem__ = __getitem__  # type: ignore
    cls.get = get  # type: ignore
    return cls


def select(selectable: Any, selector: Optional[List[str]]) -> Optional[Any]:
    """Select a value from a nested dictionary or selectable object using a list of keys."""
    if not selector or len(selector) == 0:
        return None

    for selector_element in selector:
        if (not selector_element or
                selectable is None or
                not (isinstance(selectable, dict) or
                     isinstance(selectable, Selectable))):
            return None

        if isinstance(selectable, dict):
            selectable = selectable.get(selector_element)
        else:
            try:
                selectable = selectable.get(selector_element)
            except (AttributeError, KeyError):
                return None

    return None if selectable is None else selectable
