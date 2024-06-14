from typing import Dict, Callable
from threading import Lock


class FlagConfigStorage:
    def get_flag_config(self, key: str) -> Dict:
        raise NotImplementedError

    def get_flag_configs(self) -> Dict:
        raise NotImplementedError

    def put_flag_config(self, flag_config: Dict):
        raise NotImplementedError

    def remove_if(self, condition: Callable[[Dict], bool]):
        raise NotImplementedError


class InMemoryFlagConfigStorage(FlagConfigStorage):
    def __init__(self):
        self.flag_configs = {}
        self.flag_configs_lock = Lock()

    def get_flag_config(self, key: str) -> Dict:
        with self.flag_configs_lock:
            return self.flag_configs.get(key)

    def get_flag_configs(self) -> Dict[str, Dict]:
        with self.flag_configs_lock:
            return self.flag_configs.copy()

    def put_flag_config(self, flag_config: Dict):
        with self.flag_configs_lock:
            self.flag_configs[flag_config['key']] = flag_config

    def remove_if(self, condition: Callable[[Dict], bool]):
        with self.flag_configs_lock:
            self.flag_configs = {key: value for key, value in self.flag_configs.items() if not condition(value)}
