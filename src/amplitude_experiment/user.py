import json


class User:
    """
    Defines a user context for evaluation. `device_id` and `user_id` are used for identity resolution.
    All other predefined fields and user properties are used for rule based user targeting.
    """
    def __init__(self, device_id=None, user_id=None, country=None, city=None, region=None, dma=None,
                 language=None, platform=None, version=None, os=None, device_manufacturer=None, device_brand=None,
                 device_model=None, carrier=None, library=None, user_properties=None):
        """
        Initialize User instance
            Parameters:
                device_id (str): Device ID for associating with an identity in Amplitude
                user_id (str): User ID for associating with an identity in Amplitude
                country (str): Predefined field, must be manually provided
                city (str): Predefined field, must be manually provided
                region (str): Predefined field, must be manually provided
                dma (str): Predefined field, must be manually provided
                language (str): Predefined field, must be manually provided
                platform (str): Predefined field, must be manually provided
                version (str): Predefined field, must be manually provided
                os (str): Predefined field, must be manually provided
                device_manufacturer (str): Predefined field, must be manually provided
                device_brand (str): Predefined field, must be manually provided
                device_model (str): Predefined field, must be manually provided
                carrier (str): Predefined field, must be manually provided
                library (str): Predefined field, must be manually provided
                user_properties (dict): Custom user properties

            Returns:
                User object
        """
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
        """Return user information as JSON string."""
        return json.dumps(self, default=lambda o: o.__dict__)

    def __str__(self):
        """Return user as string"""
        return self.to_json()
