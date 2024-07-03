import json
import logging
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch
from src.amplitude_experiment.cohort.cohort import Cohort
from src.amplitude_experiment.cohort.cohort_download_api import DirectCohortDownloadApi
from src.amplitude_experiment.exception import CohortTooLargeException, CohortNotModifiedException


def response(code: int, body: dict = None):
    mock_response = MagicMock()
    mock_response.status = code
    if body is not None:
        mock_response.read.return_value = json.dumps(body).encode()
    return mock_response


class CohortDownloadApiTest(unittest.TestCase):

    def setUp(self):
        self.api = DirectCohortDownloadApi('api', 'secret', 15000, 100, "https://example.amplitude.com", mock.create_autospec(logging.Logger))

    def test_cohort_download_success(self):
        cohort = Cohort(id="1234", last_modified=0, size=1, member_ids={'user'})
        cohort_info_response = Cohort(id="1234", last_modified=0, size=1, member_ids={'user'})

        with patch.object(self.api, 'get_cohort', return_value=cohort_info_response):

            result_cohort = self.api.get_cohort("1234", cohort)
            self.assertEqual(cohort, result_cohort)

    def test_cohort_download_many_202s_success(self):
        cohort = Cohort(id="1234", last_modified=0, size=1, member_ids={'user'})
        async_responses = [response(202)] * 9 + [response(200, {'cohortId': '1234', 'lastModified': 0, 'size': 1, 'groupType': 'User', 'memberIds': ['user']})]

        with patch.object(self.api, '_get_cohort_members_request', side_effect=async_responses):

            result_cohort = self.api.get_cohort("1234", cohort)
            self.assertEqual(cohort, result_cohort)

    def test_cohort_request_status_with_two_failures_succeeds(self):
        cohort = Cohort(id="1234", last_modified=0, size=1, member_ids={'user'})
        error_response = response(503)
        success_response = response(200, {'cohortId': '1234', 'lastModified': 0, 'size': 1, 'groupType': 'User', 'memberIds': ['user']})
        async_responses = [error_response, error_response, success_response]

        with patch.object(self.api, '_get_cohort_members_request', side_effect=async_responses):

            result_cohort = self.api.get_cohort("1234", cohort)
            self.assertEqual(cohort, result_cohort)

    def test_cohort_request_status_429s_keep_retrying(self):
        cohort = Cohort(id="1234", last_modified=0, size=1, member_ids={'user'})
        error_response = response(429)
        success_response = response(200, {'cohortId': '1234', 'lastModified': 0, 'size': 1, 'groupType': 'User', 'memberIds': ['user']})
        async_responses = [error_response] * 9 + [success_response]

        with patch.object(self.api, '_get_cohort_members_request', side_effect=async_responses):

            result_cohort = self.api.get_cohort("1234", cohort)
            self.assertEqual(cohort, result_cohort)

    def test_group_cohort_download_success(self):
        cohort = Cohort(id="1234", last_modified=0, size=1, member_ids={'group'}, group_type="org name")
        cohort_info_response = Cohort(id="1234", last_modified=0, size=1, member_ids={'group'}, group_type="org name")

        with patch.object(self.api, 'get_cohort', return_value=cohort_info_response):

            result_cohort = self.api.get_cohort("1234", cohort)
            self.assertEqual(cohort, result_cohort)

    def test_group_cohort_request_status_429s_keep_retrying(self):
        cohort = Cohort(id="1234", last_modified=0, size=1, member_ids={'group'}, group_type="org name")
        error_response = response(429)
        success_response = response(200, {'cohortId': '1234', 'lastModified': 0, 'size': 1, 'groupType': 'org name', 'memberIds': ['group']})
        async_responses = [error_response] * 9 + [success_response]

        with patch.object(self.api, '_get_cohort_members_request', side_effect=async_responses):

            result_cohort = self.api.get_cohort("1234", cohort)
            self.assertEqual(cohort, result_cohort)

    def test_cohort_size_too_large(self):
        cohort = Cohort(id="1234", last_modified=0, size=16000, member_ids=set())
        too_large_response = response(413)

        with patch.object(self.api, '_get_cohort_members_request', return_value=too_large_response):

            with self.assertRaises(CohortTooLargeException):
                self.api.get_cohort("1234", cohort)

    def test_cohort_not_modified_exception(self):
        cohort = Cohort(id="1234", last_modified=1000, size=1, member_ids=set())
        not_modified_response = response(204)

        with patch.object(self.api, '_get_cohort_members_request', return_value=not_modified_response):

            with self.assertRaises(CohortNotModifiedException):
                self.api.get_cohort("1234", cohort)


if __name__ == '__main__':
    unittest.main()
