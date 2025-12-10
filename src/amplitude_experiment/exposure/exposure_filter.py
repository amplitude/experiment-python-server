from .exposure import Exposure
from .exposure import DAY_MILLIS
from ..util.cache import Cache


class ExposureFilter:
    def __init__(self, size: int, ttl_millis: int = DAY_MILLIS):
        self.cache = Cache(size, ttl_millis)
        self.ttl_millis = ttl_millis

    def should_track(self, exposure: Exposure) -> bool:
        """
        Determines if an exposure should be tracked based on the dedupe filter.
        """
        if not exposure.results:
            # Don't track empty exposures.
            return False
        canonical_exposure = exposure.canonicalize()
        track = self.cache.get(canonical_exposure) is None
        if track:
            self.cache.put(canonical_exposure, object())
        return track

