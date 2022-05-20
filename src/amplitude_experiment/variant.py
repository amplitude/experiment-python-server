class Variant:

    def __init__(self, value, payload):
        self.value = value
        self.payload = payload

    def __eq__(self, obj):
        return self.value == obj.value and self.payload == obj.payload
