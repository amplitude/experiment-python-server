import time
from typing import Dict

from ..flagresult import FlagResult
from ..user import User

DAY_MILLIS = 24 * 60 * 60 * 1000


class Assignment:

    def __init__(self, user: User, results: Dict[str, FlagResult]):
        self.user = user
        self.results = results
        self.timestamp = time.time()

    def canonicalize(self) -> str:
        user = self.user.user_id.strip() if self.user.user_id else 'undefined'
        device = self.user.device_id.strip() if self.user.device_id else 'undefined'
        canonical = user + ' ' + device + ' '
        for key in sorted(self.results):
            value = self.results[key].value.strip() if self.results[key] else 'undefined'
            canonical += key.strip() + ' ' + value + ' '
        return canonical
