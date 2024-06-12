class FetchException(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code


class CohortNotModifiedException(Exception):
    def __init__(self, message):
        super().__init__(message)


class CohortTooLargeException(Exception):
    def __init__(self, message):
        super().__init__(message)


class HTTPErrorResponseException(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code
