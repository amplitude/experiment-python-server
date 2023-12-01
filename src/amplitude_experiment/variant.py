from typing import Dict, Any


class Variant:
    """Variant Class"""

    def __init__(self, value: str = None, payload: Any = None, key: str = None, metadata: Dict[str, Any] = None):
        """
        Initialize a Variant
            Parameters:
                value (str): The value of the variant determined by the flag configuration.
                payload (Any): The attached payload, if any.
                key (str): The variant key.
                metadata (Dict[str, Any]: Additional variant metadata used by the system.

            Returns:
                An experiment variant
        """
        self.value = value
        self.payload = payload
        self.key = key
        self.metadata = metadata

    def __eq__(self, obj) -> bool:
        """
        Determine if current variant equal other variant
            Parameters:
                obj (Variant): The variant to compare with

            Returns:
                True if two variant equals, otherwise False
        """
        if obj is None:
            return False
        return self.key == obj.key and self.value == obj.value and self.payload == obj.payload

    def __str__(self):
        """Return Variant as string"""
        return f"key: {self.key}, value: {self.value}, payload: {self.payload}, metadata:{self.metadata}"
