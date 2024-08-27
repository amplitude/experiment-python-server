class FetchException(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code


class CohortTooLargeException(Exception):
    def __init__(self, message):
        super().__init__(message)


class HTTPErrorResponseException(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code


class CohortsDownloadException(Exception):
    def __init__(self, errors):
        self.errors = errors
        super().__init__(self.__str__())

    def __str__(self):
        error_messages = []
        for item in self.errors:
            if isinstance(item, tuple) and len(item) == 2:
                cohort_id, error = item
                error_messages.append(f"Cohort {cohort_id}: {error}")
            else:
                error_messages.append(str(item))
        return f"One or more cohorts failed to update:\n" + "\n".join(error_messages)
