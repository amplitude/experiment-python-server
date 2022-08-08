class LocalEvaluationConfig:
    DEFAULT_SERVER_URL = 'https://api.lab.amplitude.com'

    def __init__(self, debug=False,
                 server_url=DEFAULT_SERVER_URL,
                 flag_config_polling_interval_millis=30000,
                 flag_config_poller_request_timeout_millis=10000):
        self.debug = debug
        self.server_url = server_url
        self.flag_config_polling_interval_millis = flag_config_polling_interval_millis
        self.flag_config_poller_request_timeout_millis = flag_config_poller_request_timeout_millis
