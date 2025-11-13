from .assignment import Assignment
from .assignment import DAY_MILLIS
from ..util.cache import Cache


class AssignmentFilter:
    """
    @deprecated Assignment tracking is deprecated. Use ExposureFilter with ExposureService instead.
    """
    def __init__(self, size: int, ttl_millis: int = DAY_MILLIS):
        self.cache = Cache(size, ttl_millis)

    def should_track(self, assignment: Assignment) -> bool:
        if not assignment.results:
            return False
        canonical_assignment = assignment.canonicalize()
        track = self.cache.get(canonical_assignment) is None
        if track:
            self.cache.put(canonical_assignment, object())
        return track
