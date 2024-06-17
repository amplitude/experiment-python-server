class CohortSyncConfig:
    def __init__(self, api_key: str, secret_key: str, max_cohort_size: int = 15000,
                 cohort_request_delay_millis: int = 5000):
        self.api_key = api_key
        self.secret_key = secret_key
        self.max_cohort_size = max_cohort_size
        self.cohort_request_delay_millis = cohort_request_delay_millis
