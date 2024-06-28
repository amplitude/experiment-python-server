import time
import logging
import base64
import json
from http.client import HTTPResponse
from typing import Optional

from .cohort import Cohort
from ..connection_pool import HTTPConnectionPool
from ..exception import HTTPErrorResponseException, CohortTooLargeException, CohortNotModifiedException


class CohortDownloadApi:

    def get_cohort(self, cohort_id: str, cohort: Optional[Cohort]) -> Cohort:
        raise NotImplementedError


class DirectCohortDownloadApi(CohortDownloadApi):
    def __init__(self, api_key: str, secret_key: str, max_cohort_size: int, cohort_request_delay_millis: int,
                 server_url: str, debug: bool):
        super().__init__()
        self.api_key = api_key
        self.secret_key = secret_key
        self.max_cohort_size = max_cohort_size
        self.cohort_request_delay_millis = cohort_request_delay_millis
        self.logger = logging.getLogger("Amplitude")
        self.logger.addHandler(logging.StreamHandler())
        self.server_url = server_url
        if debug:
            self.logger.setLevel(logging.DEBUG)
        self.__setup_connection_pool()

    def get_cohort(self, cohort_id: str, cohort: Optional[Cohort]) -> Cohort:
        self.logger.debug(f"getCohortMembers({cohort_id}): start")
        errors = 0
        while True:
            response = None
            try:
                last_modified = None if cohort is None else cohort.last_modified
                response = self._get_cohort_members_request(cohort_id, last_modified)
                self.logger.debug(f"getCohortMembers({cohort_id}): status={response.status}")
                if response.status == 200:
                    cohort_info = json.loads(response.read().decode("utf8"))
                    self.logger.debug(f"getCohortMembers({cohort_id}): end - resultSize={cohort_info['size']}")
                    return Cohort(
                        id=cohort_info['cohortId'],
                        last_modified=cohort_info['lastModified'],
                        size=cohort_info['size'],
                        member_ids=set(cohort_info['memberIds']),
                        group_type=cohort_info['groupType'],
                    )
                elif response.status == 204:
                    raise CohortNotModifiedException(f"Cohort not modified: {response.status}")
                elif response.status == 413:
                    raise CohortTooLargeException(f"Cohort exceeds max cohort size: {response.status}")
                elif response.status != 202:
                    raise HTTPErrorResponseException(response.status,
                                                     f"Unexpected response code: {response.status}")
            except Exception as e:
                if response and not isinstance(e, HTTPErrorResponseException) and response.status != 429:
                    errors += 1
                self.logger.debug(f"getCohortMembers({cohort_id}): request-status error {errors} - {e}")
                if errors >= 3 or isinstance(e, CohortNotModifiedException) or isinstance(e, CohortTooLargeException):
                    raise e
            time.sleep(self.cohort_request_delay_millis/1000)

    def _get_cohort_members_request(self, cohort_id: str, last_modified: int) -> HTTPResponse:
        headers = {
            'Authorization': f'Basic {self._get_basic_auth()}',
        }
        conn = self._connection_pool.acquire()
        try:
            url = f'/sdk/v1/cohort/{cohort_id}?maxCohortSize={self.max_cohort_size}'
            if last_modified is not None:
                url += f'&lastModified={last_modified}'
            response = conn.request('GET', url, headers=headers)
            return response
        finally:
            self._connection_pool.release(conn)

    def _get_basic_auth(self) -> str:
        credentials = f'{self.api_key}:{self.secret_key}'
        return base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

    def __setup_connection_pool(self):
        scheme, _, host = self.server_url.split('/', 3)
        timeout = 10
        self._connection_pool = HTTPConnectionPool(host, max_size=10, idle_timeout=30, read_timeout=timeout,
                                                   scheme=scheme)
