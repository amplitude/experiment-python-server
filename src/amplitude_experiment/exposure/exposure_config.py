import amplitude


class ExposureConfig(amplitude.Config):
    def __init__(self, cache_capacity: int = 65536, **kw):
        super(ExposureConfig, self).__init__(**kw)
        self.cache_capacity = cache_capacity

