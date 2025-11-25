import amplitude


class AssignmentConfig(amplitude.Config):
    """
    @deprecated Assignment tracking is deprecated. Use ExposureConfig with ExposureService instead.
    """
    def __init__(self, cache_capacity: int = 65536, send_evaluated_props: bool = False, **kw):
        super(AssignmentConfig, self).__init__(**kw)
        self.cache_capacity = cache_capacity
        self.send_evaluated_props = send_evaluated_props
