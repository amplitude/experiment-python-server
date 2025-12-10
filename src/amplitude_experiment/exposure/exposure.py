import time
from typing import Dict

from .. import Variant
from ..user import User

DAY_MILLIS = 24 * 60 * 60 * 1000


class Exposure:
    """
    Exposure is a class that represents a user's exposure to a set of flags.
    """

    def __init__(self, user: User, results: Dict[str, Variant]):
        self.user = user
        self.results = results
        self.timestamp = time.time() * 1000

    def canonicalize(self) -> str:
        user = self.user.user_id.strip() if self.user.user_id else 'None'
        device = self.user.device_id.strip() if self.user.device_id else 'None'
        canonical = user + ' ' + device + ' '
        for flag_key in sorted(self.results):
            variant = self.results[flag_key]
            if variant.key is None:
                continue
            value = self.results[flag_key].key.strip()
            canonical += flag_key.strip() + ' ' + value + ' '
        return canonical

