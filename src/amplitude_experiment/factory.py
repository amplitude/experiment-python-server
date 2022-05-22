from .client import Client, Config

instances = {}
default_instance = '$default_instance'


class Experiment:
    """Provides factory methods for storing singleton instance of Client"""

    @staticmethod
    def initialize(api_key: str, config: Config = None) -> Client:
        """
        Initializes a singleton Client. This method returns a default singleton instance, subsequent calls to
        init will return the initial instance regardless of input.
            Parameters:
                api_key (str): The Amplitude API Key
                config (Config): Optional Config

            Returns:
                Experiment Client
        """
        if instances.get(default_instance) is None:
            instances[default_instance] = Client(api_key, config)
        return instances[default_instance]
