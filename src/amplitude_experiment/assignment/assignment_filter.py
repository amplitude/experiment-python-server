import time

from .assignment import Assignment
from .assignment import DAY_MILLIS
from ..util.cache import Cache


class AssignmentFilter:
    def __init__(self, size: int):
        self.cache = Cache(size, DAY_MILLIS)

    def should_track(self, assignment: Assignment) -> bool:
        now = time.time()
        canonical_assignment = assignment.canonicalize()
        track = self.cache.get(canonical_assignment) is None
        if track:
            self.cache.put(canonical_assignment, object())
        return track
