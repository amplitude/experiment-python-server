import time
import logging
import base64
import json
import csv
from io import StringIO
from typing import Set

from .cohort_description import CohortDescription, USER_GROUP_TYPE
from ..connection_pool import HTTPConnectionPool
from ..exception import CachedCohortDownloadException, HTTPErrorResponseException

CDN_COHORT_SYNC_URL = 'https://cohort.lab.amplitude.com'


class CohortDownloadApi:
    def __init__(self):
        self.cdn_server_url = CDN_COHORT_SYNC_URL

    def get_cohort_description(self, cohort_id: str) -> CohortDescription:
        raise NotImplementedError

    def get_cohort_members(self, cohort_description: CohortDescription) -> Set[str]:
        raise NotImplementedError


class DirectCohortDownloadApiV5(CohortDownloadApi):
    def __init__(self, api_key: str, secret_key: str):
        super().__init__()
        self.api_key = api_key
        self.secret_key = secret_key
        self.__setup_connection_pool()
        self.request_status_delay = 2  # seconds, adjust as necessary

    def get_cohort_description(self, cohort_id: str) -> CohortDescription:
        response = self.get_cohort_info(cohort_id)
        cohort_info = json.loads(response.read().decode("utf8"))
        return CohortDescription(
            id=cohort_info['cohort_id'],
            last_computed=cohort_info['last_computed'],
            size=cohort_info['size'],
            group_type=cohort_info['group_type'],
        )

    def get_cohort_info(self, cohort_id: str):
        conn = self._connection_pool.acquire()
        try:
            return conn.request('GET', f'api/3/cohorts/info/{cohort_id}',
                                headers={'Authorization': f'Basic {self._get_basic_auth()}'})
        finally:
            self._connection_pool.release(conn)

    def get_cohort_members(self, cohort_description: CohortDescription) -> Set[str]:
        try:
            logging.debug(f"getCohortMembers({cohort_description.id}): start - {cohort_description}")
            initial_response = self._get_cohort_async_request(cohort_description)
            request_id = json.loads(initial_response.read().decode('utf-8'))['request_id']
            logging.debug(f"getCohortMembers({cohort_description.id}): requestId={request_id}")

            errors = 0
            while True:
                try:
                    status_response = self._get_cohort_async_request_status(request_id)
                    logging.debug(f"getCohortMembers({cohort_description.id}): status={status_response.status}")
                    if status_response.status == 200:
                        break
                    elif status_response.status != 202:
                        raise HTTPErrorResponseException(status_response.status,
                                                         f"Unexpected response code: {status_response.status}")
                except Exception as e:
                    if not isinstance(e, HTTPErrorResponseException) or e.status_code != 429:
                        errors += 1
                    logging.debug(f"getCohortMembers({cohort_description.id}): request-status error {errors} - {e}")
                    if errors >= 3:
                        raise e
                time.sleep(self.request_status_delay)

            location = self._get_cohort_async_request_location(request_id)
            members = self._get_cohort_async_request_members(cohort_description.id, cohort_description.group_type,
                                                             location)
            logging.debug(f"getCohortMembers({cohort_description.id}): end - resultSize={len(members)}")
            return members
        except Exception as e1:
            try:
                cached_members = self._get_cached_cohort_members(cohort_description.id, cohort_description.group_type)
                logging.debug(
                    f"getCohortMembers({cohort_description.id}): end cached fallback - resultSize={len(cached_members)}")
                raise CachedCohortDownloadException(cached_members, e1)
            except Exception as e2:
                raise e2

    def _get_cohort_async_request(self, cohort_description: CohortDescription):
        conn = self._connection_pool.acquire()
        try:
            return conn.request('GET', f'api/5/cohorts/request/{cohort_description.id}',
                                headers={'Authorization': f'Basic {self._get_basic_auth()}'},
                                queries={'lastComputed': str(cohort_description.last_computed)})
        finally:
            self._connection_pool.release(conn)

    def _get_cohort_async_request_status(self, request_id: str):
        conn = self._connection_pool.acquire()
        try:
            return conn.request('GET', f'api/5/cohorts/request-status/{request_id}',
                                headers={'Authorization': f'Basic {self._get_basic_auth()}'})
        finally:
            self._connection_pool.release(conn)

    def _get_cohort_async_request_location(self, request_id: str):
        conn = self._connection_pool.acquire()
        try:
            response = conn.request('GET', f'api/5/cohorts/request-status/{request_id}/file',
                                    headers={'Authorization': f'Basic {self._get_basic_auth()}'})
            location_header = response.headers.get('location')
            if not location_header:
                raise ValueError('Cohort response location must not be null')
            return location_header
        finally:
            self._connection_pool.release(conn)

    def _get_cohort_async_request_members(self, cohort_id: str, group_type: str, location: str) -> Set[str]:
        headers = {
            'X-Amp-Authorization': f'Basic {self._get_basic_auth()}',
            'X-Cohort-ID': cohort_id,
        }
        conn = self._connection_pool.acquire()
        try:
            response = conn.request('GET', location, headers)
            return self._parse_csv_response(response.read(), group_type)
        finally:
            self._connection_pool.release(conn)

    def get_cached_cohort_members(self, cohort_id: str, group_type: str) -> Set[str]:
        headers = {
            'X-Amp-Authorization': f'Basic {self._get_basic_auth()}',
            'X-Cohort-ID': cohort_id,
        }
        conn = self._connection_pool.acquire()
        try:
            response = conn.request('GET', 'cohorts', headers)
            input_stream = response.read()
            if not input_stream:
                raise ValueError('Cohort response body must not be null')
            return self._parse_csv_response(input_stream, group_type)
        finally:
            self._connection_pool.release(conn)

    @staticmethod
    def _parse_csv_response(input_stream: bytes, group_type: str) -> Set[str]:
        csv_file = StringIO(input_stream.decode('utf-8'))
        csv_data = list(csv.DictReader(csv_file))
        if group_type == USER_GROUP_TYPE:
            return {row['user_id'] for row in csv_data if row['user_id']}
        else:
            values = set()
            for row in csv_data:
                try:
                    value = row.get('\tgroup_value', row.get('group_value'))
                    if value:
                        values.add(value.lstrip("\t"))
                except ValueError:
                    pass
            return values

    def _get_basic_auth(self) -> str:
        credentials = f'{self.api_key}:{self.secret_key}'
        return base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

    def __setup_connection_pool(self):
        scheme, _, host = self.cdn_server_url.split('/', 3)
        timeout = 10
        self._connection_pool = HTTPConnectionPool(host, max_size=1, idle_timeout=30, read_timeout=timeout,
                                                   scheme=scheme)
