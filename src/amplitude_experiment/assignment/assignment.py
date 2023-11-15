import time
from typing import Dict

from .. import Variant
from ..user import User

DAY_MILLIS = 24 * 60 * 60 * 1000


class Assignment:

    def __init__(self, user: User, results: Dict[str, Variant]):
        self.user = user
        self.results = results
        self.timestamp = time.time() * 1000

    def canonicalize(self) -> str:
        user = self.user.user_id.strip() if self.user.user_id else 'None'
        device = self.user.device_id.strip() if self.user.device_id else 'None'
        canonical = user + ' ' + device + ' '
        for flag_key in sorted(self.results):
            value = self.results[flag_key].key.strip() if self.results[flag_key] and self.results[flag_key] and \
                                                                self.results[flag_key].key else 'None'
            canonical += flag_key.strip() + ' ' + value + ' '
        return canonical
