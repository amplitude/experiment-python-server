import time
from src.amplitude_experiment.util import Cache

from src.amplitude_experiment.assignment import Assignment


class MockAssignmentFilter:
    def __init__(self, size: int, ttl_millis: int):
        self.cache = Cache(size, ttl_millis)

    def should_track(self, assignment: Assignment) -> bool:
        canonical_assignment = assignment.canonicalize()
        print(canonical_assignment)
        track = self.cache.get(canonical_assignment) is None
        if track:
            self.cache.put(canonical_assignment, object())
        return track
