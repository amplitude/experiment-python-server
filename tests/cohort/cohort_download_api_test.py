import json
import unittest
from unittest.mock import MagicMock, patch
from src.amplitude_experiment.cohort.cohort_description import CohortDescription
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
        self.api = DirectCohortDownloadApi('api', 'secret', 15000, False, 100)

    def test_cohort_download_success(self):
        cohort = CohortDescription(id="1234", last_computed=0, size=1, group_type='user')
        cohort_info_response = response(200, {'cohortId': '1234', 'lastComputed': 0, 'size': 1, 'groupType': 'user'})
        members_response = response(200, {'memberIds': ['user']})

        with patch.object(self.api, 'get_cohort_info', return_value=cohort_info_response), \
                patch.object(self.api, '_get_cohort_members_request', return_value=members_response):

            members = self.api.get_cohort_members(cohort)
            self.assertEqual({'user'}, members)

    def test_cohort_download_many_202s_success(self):
        cohort = CohortDescription(id="1234", last_computed=0, size=1, group_type='user')
        cohort_info_response = response(200, {'cohortId': '1234', 'lastComputed': 0, 'size': 1, 'groupType': 'user'})
        members_response = response(200, {'memberIds': ['user']})
        async_responses = [response(202)] * 9 + [members_response]

        with patch.object(self.api, 'get_cohort_info', return_value=cohort_info_response), \
                patch.object(self.api, '_get_cohort_members_request', side_effect=async_responses):

            members = self.api.get_cohort_members(cohort)
            self.assertEqual({'user'}, members)

    def test_cohort_request_status_with_two_failures_succeeds(self):
        cohort = CohortDescription(id="1234", last_computed=0, size=1, group_type='user')
        cohort_info_response = response(200, {'cohortId': '1234', 'lastComputed': 0, 'size': 1, 'groupType': 'user'})
        error_response = response(503)
        members_response = response(200, {'memberIds': ['user']})
        async_responses = [error_response, error_response, members_response]

        with patch.object(self.api, 'get_cohort_info', return_value=cohort_info_response), \
                patch.object(self.api, '_get_cohort_members_request', side_effect=async_responses):

            members = self.api.get_cohort_members(cohort)
            self.assertEqual({'user'}, members)

    def test_cohort_request_status_429s_keep_retrying(self):
        cohort = CohortDescription(id="1234", last_computed=0, size=1, group_type='user')
        cohort_info_response = response(200, {'cohortId': '1234', 'lastComputed': 0, 'size': 1, 'groupType': 'user'})
        error_response = response(429)
        members_response = response(200, {'memberIds': ['user']})
        async_responses = [error_response] * 9 + [members_response]

        with patch.object(self.api, 'get_cohort_info', return_value=cohort_info_response), \
                patch.object(self.api, '_get_cohort_members_request', side_effect=async_responses):

            members = self.api.get_cohort_members(cohort)
            self.assertEqual({'user'}, members)

    def test_group_cohort_download_success(self):
        cohort = CohortDescription(id="1234", last_computed=0, size=1, group_type="org name")
        cohort_info_response = response(200, {'cohortId': '1234', 'lastComputed': 0, 'size': 1, 'groupType': "org name"})
        members_response = response(200, {'memberIds': ['group']})

        with patch.object(self.api, 'get_cohort_info', return_value=cohort_info_response), \
                patch.object(self.api, '_get_cohort_members_request', return_value=members_response):

            members = self.api.get_cohort_members(cohort)
            self.assertEqual({'group'}, members)

    def test_group_cohort_request_status_429s_keep_retrying(self):
        cohort = CohortDescription(id="1234", last_computed=0, size=1, group_type="org name")
        cohort_info_response = response(200, {'cohortId': '1234', 'lastComputed': 0, 'size': 1, 'groupType': "org name"})
        error_response = response(429)
        members_response = response(200, {'memberIds': ['group']})
        async_responses = [error_response] * 9 + [members_response]

        with patch.object(self.api, 'get_cohort_info', return_value=cohort_info_response), \
                patch.object(self.api, '_get_cohort_members_request', side_effect=async_responses):

            members = self.api.get_cohort_members(cohort)
            self.assertEqual({'group'}, members)

    def test_cohort_size_too_large(self):
        cohort = CohortDescription(id="1234", last_computed=0, size=16000, group_type='user')
        cohort_info_response = response(200, {'cohortId': '1234', 'lastComputed': 0, 'size': 16000, 'groupType': 'user'})
        too_large_response = response(413)

        with patch.object(self.api, 'get_cohort_info', return_value=cohort_info_response), \
                patch.object(self.api, '_get_cohort_members_request', return_value=too_large_response):

            with self.assertRaises(CohortTooLargeException):
                self.api.get_cohort_members(cohort)

    def test_cohort_not_modified_exception(self):
        cohort = CohortDescription(id="1234", last_computed=1000, size=1, group_type='user')
        cohort_info_response = response(200, {'cohortId': '1234', 'lastComputed': 1000, 'size': 1, 'groupType': 'user'})
        not_modified_response = response(204)

        with patch.object(self.api, 'get_cohort_info', return_value=cohort_info_response), \
                patch.object(self.api, '_get_cohort_members_request', return_value=not_modified_response):

            with self.assertRaises(CohortNotModifiedException):
                self.api.get_cohort_members(cohort, should_download_cohort=False)


if __name__ == '__main__':
    unittest.main()
