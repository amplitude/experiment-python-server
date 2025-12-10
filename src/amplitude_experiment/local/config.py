import logging
import sys

from ..assignment import AssignmentConfig
from ..exposure import ExposureConfig
from ..cohort.cohort_sync_config import CohortSyncConfig, DEFAULT_COHORT_SYNC_URL, EU_COHORT_SYNC_URL
from ..server_zone import ServerZone

DEFAULT_SERVER_URL = 'https://api.lab.amplitude.com'
EU_SERVER_URL = 'https://flag.lab.eu.amplitude.com'

DEFAULT_STREAM_URL = 'https://stream.lab.amplitude.com'
EU_STREAM_SERVER_URL = 'https://stream.lab.eu.amplitude.com'


class LocalEvaluationConfig:
    """Experiment Local Client Configuration"""

    def __init__(self, debug: bool = False,
                 server_url: str = DEFAULT_SERVER_URL,
                 server_zone: ServerZone = ServerZone.US,
                 flag_config_polling_interval_millis: int = 30000,
                 flag_config_poller_request_timeout_millis: int = 10000,
                 stream_updates: bool = False,
                 stream_server_url: str = DEFAULT_STREAM_URL,
                 stream_flag_conn_timeout: int = 1500,
                 assignment_config: AssignmentConfig = None,
                 exposure_config: ExposureConfig = None,
                 cohort_sync_config: CohortSyncConfig = None,
                 logger: logging.Logger = None):
        """
        Initialize a config
           Parameters:
                debug (bool): Set to true to log some extra information to the console.
                server_url (str): The server endpoint from which to request flag configs.
                server_zone (ServerZone): Location of the Amplitude data center to get flags and cohorts from, US or EU
                flag_config_polling_interval_millis (int): The interval, in milliseconds, at which to poll for flag
                  configurations.
                flag_config_poller_request_timeout_millis (int): The request timeout, in milliseconds, used when
                  fetching flag configurations.
                assignment_config (AssignmentConfig): The assignment configuration. @deprecated use exposure_config instead.
                exposure_config (ExposureConfig): The exposure configuration.
                cohort_sync_config (CohortSyncConfig): The cohort sync configuration.
                logger (logging.Logger): Optional logger instance. If provided, this logger will be used instead of
                  creating a new one. The debug flag only applies when no logger is provided.

           Returns:
               The config object
        """
        self.debug = debug
        self.server_url = server_url
        self.server_zone = server_zone
        self.cohort_sync_config = cohort_sync_config
        if server_url == DEFAULT_SERVER_URL and server_zone == ServerZone.EU:
            self.server_url = EU_SERVER_URL
            if (cohort_sync_config is not None and
                    cohort_sync_config.cohort_server_url == DEFAULT_COHORT_SYNC_URL):
                self.cohort_sync_config.cohort_server_url = EU_COHORT_SYNC_URL

        self.stream_server_url = stream_server_url
        if stream_server_url == DEFAULT_SERVER_URL and server_zone == ServerZone.EU:
            self.stream_server_url = EU_STREAM_SERVER_URL

        self.flag_config_polling_interval_millis = flag_config_polling_interval_millis
        self.flag_config_poller_request_timeout_millis = flag_config_poller_request_timeout_millis
        self.stream_updates = stream_updates
        self.stream_flag_conn_timeout = stream_flag_conn_timeout
        self.assignment_config = assignment_config
        self.exposure_config = exposure_config
        # Set up logger: use provided logger or create default one
        if logger is None:
            self.logger = logging.getLogger("Amplitude")
            # Only add handler if logger doesn't already have one
            if not self.logger.handlers:
                handler = logging.StreamHandler(sys.stderr)
                self.logger.addHandler(handler)
            # Set log level: DEBUG if debug=True, otherwise WARNING
            # Only apply debug flag to default logger, not user-provided loggers
            log_level = logging.DEBUG if self.debug else logging.WARNING
            self.logger.setLevel(log_level)
        else:
            self.logger = logger
