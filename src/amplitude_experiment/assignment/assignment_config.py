import amplitude


class AssignmentConfig(amplitude.Config):
    def __init__(self, api_key: str, cache_capacity: int = 65536, **kw):
        self.api_key = api_key
        self.cache_capacity = cache_capacity
        super(AssignmentConfig, self).__init__(**kw)
