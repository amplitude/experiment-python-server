from typing import Dict, Callable
from threading import Lock

from ..evaluation.types import EvaluationFlag


class FlagConfigStorage:
    def get_flag_config(self, key: str) -> EvaluationFlag:
        raise NotImplementedError

    def get_flag_configs(self) -> Dict[str, EvaluationFlag]:
        raise NotImplementedError

    def put_flag_config(self, flag_config: EvaluationFlag):
        raise NotImplementedError

    def remove_if(self, condition: Callable[[EvaluationFlag], bool]):
        raise NotImplementedError


class InMemoryFlagConfigStorage(FlagConfigStorage):
    def __init__(self):
        self.flag_configs = {}
        self.flag_configs_lock = Lock()

    def get_flag_config(self, key: str) -> EvaluationFlag:
        with self.flag_configs_lock:
            return self.flag_configs.get(key)

    def get_flag_configs(self) -> Dict[str, EvaluationFlag]:
        with self.flag_configs_lock:
            return self.flag_configs.copy()

    def put_flag_config(self, flag_config: EvaluationFlag):
        with self.flag_configs_lock:
            self.flag_configs[flag_config.key] = flag_config

    def remove_if(self, condition: Callable[[EvaluationFlag], bool]):
        with self.flag_configs_lock:
            self.flag_configs = {key: value for key, value in self.flag_configs.items() if not condition(value)}
