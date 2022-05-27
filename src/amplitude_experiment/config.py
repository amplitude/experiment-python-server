class Config:
    """Experiment Client Configuration"""

    DEFAULT_SERVER_URL = 'https://api.lab.amplitude.com'

    def __init__(self, debug=False,
                 server_url=DEFAULT_SERVER_URL,
                 fetch_timeout_millis=10000,
                 fetch_retries=0,
                 fetch_retry_backoff_min_millis=500,
                 fetch_retry_backoff_max_millis=10000,
                 fetch_retry_backoff_scalar=1.5,
                 fetch_retry_timeout_millis=10000):
        """
        Initialize a config
            Parameters:
                debug (bool): Set to true to log some extra information to the console.
                server_url (str): The server endpoint from which to request variants.
                fetch_timeout_millis (int): The request timeout, in milliseconds, used when fetching variants
                  triggered by calling start() or setUser().
                fetch_retries (int): The number of retries to attempt before failing.
                fetch_retry_backoff_min_millis (int): Retry backoff minimum (starting backoff delay) in milliseconds.
                  The minimum backoff is scaled by `fetch_retry_backoff_scalar` after each retry failure.
                fetch_retry_backoff_max_millis (int): Retry backoff maximum in milliseconds. If the scaled backoff is
                  greater than the max, the max is used for all subsequent retries.
                fetch_retry_backoff_scalar (float): Scales the minimum backoff exponentially.
                fetch_retry_timeout_millis (int): The request timeout for retrying fetch requests.

            Returns:
                The config object
        """
        self.debug = debug
        self.server_url = server_url
        self.fetch_timeout_millis = fetch_timeout_millis
        self.fetch_retries = fetch_retries
        self.fetch_retry_backoff_min_millis = fetch_retry_backoff_min_millis
        self.fetch_retry_backoff_max_millis = fetch_retry_backoff_max_millis
        self.fetch_retry_backoff_scalar = fetch_retry_backoff_scalar
        self.fetch_retry_timeout_millis = fetch_retry_timeout_millis
