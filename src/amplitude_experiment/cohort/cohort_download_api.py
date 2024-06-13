import time
import logging
import base64
import json
from http.client import HTTPResponse
from typing import Set

from .cohort_description import CohortDescription
from ..connection_pool import HTTPConnectionPool
from ..exception import HTTPErrorResponseException, CohortTooLargeException, CohortNotModifiedException

CDN_COHORT_SYNC_URL = 'https://cohort-v2.lab.amplitude.com'


class CohortDownloadApi:
    def __init__(self):
        self.cdn_server_url = CDN_COHORT_SYNC_URL

    def get_cohort_description(self, cohort_id: str) -> CohortDescription:
        raise NotImplementedError

    def get_cohort_members(self, cohort_description: CohortDescription, last_modified: int) -> Set[str]:
        raise NotImplementedError


class DirectCohortDownloadApi(CohortDownloadApi):
    def __init__(self, api_key: str, secret_key: str, max_cohort_size: int = 15000,
                 debug: bool = False, cohort_request_delay_millis: int = 5000):
        super().__init__()
        self.api_key = api_key
        self.secret_key = secret_key
        self.max_cohort_size = max_cohort_size
        self.__setup_connection_pool()
        self.cohort_request_delay_millis = cohort_request_delay_millis
        self.logger = logging.getLogger("Amplitude")
        self.logger.addHandler(logging.StreamHandler())
        if debug:
            self.logger.setLevel(logging.DEBUG)

    def get_cohort_description(self, cohort_id: str) -> CohortDescription:
        response = self.get_cohort_info(cohort_id)
        cohort_info = json.loads(response.read().decode("utf-8"))
        return CohortDescription(
            id=cohort_info['cohortId'],
            last_computed=cohort_info['lastComputed'],
            size=cohort_info['size'],
            group_type=cohort_info['groupType'],
        )

    def get_cohort_info(self, cohort_id: str) -> HTTPResponse:
        conn = self._connection_pool.acquire()
        try:
            return conn.request('GET', f'/sdk/v1/cohort/{cohort_id}?skipCohortDownload=true',
                                headers={'Authorization': f'Basic {self._get_basic_auth()}'})
        finally:
            self._connection_pool.release(conn)

    def get_cohort_members(self, cohort_description: CohortDescription, should_download_cohort: bool = False) -> Set[str]:
        self.logger.debug(f"getCohortMembers({cohort_description.id}): start - {cohort_description}")
        errors = 0
        while True:
            response = None
            try:
                last_modified = -1 if should_download_cohort else cohort_description.last_computed
                response = self._get_cohort_members_request(cohort_description.id, last_modified)
                self.logger.debug(f"getCohortMembers({cohort_description.id}): status={response.status}")
                if response.status == 200:
                    response_json = json.loads(response.read().decode("utf8"))
                    members = set(response_json['memberIds'])
                    self.logger.debug(f"getCohortMembers({cohort_description.id}): end - resultSize={len(members)}")
                    return members
                elif response.status == 204:
                    raise CohortNotModifiedException(f"Cohort not modified: {response.status}")
                elif response.status == 413:
                    raise CohortTooLargeException(f"Cohort exceeds max cohort size: {response.status}")
                elif response.status != 202:
                    raise HTTPErrorResponseException(response.status,
                                                     f"Unexpected response code: {response.status}")
            except Exception as e:
                if not isinstance(e, HTTPErrorResponseException) and response.status != 429:
                    errors += 1
                self.logger.debug(f"getCohortMembers({cohort_description.id}): request-status error {errors} - {e}")
                if errors >= 3 or isinstance(e, CohortTooLargeException):
                    raise e
            time.sleep(self.cohort_request_delay_millis/1000)

    def _get_cohort_members_request(self, cohort_id: str, last_modified: int) -> HTTPResponse:
        headers = {
            'Authorization': f'Basic {self._get_basic_auth()}',
        }
        conn = self._connection_pool.acquire()
        try:
            response = conn.request('GET', f'/sdk/v1/cohort/{cohort_id}?maxCohortSize={self.max_cohort_size}'
                                           f'&lastModified={last_modified}',
                                    headers=headers)
            return response
        finally:
            self._connection_pool.release(conn)

    def _get_basic_auth(self) -> str:
        credentials = f'{self.api_key}:{self.secret_key}'
        return base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

    def __setup_connection_pool(self):
        scheme, _, host = self.cdn_server_url.split('/', 3)
        timeout = 10
        self._connection_pool = HTTPConnectionPool(host, max_size=10, idle_timeout=30, read_timeout=timeout,
                                                   scheme=scheme)