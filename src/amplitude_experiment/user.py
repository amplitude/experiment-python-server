import json


class User:
    def __init__(self, device_id=None, user_id=None, country=None, city=None, region=None, dma=None,
                 language=None, platform=None, version=None, os=None, device_manufacturer=None, device_brand=None,
                 device_model=None, carrier=None, library=None, user_properties=None):
        self.device_id = device_id
        self.user_id = user_id
        self.country = country
        self.city = city
        self.region = region
        self.dma = dma
        self.language = language
        self.platform = platform
        self.version = version
        self.os = os
        self.device_manufacturer = device_manufacturer
        self.device_brand = device_brand
        self.device_model = device_model
        self.carrier = carrier
        self.library = library
        self.user_properties = user_properties

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)
