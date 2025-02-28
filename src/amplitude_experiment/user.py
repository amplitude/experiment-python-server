import json

from typing import Dict, Any, Set, List


class User:
    """
    Defines a user context for evaluation. `device_id` and `user_id` are used for identity resolution.
    All other predefined fields and user properties are used for rule based user targeting.
    """

    def __init__(
            self,
            device_id: str = None,
            user_id: str = None,
            country: str = None,
            city: str = None,
            region: str = None,
            dma: str = None,
            language: str = None,
            platform: str = None,
            version: str = None,
            os: str = None,
            device_manufacturer: str = None,
            device_brand: str = None,
            device_model: str = None,
            carrier: str = None,
            library: str = None,
            ip_address: str = None,
            user_properties: Dict[str, Any] = None,
            groups: Dict[str, List[str]] = None,
            group_properties: Dict[str, Dict[str, Dict[str, Any]]] = None,
            group_cohort_ids: Dict[str, Dict[str, List[str]]] = None,
            cohort_ids: List[str] = None
    ):
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
                ip_address (str): Predefined field, must be manually provided
                user_properties (dict): Custom user properties
                groups (dict): Groups associated with the user
                group_properties (dict): Properties for groups

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
        self.ip_address = ip_address
        self.user_properties = user_properties
        self.groups = groups
        self.group_properties = group_properties
        self.group_cohort_ids = group_cohort_ids
        self.cohort_ids = cohort_ids

    def to_json(self):
        """Return user information as JSON string."""
        return json.dumps(self, default=lambda o: o.__dict__)

    def __str__(self):
        """Return user as string"""
        return self.to_json()

    def add_group_cohort_ids(self, group_type: str, group_name: str, cohort_ids: List[str]) -> None:
        """
        Add cohort IDs for a group.
        Parameters:
            group_type (str): The type of the group
            group_name (str): The name of the group
            cohort_ids (Set[str]): Set of cohort IDs associated with the group
        """
        if self.group_cohort_ids is None:
            self.group_cohort_ids = {}

        group_names = self.group_cohort_ids.setdefault(group_type, {})
        group_names[group_name] = cohort_ids
