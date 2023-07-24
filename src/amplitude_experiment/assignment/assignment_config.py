import amplitude


class AssignmentConfig(amplitude.Config):
    def __init__(self, filter_capacity: int = 65536, **kw):
        self.filter_capacity = filter_capacity
        super(AssignmentConfig, self).__init__(**kw)
