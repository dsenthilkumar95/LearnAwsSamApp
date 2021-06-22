import unittest
import logging
import lambda_functions.revoke_from_other_flows.revoking as lambda_to_test
from tests.mocks.ds_mocks import all_publish_profile_ids
from tests.mocks.ds_mocks import workflow_results_all_processed
from tests.mocks.ds_mocks import workflow_results_previously_revoked
import os
from unittest.mock import Mock, patch
from requests.exceptions import HTTPError

"""
Tests for lambda
"""


class Session:
    def __init__(self, status=200, content=None, json_data=None, raise_for_status=None):
        self.auth = None
        self.status = status
        self.content = content
        self.json_data = json_data
        self.raise_for_status = raise_for_status

    def get(self, url, params):
        return self._mock_response(self.status, self.content, self.json_data, self.raise_for_status)

    @staticmethod
    def _mock_response(
            status=200,
            content="CONTENT",
            json_data=None,
            raise_for_status=None):

        mock_resp = Mock()
        # mock raise_for_status call w/optional error
        mock_resp.raise_for_status = Mock()
        if raise_for_status:
            mock_resp.raise_for_status.side_effect = raise_for_status
        # set status code and content
        mock_resp.status_code = status
        mock_resp.content = content
        # add json data if provided
        if json_data:
            mock_resp.json = Mock(
                return_value=json_data
            )
        return mock_resp


class mpxAuth:
    def __init__(self):
        self.auth = None

    def init(self, data):
        self.auth = data


class TestRevokeFromOtherFlows(unittest.TestCase):
    """
    Base TestCase class
    """

    @classmethod
    def setUpClass(cls):
        logging.debug("")
        # Test config ends
        logging.basicConfig(level='DEBUG')
        logging.getLogger().setLevel('DEBUG')
        cls.logger = logging.getLogger('RevokeFromOtherProfileTestCase')

    @patch('lambda_functions.revoke_from_other_flows.revoking.filter_input_notifications')
    @patch('lambda_functions.revoke_from_other_flows.revoking.authentication.mpxAuth')
    def test_lambda_handler_should_exit_filter_none(self, mock_auth, mock_filter_input_notifications):
        mock_auth.return_value = mpxAuth()
        mock_filter_input_notifications.return_value = None
        context = ""
        event = {'Records': [
            {
                'EventSource': 'aws:sns', 'EventVersion': '1.0',
                'EventSubscriptionArn': 'arn:aws:sns:eu-west-2:701984544886:ocs-dev-profile-result-ntfy:504b7e1b-a37b-42a7-a326-011f797b4e37',
                'Sns':
                    {
                        'Type': 'Notification', 'MessageId': 'e8be3c54-a89f-51ba-bc82-6b13f1e81732',
                        'TopicArn': 'arn:aws:sns:eu-west-2:701984544886:ocs-dev-profile-result-ntfy',
                        'Subject': None,
                        'Message': '{"id":679325754,"method":"put","entry":{"mediaId":"http://data.media.theplatform.eu/media/data/Media/495654469171","profileId":"http://data.publish.theplatform.eu/publish/data/PublishProfile/5115263","batchIds":[],"status":"Processed","ownerId":"http://access.auth.theplatform.com/data/Account/2703231863","updatedByUserId":"https://identity.auth.theplatform.com/idm/data/User/mpx/2745985","id":"http://data.workflow.theplatform.eu/workflow/data/ProfileResult/1040314828580","guid":"fkd8cDbwnf8ssK6TWponWT4RixEg3hgn","updated":1590515509000,"nullFields":[{"namespace":"http://xml.theplatform.com/workflow/data/ProfileResult","name":"sharedMediaId"}]},"oldEntry":{"status":"Processing","nullFields":[]},"objectType":"ProfileResult","cid":"a6b76f68-e12b-4f88-be62-e58ac08bb4fc"}',
                        'Timestamp': '2020-05-26T17:51:51.752Z', 'SignatureVersion': '1',
                        'Signature': 'gO88bzMI0x7Zthafypj2yezO0CqULnMLR9TACQ9snNC2JlkoyXRuxZWN5M57eKQpEN7oOpQ3Pvg3Z/Ilgt9azCCYeg34E0+j4IEsq2th4aMrsxOZm3L3ZSSvfJjgHLhaitqH2vViY9YEgCoen5OEPiJmEWSNpD3/mwnc/gH/U9LeJXHTtGxr57mnGBbGIs3fWlnsh9OnbKFEntgcH+B9Xt7LstegvDNt47Q4Uan61FfXGZWT1oePAsi8YTkzN0/2jUWvVaKbqHqI6/5zWSlucKIJNyTp6PkcHkdnGFCN2d5DQPL6pMsEzrMYR0FN2ZPp8phJHIPkuf29C+tai2PyBw==',
                        'SigningCertUrl': 'https://sns.eu-west-2.amazonaws.com/SimpleNotificationService-a86cb10b4e1f29c941702d737128f7b6.pem',
                        'UnsubscribeUrl': 'https://sns.eu-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:eu-west-2:701984544886:ocs-dev-profile-result-ntfy:504b7e1b-a37b-42a7-a326-011f797b4e37',
                        'MessageAttributes': {
                            'method': {'Type': 'String', 'Value': 'put'},
                            'id': {'Type': 'String', 'Value': '679325754'},
                            'objectType': {'Type': 'String',
                                           'Value': 'ProfileResult'}
                        }
                    }
            }
        ]}
        result = lambda_to_test.lambda_handler(event, context)
        self.assertEqual(result, None)

    @patch('lambda_functions.revoke_from_other_flows.revoking.filter_input_notifications')
    @patch('lambda_functions.revoke_from_other_flows.revoking.authentication.mpxAuth')
    def test_lambda_handler_should_exit_no_message(self, mock_auth, mock_filter_input_notifications):
        mock_auth.return_value = mpxAuth()
        mock_filter_input_notifications.return_value = None
        context = ""
        event = {'Records': [
            {
                'EventSource': 'aws:sns', 'EventVersion': '1.0',
                'EventSubscriptionArn': 'arn:aws:sns:eu-west-2:701984544886:ocs-dev-profile-result-ntfy:504b7e1b-a37b-42a7-a326-011f797b4e37',
                'Sns':
                    {
                        'Type': 'Notification', 'MessageId': 'e8be3c54-a89f-51ba-bc82-6b13f1e81732',
                        'TopicArn': 'arn:aws:sns:eu-west-2:701984544886:ocs-dev-profile-result-ntfy',
                        'Subject': None,
                        'Message': '',
                        'Timestamp': '2020-05-26T17:51:51.752Z', 'SignatureVersion': '1',
                        'Signature': 'gO88bzMI0x7Zthafypj2yezO0CqULnMLR9TACQ9snNC2JlkoyXRuxZWN5M57eKQpEN7oOpQ3Pvg3Z/Ilgt9azCCYeg34E0+j4IEsq2th4aMrsxOZm3L3ZSSvfJjgHLhaitqH2vViY9YEgCoen5OEPiJmEWSNpD3/mwnc/gH/U9LeJXHTtGxr57mnGBbGIs3fWlnsh9OnbKFEntgcH+B9Xt7LstegvDNt47Q4Uan61FfXGZWT1oePAsi8YTkzN0/2jUWvVaKbqHqI6/5zWSlucKIJNyTp6PkcHkdnGFCN2d5DQPL6pMsEzrMYR0FN2ZPp8phJHIPkuf29C+tai2PyBw==',
                        'SigningCertUrl': 'https://sns.eu-west-2.amazonaws.com/SimpleNotificationService-a86cb10b4e1f29c941702d737128f7b6.pem',
                        'UnsubscribeUrl': 'https://sns.eu-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:eu-west-2:701984544886:ocs-dev-profile-result-ntfy:504b7e1b-a37b-42a7-a326-011f797b4e37',
                        'MessageAttributes': {
                            'method': {'Type': 'String', 'Value': 'put'},
                            'id': {'Type': 'String', 'Value': '679325754'},
                            'objectType': {'Type': 'String',
                                           'Value': 'ProfileResult'}
                        }
                    }
            }
        ]}
        result = lambda_to_test.lambda_handler(event, context)
        self.assertEqual(result, None)

    @patch('lambda_functions.revoke_from_other_flows.revoking.get_profile_id_from_guid')
    @patch('lambda_functions.revoke_from_other_flows.revoking.authentication.mpxAuth')
    def test_lambda_handler_should_exit_wrong_profile(self, mock_auth, mock_get_profile_id_from_guid):
        mock_auth.return_value = mpxAuth()
        mock_get_profile_id_from_guid.return_value = [
            {"id": "http://data.publish.theplatform.eu/publish/data/PublishProfile/123400"}
        ]
        context = ""
        event = {'Records': [
            {
                'EventSource': 'aws:sns', 'EventVersion': '1.0',
                'EventSubscriptionArn': 'arn:aws:sns:eu-west-2:701984544886:ocs-dev-profile-result-ntfy:504b7e1b-a37b-42a7-a326-011f797b4e37',
                'Sns':
                    {
                        'Type': 'Notification', 'MessageId': 'e8be3c54-a89f-51ba-bc82-6b13f1e81732',
                        'TopicArn': 'arn:aws:sns:eu-west-2:701984544886:ocs-dev-profile-result-ntfy',
                        'Subject': None,
                        'Message': '{"id":679325754,"method":"put","entry":{"mediaId":"http://data.media.theplatform.eu/media/data/Media/495654469171","profileId":"http://data.publish.theplatform.eu/publish/data/PublishProfile/123456","batchIds":[],"status":"Processed","ownerId":"http://access.auth.theplatform.com/data/Account/2703231863","updatedByUserId":"https://identity.auth.theplatform.com/idm/data/User/mpx/2745985","id":"http://data.workflow.theplatform.eu/workflow/data/ProfileResult/1040314828580","guid":"fkd8cDbwnf8ssK6TWponWT4RixEg3hgn","updated":1590515509000,"nullFields":[{"namespace":"http://xml.theplatform.com/workflow/data/ProfileResult","name":"sharedMediaId"}]},"oldEntry":{"status":"Processing","nullFields":[]},"objectType":"ProfileResult","cid":"a6b76f68-e12b-4f88-be62-e58ac08bb4fc"}',
                        'Timestamp': '2020-05-26T17:51:51.752Z', 'SignatureVersion': '1',
                        'Signature': 'gO88bzMI0x7Zthafypj2yezO0CqULnMLR9TACQ9snNC2JlkoyXRuxZWN5M57eKQpEN7oOpQ3Pvg3Z/Ilgt9azCCYeg34E0+j4IEsq2th4aMrsxOZm3L3ZSSvfJjgHLhaitqH2vViY9YEgCoen5OEPiJmEWSNpD3/mwnc/gH/U9LeJXHTtGxr57mnGBbGIs3fWlnsh9OnbKFEntgcH+B9Xt7LstegvDNt47Q4Uan61FfXGZWT1oePAsi8YTkzN0/2jUWvVaKbqHqI6/5zWSlucKIJNyTp6PkcHkdnGFCN2d5DQPL6pMsEzrMYR0FN2ZPp8phJHIPkuf29C+tai2PyBw==',
                        'SigningCertUrl': 'https://sns.eu-west-2.amazonaws.com/SimpleNotificationService-a86cb10b4e1f29c941702d737128f7b6.pem',
                        'UnsubscribeUrl': 'https://sns.eu-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:eu-west-2:701984544886:ocs-dev-profile-result-ntfy:504b7e1b-a37b-42a7-a326-011f797b4e37',
                        'MessageAttributes': {
                            'method': {'Type': 'String', 'Value': 'put'},
                            'id': {'Type': 'String', 'Value': '679325754'},
                            'objectType': {'Type': 'String',
                                           'Value': 'ProfileResult'}
                        }
                    }
            }
        ]}
        result = lambda_to_test.lambda_handler(event, context)
        self.assertEqual(result, None)

    @patch('lambda_functions.revoke_from_other_flows.revoking.get_all_workflow_profile_ids')
    def test_filter_medias_published_in_different_flow(self, mock_get_all_profile_ids):
        mock_get_all_profile_ids.return_value = all_publish_profile_ids
        session = Session()
        media_id_profile_results = workflow_results_all_processed
        result = lambda_to_test.filter_medias_published_in_different_flow(session, media_id_profile_results)

        expected = [
            {'id': 'http://data.workflow.theplatform.eu/workflow/data/ProfileResult/1040302540675',
             'added': 1590512060000, 'mediaId': 'http://data.media.theplatform.eu/media/data/Media/495654469171',
             'profileId': 'http://data.publish.theplatform.eu/publish/data/PublishProfile/2642645',
             'status': 'Processed'},
            {'id': 'http://data.workflow.theplatform.eu/workflow/data/ProfileResult/1040308684398',
             'added': 1590512459000, 'mediaId': 'http://data.media.theplatform.eu/media/data/Media/495654469171',
             'profileId': 'http://data.publish.theplatform.eu/publish/data/PublishProfile/5066842',
             'status': 'Processed'}]

        self.assertEqual(result, expected)

    @patch('lambda_functions.revoke_from_other_flows.revoking.get_all_workflow_profile_ids')
    def test_filter_medias_published_in_different_flow_previously_revoked(self, mock_get_all_profile_ids):
        mock_get_all_profile_ids.return_value = all_publish_profile_ids
        session = Session()
        media_id_profile_results = workflow_results_previously_revoked

        with self.assertRaises(SystemExit):
            lambda_to_test.filter_medias_published_in_different_flow(session, media_id_profile_results)

    @patch('lambda_functions.revoke_from_other_flows.revoking.revoke_media')
    def test_revoke_oldest_matching_profile(self, event_mocked):
        session = Session()
        given_input = [
            {'id': 'http://data.workflow.theplatform.eu/workflow/data/ProfileResult/1040302540675',
             'added': 1590512060000, 'mediaId': 'http://data.media.theplatform.eu/media/data/Media/495654469171',
             'profileId': 'http://data.publish.theplatform.eu/publish/data/PublishProfile/2642645',
             'status': 'Processed'},
            {'id': 'http://data.workflow.theplatform.eu/workflow/data/ProfileResult/1040308684398',
             'added': 1590512459000, 'mediaId': 'http://data.media.theplatform.eu/media/data/Media/495654469171',
             'profileId': 'http://data.publish.theplatform.eu/publish/data/PublishProfile/5066842',
             'status': 'Processed'}]
        lambda_to_test.revoke_oldest_matching_profile(session, given_input)
        expected_media_id = "http://data.media.theplatform.eu/media/data/Media/495654469171"
        expected_profile_id = "http://data.publish.theplatform.eu/publish/data/PublishProfile/2642645"
        event_mocked.assert_called_with(
            session,
            expected_media_id,
            expected_profile_id
        )

    def test_get_profile_id_from_guid_isException_data_service(self):
        json_data = {
            "title": "ObjectNotFoundException",
            "description": "Could not find object with guid weweewe",
            "isException": True,
            "responseCode": 404,
            "correlationId": "cd872f69-fe77-4685-b513-0f05c8ee8dbe",
            "serverStackTrace": "stack trace",
            "raise_for_status": "Exception"
        }

        session = Session(404, None, json_data, HTTPError("ObjectNotFoundException"))
        with self.assertRaises(SystemExit):
            lambda_to_test.get_profile_id_from_guid(session, "guid")

    def test_get_profile_id_from_guid_isException_response(self):
        json_data = {
            "title": "ObjectNotFoundException",
            "description": "Could not find object with guid weweewe",
            "isException": True,
            "responseCode": 200,
            "correlationId": "cd872f69-fe77-4685-b513-0f05c8ee8dbe",
            "serverStackTrace": "stack trace",
            "raise_for_status": "Exception"
        }

        session = Session(200, None, json_data, None)
        with self.assertRaises(SystemExit):
            lambda_to_test.get_profile_id_from_guid(session, "guid")

    def test_get_profile_id_from_guid_empty_entries(self):
        json_data = {
            "startIndex": 1,
            "itemsPerPage": 100,
            "entryCount": 0,
            "entries": [

            ]
        }
        session = Session(200, None, json_data, None)
        with self.assertRaises(SystemExit):
            lambda_to_test.get_profile_id_from_guid(session, "guid")

    def test_get_profile_id_from_guid_with_entries(self):
        json_data = {
            "startIndex": 1,
            "itemsPerPage": 100,
            "entryCount": 0,
            "entries": [
                {
                    "id": "http://data.publish.theplatform.eu/publish/data/PublishProfile/2642574",
                    "guid": "urn:cts:nbcr:ocs:guid:publish:publishprofile:main:step-06:1.3.0"
                }
            ]
        }

        expected_value = [
                {
                    "id": "http://data.publish.theplatform.eu/publish/data/PublishProfile/2642574",
                    "guid": "urn:cts:nbcr:ocs:guid:publish:publishprofile:main:step-06:1.3.0"
                }
            ]
        session = Session(200, None, json_data, None)
        result = lambda_to_test.get_profile_id_from_guid(session, "guid")
        self.assertEqual(result, expected_value)


if __name__ == '__main__':
    unittest.main()
