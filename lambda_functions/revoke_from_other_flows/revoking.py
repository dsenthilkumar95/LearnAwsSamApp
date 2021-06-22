import json
import os
import logging
import requests
from pytp import authentication

REVOKE_PROFILE_GUID = os.getenv('REVOKE_PROFILE_GUID')
MPX_USERNAME = os.getenv("MPX_USERNAME")
MPX_PASSWORD = os.getenv("MPX_PASSWORD")
MPX_AUTH_REGION = os.getenv("MPX_AUTH_REGION")
MPX_ACCOUNT = os.getenv("MPX_ACCOUNT")
LONDON_WORKFLOW_GUID = os.getenv("LONDON_WORKFLOW_GUID")
MAIN_WORKFLOW_GUID = os.getenv("MAIN_WORKFLOW_GUID")
LEGACY_WORKFLOW_GUID = os.getenv("LEGACY_WORKFLOW_GUID")

logger = logging.getLogger("RevokeFromOtherFlows")
logger.setLevel(os.getenv("LOG_LEVEL", "DEBUG"))


def lambda_handler(event, context):
    requests_session = requests.session()
    requests_session.auth = authentication.mpxAuth(username=MPX_USERNAME, password=MPX_PASSWORD,
                                                   account_title=MPX_ACCOUNT, region=MPX_AUTH_REGION)

    notification = []
    for record in event["Records"]:
        if "Sns" not in record:
            continue
        if "Message" not in record["Sns"] or record["Sns"]["Message"] == "":
            continue
        notification.append(json.loads(record["Sns"]["Message"]))

    if notification:
        valid_notifications = filter_input_notifications(requests_session, notification)
        if not valid_notifications:
            logger.debug("Not a valid notification. Exit Lambda")
            return None
    else:
        logger.debug("No notification Message content. Exit Lambda")
        return None

    logger.debug("Valid notifications message to process: " + json.dumps(valid_notifications))

    media_id_profile_results = get_all_profile_results_for_media(requests_session, valid_notifications)

    valid_profile_results = {}
    if len(media_id_profile_results.items()) > 0:
        valid_profile_results = filter_medias_published_in_different_flow(requests_session, media_id_profile_results)

    if len(valid_profile_results) > 0:
        revoke_oldest_matching_profile(requests_session, valid_profile_results)


def get_profile_id_from_guid(requests_session, guid):

    publish_profiles_ds = None
    publish_profile_url = 'http://data.publish.theplatform.eu/publish/data/PublishProfile'
    publish_profile_params = {
        'schema': '1.9.0',
        'form': 'cjson',
        'pretty': 'true',
        'fields': "id,guid",
        'byGuid': guid
    }
    try:
        publish_profiles_ds = requests_session.get(url=publish_profile_url, params=publish_profile_params)
        publish_profiles_ds.raise_for_status()
        if "isException" in publish_profiles_ds.json():
            raise Exception(publish_profiles_ds.json())
        publish_profiles_ds = publish_profiles_ds.json()
        if "entries" not in publish_profiles_ds or len(publish_profiles_ds["entries"]) == 0:
            raise Exception(publish_profiles_ds)
    except Exception as e:
        logger.error("Error occurred in Publish Profiles API call: " + str(e))
        exit(1)

    return publish_profiles_ds["entries"]


def get_all_workflow_profile_ids(requests_session):
    guid_list = f"{LONDON_WORKFLOW_GUID}|{MAIN_WORKFLOW_GUID}|{LEGACY_WORKFLOW_GUID}"
    selected_profile_ids = get_profile_id_from_guid(requests_session, guid_list)
    all_publish_profile_id_list = []
    for profile_id in selected_profile_ids:
        all_publish_profile_id_list.append(profile_id['id'])
    return all_publish_profile_id_list


def filter_input_notifications(requests_session, notifications):
    valid_notifications = []
    revoke_profile_id = get_profile_id_from_guid(requests_session, REVOKE_PROFILE_GUID)[0]['id']
    if revoke_profile_id is None:
        logger.error("Revoke publish profileId not found")
        exit(1)
    for notification in notifications:
        entry = notification['entry']
        if "profileId" not in entry:
            continue
        if "status" not in entry:
            continue
        if "id" not in entry:
            continue
        if "mediaId" not in entry:
            continue
        if entry["profileId"] != revoke_profile_id or entry['status'] != "Processed":
            continue
        logger.debug("Valid notification with revoke profile published")
        valid_notifications.append(notification)

    return valid_notifications


def get_profile_results(requests_session, media_id):
    page_size = 500
    entries_size = page_size
    first_index = 1
    last_index = page_size

    all_profile_results = []
    workflow_url = 'http://data.workflow.theplatform.eu/workflow/data/ProfileResult'
    workflow_params = {
        'schema': '1.3.0',
        'form': 'cjson',
        'pretty': 'true',
        'fields': 'id,mediaId,profileId,status,added',
        'byMediaId': media_id,
        'sort': "added|asc"
    }

    while entries_size == page_size:
        workflow_params["range"] = str(first_index) + "-" + str(last_index)
        profile_results_ds = None
        try:
            profile_results_ds = requests_session.get(url=workflow_url, params=workflow_params)
            profile_results_ds.raise_for_status()
            if "isException" in profile_results_ds.json():
                raise Exception(profile_results_ds.json())
            profile_results_ds = profile_results_ds.json()
        except Exception as e:
            logger.error("Error occurred in Profile Results API call: " + str(e))
            exit(1)

        all_profile_results.extend(profile_results_ds["entries"])
        entries_size = len(profile_results_ds["entries"])

        first_index += page_size
        last_index += page_size

    return all_profile_results


def get_all_profile_results_for_media(requests_session, valid_notifications):
    profile_results = {}
    for notification in valid_notifications:
        media_id = notification['entry']['mediaId']
        all_profile_results = get_profile_results(requests_session, media_id)
        profile_results[media_id] = all_profile_results
    return profile_results


def filter_medias_published_in_different_flow(requests_session, media_id_profile_results):
    all_publish_profile_ids = get_all_workflow_profile_ids(requests_session)
    valid_revoke_profiles = []
    for media_id, profile_results_list in media_id_profile_results.items():
        for profile_result in profile_results_list:
            if profile_result['profileId'] in all_publish_profile_ids and profile_result['status'] == 'Processed':
                valid_revoke_profiles.append(profile_result)
        if len(valid_revoke_profiles) == 1:
            logger.error("Media is published with only one workflow but the revoking profile was triggered")
            exit(1)

    return valid_revoke_profiles


def revoke_oldest_matching_profile(requests_session, valid_profile_results):
    revoke_profile_id = valid_profile_results[0]["profileId"]
    revoke_media_id = valid_profile_results[0]["mediaId"]
    revoke_result = revoke_media(requests_session, revoke_media_id, revoke_profile_id)
    logger.info(f"Successfully revoked {revoke_profile_id} from {revoke_media_id}, result {revoke_result}")
    return revoke_result


def revoke_media(requests_session, media_id, profile_id):
    revoke_public_url = 'http://publish.theplatform.eu/web/Publish/revoke'
    revoke_public_params = {
        'schema': '1.2',
        'form': 'json',
        'pretty': 'true',
        "_mediaId": media_id,
        "_profileId": profile_id
    }
    revoke_publish_ds = None
    try:
        revoke_publish_ds = requests_session.get(url=revoke_public_url, params=revoke_public_params)
        revoke_publish_ds.raise_for_status()
        if "isException" in revoke_publish_ds.json():
            raise Exception(revoke_publish_ds.json())
        revoke_publish_ds = revoke_publish_ds.json()
    except Exception as e:
        logger.error("Error occurred in Revoke Publish API call: " + str(e))
        exit(1)

    return revoke_publish_ds
