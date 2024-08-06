DEFAULT_COHORT_SYNC_URL = 'https://cohort-v2.lab.amplitude.com'
EU_COHORT_SYNC_URL = 'https://cohort-v2.lab.eu.amplitude.com'


class CohortSyncConfig:
    """Experiment Cohort Sync Configuration
    This configuration is used to set up the cohort loader. The cohort loader is responsible for
    downloading cohorts from the server and storing them locally.
        Parameters:
            api_key (str): The project API Key
            secret_key (str): The project Secret Key
            max_cohort_size (int): The maximum cohort size that can be downloaded
            cohort_polling_interval_millis (int): The interval, in milliseconds, at which to poll for
            cohort updates, minimum 60000
            cohort_server_url (str): The server endpoint from which to request cohorts
    """

    def __init__(self, api_key: str, secret_key: str, max_cohort_size: int = 2147483647,
                 cohort_polling_interval_millis: int = 60000, cohort_server_url: str = DEFAULT_COHORT_SYNC_URL):
        self.api_key = api_key
        self.secret_key = secret_key
        self.max_cohort_size = max_cohort_size
        self.cohort_polling_interval_millis = max(cohort_polling_interval_millis, 60000)
        self.cohort_server_url = cohort_server_url
