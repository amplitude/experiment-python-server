from .user import User
import base64


class AmplitudeCookie:
    """This class provides utility functions for parsing and handling identity from Amplitude cookies."""

    @staticmethod
    def cookie_name(api_key: str) -> str:
        """
        Get the cookie name that Amplitude sets for the provided
            Parameters:
                api_key (str): The Amplitude API Key

            Returns:
                The cookie name that Amplitude sets for the provided Amplitude API Key
       """
        if not api_key:
            raise ValueError("Invalid Amplitude API Key")
        return f"amp_{api_key[0:6]}"

    @staticmethod
    def parse(amplitude_cookie: str) -> User:
        """
        Parse a cookie string and returns user
            Parameters:
                amplitude_cookie (str):  A string from the amplitude cookie

            Returns:
                Experiment User context containing a device_id and user_id (if available)
        """
        values = amplitude_cookie.split('.')
        user_id = None
        if values[1]:
            try:
                user_id = base64.b64decode(values[1]).decode("utf-8")
            except:
                user_id = None
        return User(user_id=user_id, device_id=values[0])

    @staticmethod
    def generate(device_id: str) -> str:
        """
        Generates a cookie string to set for the Amplitude Javascript SDK
            Parameters:
                device_id (str):  A device id to set

            Returns:
                A cookie string to set for the Amplitude Javascript SDK to read
        """
        return f"{device_id}.........."
