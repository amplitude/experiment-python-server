class FetchException(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code


class CachedCohortDownloadException(Exception):
    def __init__(self, cached_members, message):
        super().__init__(message)
        self.cached_members = cached_members


class HTTPErrorResponseException(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code
