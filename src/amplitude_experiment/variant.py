class Variant:
    """Variant Class"""

    def __init__(self, value: str, payload=None):
        """
        Initialize a Variant
            Parameters:
                value (str): The value of the variant determined by the flag configuration.
                payload (Any): The attached payload, if any.

            Returns:
                Experiment User context containing a device_id and user_id (if available)
        """
        self.value = value
        self.payload = payload

    def __eq__(self, obj) -> bool:
        """
        Determine if current variant equal other variant
            Parameters:
                obj (Variant): The variant to compare with

            Returns:
                True if two variant equals, otherwise False
        """
        return self.value == obj.value and self.payload == obj.payload

    def __str__(self):
        """Return Variant as string"""
        return f"value: {self.value}, payload: {self.payload}"
