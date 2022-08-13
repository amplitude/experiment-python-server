class LocalEvaluationConfig:
    """Experiment Local Client Configuration"""

    DEFAULT_SERVER_URL = 'https://api.lab.amplitude.com'

    def __init__(self, debug: bool = False,
                 server_url: str = DEFAULT_SERVER_URL,
                 flag_config_polling_interval_millis: int = 30000,
                 flag_config_poller_request_timeout_millis: int = 10000):
        """
        Initialize a config
           Parameters:
               debug (bool): Set to true to log some extra information to the console.
               server_url (str): The server endpoint from which to request variants.
               flag_config_polling_interval_millis (int): The interval in milliseconds to poll the amplitude server for
                   flag config updates. These rules are stored in memory and used when calling evaluate()
                   to perform local evaluation.
               flag_config_poller_request_timeout_millis (int): The request timeout, in milliseconds,
                   used when fetching variants.

           Returns:
               The config object
        """
        self.debug = debug
        self.server_url = server_url
        self.flag_config_polling_interval_millis = flag_config_polling_interval_millis
        self.flag_config_poller_request_timeout_millis = flag_config_poller_request_timeout_millis
