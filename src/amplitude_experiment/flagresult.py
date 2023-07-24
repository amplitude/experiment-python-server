class FlagResult:
    def __init__(self, value: str, is_default_variant: bool, payload: str = None, expkey: str = None,
                 deployed: bool = None, type: str = None):
        self.value = value
        self.payload = payload
        self.is_default_variant = is_default_variant
        self.expkey = expkey
        self.deployed = deployed
        self.type = type
