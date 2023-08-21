class FlagResult:
    def __init__(self, value: str, is_default_variant: bool, payload: str = None, exp_key: str = None,
                 deployed: bool = None, type: str = None):
        self.value = value
        self.payload = payload
        self.is_default_variant = is_default_variant
        self.exp_key = exp_key
        self.deployed = deployed
        self.type = type
