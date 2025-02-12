import json
import logging
import urllib.parse

from .user import User
import base64


class AmplitudeCookie:
    """This class provides utility functions for parsing and handling identity from Amplitude cookies."""

    @staticmethod
    def cookie_name(api_key: str, new_format: bool = False) -> str:
        """
        Get the cookie name that Amplitude sets for the provided
            Parameters:
                api_key (str): The Amplitude API Key
                new_format (bool): True if cookie is in Browser SDK 2.0 format

            Returns:
                The cookie name that Amplitude sets for the provided Amplitude API Key
       """
        if not api_key:
            raise ValueError("Invalid Amplitude API Key")

        if new_format:
            if len(api_key) < 10:
                raise ValueError("Invalid Amplitude API Key")
            return f"AMP_{api_key[0:10]}"

        if len(api_key) < 6:
            raise ValueError("Invalid Amplitude API Key")
        return f"amp_{api_key[0:6]}"

    @staticmethod
    def parse(amplitude_cookie: str, new_format: bool = False) -> User:
        """
        Parse a cookie string and returns user
            Parameters:
                amplitude_cookie (str):  A string from the amplitude cookie
                new_format: True if cookie is in Browser SDK 2.0 format

            Returns:
                Experiment User context containing a device_id and user_id (if available)
        """

        if new_format:
            decoding = base64.b64decode(amplitude_cookie).decode("utf-8")
            try:
                user_session = json.loads(urllib.parse.unquote_plus(decoding))
                if "userId" not in user_session:
                    return User(user_id=None, device_id=user_session["deviceId"])
                return User(user_id=user_session["userId"], device_id=user_session["deviceId"])
            except Exception as e:
                logger = logging.getLogger("Amplitude")
                logger.error("Error parsing the Amplitude cookie: " + str(e))
                return User()

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
                new_format: True if cookie is in Browser SDK 2.0 format

            Returns:
                A cookie string to set for the Amplitude Javascript SDK to read
        """
        if not new_format:
            return f"{device_id}.........."

        user_session_hash = {
            "deviceId": device_id
        }
        json_data = json.dumps(user_session_hash)
        encoded_json = urllib.parse.quote(json_data)
        base64_encoded = base64.b64encode(bytearray(encoded_json, "utf-8")).decode("utf-8")

        return base64_encoded
