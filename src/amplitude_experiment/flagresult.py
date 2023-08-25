class FlagResult:
    def __init__(self, result):
        self.variant = result.get('variant')
        self.description = result.get('description')
        self.is_default_variant = result.get('isDefaultVariant')
        self.exp_key = result.get('exp_key')
        self.deployed = result.get('deployed')
        self.type = result.get('type')
