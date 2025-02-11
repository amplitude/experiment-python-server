import base64
import json
from urllib.parse import quote, unquote

from .user import User


class AmplitudeCookie:
    """This class provides utility functions for parsing and handling identity from Amplitude cookies."""

    @staticmethod
    def cookie_name(api_key: str, new_format: bool = False) -> str:
        """
        Get the cookie name that Amplitude sets for the provided
            Parameters:
                api_key (str): The Amplitude API Key
                new_format: (bool): True if the cookie is in the Browser SDK 2.0 format

            Returns:
                The cookie name that Amplitude sets for the provided Amplitude API Key
        """
        if not api_key:
            raise ValueError("Invalid Amplitude API Key")

        if new_format:
            if len(api_key) < 10:
                raise ValueError("Invalid Amplitude API Key")

            return f"AMP_{api_key[:10]}"

        return f"amp_{api_key[0:6]}"

    @staticmethod
    def parse(amplitude_cookie: str, new_format: bool = False) -> User:
        """
        Parse a cookie string and returns user
            Parameters:
                amplitude_cookie (str):  A string from the amplitude cookie
                new_format: (bool): True if the cookie is in the Browser SDK 2.0 format

            Returns:
                Experiment User context containing a device_id and user_id (if available)
        """
        if new_format:
            decoded = base64.b64decode(amplitude_cookie)
            user_session = json.loads(unquote(decoded))
            return User(user_id=user_session.get("userId"), device_id=user_session["deviceId"])

        values = amplitude_cookie.split('.')
        user_id = None
        if values[1]:
            try:
                user_id = base64.b64decode(values[1]).decode("utf-8")
            except:
                user_id = None
        return User(user_id=user_id, device_id=values[0])

    @staticmethod
    def generate(device_id: str, new_format: bool = False) -> str:
        """
        Generates a cookie string to set for the Amplitude Javascript SDK
            Parameters:
                device_id (str):  A device id to set
                new_format: (bool): True if the cookie must be in the Browser SDK 2.0 format

            Returns:
                A cookie string to set for the Amplitude Javascript SDK to read
        """
        if new_format:
            user_session = {"deviceId": device_id}
            user_session_json = json.dumps(user_session, separators=(',', ':'))
            b64encoded = base64.b64encode(quote(user_session_json).encode())
            return b64encoded.decode()

        return f"{device_id}.........."
