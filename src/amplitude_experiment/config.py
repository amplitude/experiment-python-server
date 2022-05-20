class Config:
    DEFAULT_SERVER_URL = 'https://api.lab.amplitude.com'

    def __init__(self, debug=False,
                 server_url=DEFAULT_SERVER_URL,
                 fetch_timeout_millis=10000,
                 fetch_retries=0,
                 fetch_retry_backoff_min_millis=500,
                 fetch_retry_backoff_max_millis=10000,
                 fetch_retry_backoff_scalar=1.5,
                 fetch_retry_timeout_millis=10000):
        self.debug = debug
        self.server_url = server_url
        self.fetch_timeout_millis = fetch_timeout_millis
        self.fetch_retries = fetch_retries
        self.fetch_retry_backoff_min_millis = fetch_retry_backoff_min_millis
        self.fetch_retry_backoff_max_millis = fetch_retry_backoff_max_millis
        self.fetch_retry_backoff_scalar = fetch_retry_backoff_scalar
        self.fetch_retry_timeout_millis = fetch_retry_timeout_millis
