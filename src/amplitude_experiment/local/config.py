from enum import Enum

from ..assignment import AssignmentConfig
from ..cohort.cohort_sync_config import CohortSyncConfig, DEFAULT_COHORT_SYNC_URL, EU_COHORT_SYNC_URL

DEFAULT_SERVER_URL = 'https://api.lab.amplitude.com'
EU_SERVER_URL = 'https://flag.lab.eu.amplitude.com'


class ServerZone(Enum):
    US = "US"
    EU = "EU"


class LocalEvaluationConfig:
    """Experiment Local Client Configuration"""

    def __init__(self, debug: bool = False,
                 server_url: str = DEFAULT_SERVER_URL,
                 server_zone: ServerZone = ServerZone.US,
                 flag_config_polling_interval_millis: int = 30000,
                 flag_config_poller_request_timeout_millis: int = 10000,
                 assignment_config: AssignmentConfig = None,
                 cohort_sync_config: CohortSyncConfig = None):
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
                assignment_config (AssignmentConfig): The assignment configuration.
                cohort_sync_config (CohortSyncConfig): The cohort sync configuration.

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

        self.flag_config_polling_interval_millis = flag_config_polling_interval_millis
        self.flag_config_poller_request_timeout_millis = flag_config_poller_request_timeout_millis
        self.assignment_config = assignment_config
