import json
import unittest
from unittest.mock import MagicMock
from src.amplitude_experiment.cohort.cohort_description import CohortDescription, USER_GROUP_TYPE
from src.amplitude_experiment.exception import CachedCohortDownloadException
from src.amplitude_experiment.cohort.cohort_download_api import DirectCohortDownloadApiV5
from urllib.parse import urlparse


def response(code: int):
    mock_response = MagicMock()
    mock_response.status = code
    mock_response.headers = {'location': 'https://example.com/cohorts/Cohort_asdf?asdf=asdf#asdf'}
    return mock_response


class CohortDownloadApiTest(unittest.TestCase):
    location = 'https://example.com/cohorts/Cohort_asdf?asdf=asdf#asdf'

    def test_cohort_download_success(self):
        cohort = CohortDescription(id="1234", last_computed=0, size=1)
        async_request_response = MagicMock()
        async_request_response.read.return_value = json.dumps({'cohort_id': '1234', 'request_id': '4321'}).encode()

        async_request_status_response = response(200)
        api = DirectCohortDownloadApiV5('api', 'secret')
        api._get_cohort_async_request = MagicMock(return_value=async_request_response)
        api._get_cohort_async_request_status = MagicMock(return_value=async_request_status_response)
        api._get_cohort_async_request_location = MagicMock(return_value=urlparse(self.location))
        api._get_cohort_async_request_members = MagicMock(return_value={'user'})

        members = api.get_cohort_members(cohort)
        self.assertEqual({'user'}, members)
        api._get_cohort_async_request.assert_called_once_with(cohort)
        api._get_cohort_async_request_status.assert_called_once_with('4321')
        api._get_cohort_async_request_location.assert_called_once_with('4321')
        api._get_cohort_async_request_members.assert_called_once_with('1234', USER_GROUP_TYPE, urlparse(self.location))

    def test_cohort_download_many_202s_success(self):
        cohort = CohortDescription(id="1234", last_computed=0, size=1)
        async_request_response = MagicMock()
        async_request_response.read.return_value = json.dumps({'cohort_id': '1234', 'request_id': '4321'}).encode()

        async_request_status_202_response = response(202)
        async_request_status_200_response = response(200)
        api = DirectCohortDownloadApiV5('api', 'secret')
        api._get_cohort_async_request = MagicMock(return_value=async_request_response)
        api._get_cohort_async_request_status = MagicMock(
            side_effect=[async_request_status_202_response] * 9 + [async_request_status_200_response])
        api._get_cohort_async_request_location = MagicMock(return_value=urlparse(self.location))
        api._get_cohort_async_request_members = MagicMock(return_value={'user'})

        members = api.get_cohort_members(cohort)
        self.assertEqual({'user'}, members)
        api._get_cohort_async_request.assert_called_once_with(cohort)
        self.assertEqual(api._get_cohort_async_request_status.call_count, 10)
        api._get_cohort_async_request_location.assert_called_once_with('4321')
        api._get_cohort_async_request_members.assert_called_once_with('1234', USER_GROUP_TYPE, urlparse(self.location))

    def test_cohort_request_status_with_two_failures_succeeds(self):
        cohort = CohortDescription(id="1234", last_computed=0, size=1)
        async_request_response = MagicMock()
        async_request_response.read.return_value = json.dumps({'cohort_id': '1234', 'request_id': '4321'}).encode()

        async_request_status_503_response = response(503)
        async_request_status_200_response = response(200)
        api = DirectCohortDownloadApiV5('api', 'secret')
        api._get_cohort_async_request = MagicMock(return_value=async_request_response)
        api._get_cohort_async_request_status = MagicMock(
            side_effect=[async_request_status_503_response, async_request_status_503_response,
                         async_request_status_200_response])
        api._get_cohort_async_request_location = MagicMock(return_value=urlparse(self.location))
        api._get_cohort_async_request_members = MagicMock(return_value={'user'})

        members = api.get_cohort_members(cohort)
        self.assertEqual({'user'}, members)
        api._get_cohort_async_request.assert_called_once_with(cohort)
        self.assertEqual(api._get_cohort_async_request_status.call_count, 3)
        api._get_cohort_async_request_location.assert_called_once_with('4321')
        api._get_cohort_async_request_members.assert_called_once_with('1234', USER_GROUP_TYPE, urlparse(self.location))

    def test_cohort_request_status_throws_after_3_failures_cache_fallback_succeeds(self):
        cohort = CohortDescription(id="1234", last_computed=0, size=1)
        async_request_response = MagicMock()
        async_request_response.read.return_value = json.dumps({'cohort_id': '1234', 'request_id': '4321'}).encode()

        async_request_status_response = response(503)
        api = DirectCohortDownloadApiV5('api', 'secret')
        api._get_cohort_async_request = MagicMock(return_value=async_request_response)
        api._get_cohort_async_request_status = MagicMock(return_value=async_request_status_response)
        api._get_cohort_async_request_location = MagicMock(return_value=urlparse(self.location))
        api._get_cohort_async_request_members = MagicMock(return_value={'user'})
        api._get_cached_cohort_members = MagicMock(return_value={'user2'})

        with self.assertRaises(CachedCohortDownloadException) as e:
            api.get_cohort_members(cohort)

        self.assertEqual({'user2'}, e.exception.cached_members)
        api._get_cohort_async_request.assert_called_once_with(cohort)
        self.assertEqual(api._get_cohort_async_request_status.call_count, 3)
        api._get_cohort_async_request_location.assert_not_called()
        api._get_cohort_async_request_members.assert_not_called()
        api._get_cached_cohort_members.assert_called_once_with('1234', USER_GROUP_TYPE)

    def test_cohort_request_status_429s_keep_retrying(self):
        cohort = CohortDescription(id="1234", last_computed=0, size=1)
        async_request_response = MagicMock()
        async_request_response.read.return_value = json.dumps({'cohort_id': '1234', 'request_id': '4321'}).encode()

        async_request_status_429_response = response(429)
        async_request_status_200_response = response(200)
        api = DirectCohortDownloadApiV5('api', 'secret')
        api._get_cohort_async_request = MagicMock(return_value=async_request_response)
        api._get_cohort_async_request_status = MagicMock(
            side_effect=[async_request_status_429_response] * 9 + [async_request_status_200_response])
        api._get_cohort_async_request_location = MagicMock(return_value=urlparse(self.location))
        api._get_cohort_async_request_members = MagicMock(return_value={'user'})

        members = api.get_cohort_members(cohort)
        self.assertEqual({'user'}, members)
        api._get_cohort_async_request.assert_called_once_with(cohort)
        self.assertEqual(api._get_cohort_async_request_status.call_count, 10)
        api._get_cohort_async_request_location.assert_called_once_with('4321')
        api._get_cohort_async_request_members.assert_called_once_with('1234', USER_GROUP_TYPE, urlparse(self.location))

    def test_cohort_async_request_download_failure_falls_back_on_cached_request(self):
        cohort = CohortDescription(id="1234", last_computed=0, size=1)
        api = DirectCohortDownloadApiV5('api', 'secret')
        api._get_cohort_async_request = MagicMock(side_effect=Exception('fail'))
        api._get_cached_cohort_members = MagicMock(return_value={'user'})

        with self.assertRaises(CachedCohortDownloadException) as e:
            api.get_cohort_members(cohort)

        self.assertEqual({'user'}, e.exception.cached_members)
        api._get_cached_cohort_members.assert_called_once_with('1234', USER_GROUP_TYPE)

    def test_group_cohort_download_success(self):
        cohort = CohortDescription(id="1234", last_computed=0, size=1, group_type="org name")
        async_request_response = MagicMock()
        async_request_response.read.return_value = json.dumps({'cohort_id': '1234', 'request_id': '4321'}).encode()

        async_request_status_response = response(200)
        api = DirectCohortDownloadApiV5('api', 'secret')
        api._get_cohort_async_request = MagicMock(return_value=async_request_response)
        api._get_cohort_async_request_status = MagicMock(return_value=async_request_status_response)
        api._get_cohort_async_request_location = MagicMock(return_value=urlparse(self.location))
        api._get_cohort_async_request_members = MagicMock(return_value={'group'})

        members = api.get_cohort_members(cohort)
        self.assertEqual({'group'}, members)
        api._get_cohort_async_request.assert_called_once_with(cohort)
        api._get_cohort_async_request_status.assert_called_once_with('4321')
        api._get_cohort_async_request_location.assert_called_once_with('4321')
        api._get_cohort_async_request_members.assert_called_once_with('1234', 'org name', urlparse(self.location))

    def test_group_cohort_request_status_429s_keep_retrying(self):
        cohort = CohortDescription(id="1234", last_computed=0, size=1, group_type="org name")
        async_request_response = MagicMock()
        async_request_response.read.return_value = json.dumps({'cohort_id': '1234', 'request_id': '4321'}).encode()

        async_request_status_429_response = response(429)
        async_request_status_200_response = response(200)
        api = DirectCohortDownloadApiV5('api', 'secret')
        api._get_cohort_async_request = MagicMock(return_value=async_request_response)
        api._get_cohort_async_request_status = MagicMock(
            side_effect=[async_request_status_429_response] * 9 + [async_request_status_200_response])
        api._get_cohort_async_request_location = MagicMock(return_value=urlparse(self.location))
        api._get_cohort_async_request_members = MagicMock(return_value={'group'})

        members = api.get_cohort_members(cohort)
        self.assertEqual({'group'}, members)
        api._get_cohort_async_request.assert_called_once_with(cohort)
        self.assertEqual(api._get_cohort_async_request_status.call_count, 10)
        api._get_cohort_async_request_location.assert_called_once_with('4321')
        api._get_cohort_async_request_members.assert_called_once_with('1234', 'org name', urlparse(self.location))


if __name__ == '__main__':
    unittest.main()
