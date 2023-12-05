import boto3
import os


def milliseconds_to_frames(milliseconds, framerate):
    return round((float(milliseconds) / 1000) * float(framerate))


def edit_time_to_mediaconvert_time(edit_time, framerate):
    hours = int(edit_time["hours"])
    minutes = int(edit_time["minutes"])
    seconds = int(edit_time["seconds"])
    frames = milliseconds_to_frames(edit_time["milliseconds"], framerate)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"


def handler(event, context):
    stage = os.environ["STAGE"]
    user_id = event["requestContext"]["authorizer"]["iam"]["cognitoIdentity"]["identityId"]
    params = event.get("pathParameters", {})
    if "sessionId" not in params:
        return {"statusCode": 400, "body": "sessionId is required"}
    session_id = params["sessionId"]

    edit_session_table_name = f"video-ai-{stage}-edit-session"
    edit_session_table = boto3.resource("dynamodb").Table(edit_session_table_name)

    # get the edit session
    edit_session_response = edit_session_table.get_item(Key={"sessionId": session_id})
    if "Item" not in edit_session_response:
        return {"statusCode": 404, "body": "edit session not found"}
    edit_session = edit_session_response["Item"]
    if edit_session["userId"] != user_id:
        return {"statusCode": 403, "body": "user does not have access to this edit session"}
    if not edit_session["currentEdit"]:
        return {"statusCode": 405, "body": "no edits saved"}

    # create mediaconvert job
    mediaconvert = boto3.client("mediaconvert", endpoint_url="https://vasjpylpa.mediaconvert.us-east-1.amazonaws.com")
    destination = f"s3://video-ai-videos-dev/private/{user_id}/{session_id}"

    job_settings = {
        "Settings": {
            "Inputs": [],
            "OutputGroups": [
                {
                    "Name": "File Group",
                    "OutputGroupSettings": {
                        "Type": "FILE_GROUP_SETTINGS",
                        "FileGroupSettings": {"Destination": destination},
                    },
                    "Outputs": [
                        {
                            "VideoDescription": {
                                "CodecSettings": {
                                    "Codec": "H_264",
                                    "H264Settings": {
                                        "RateControlMode": "QVBR",
                                        "SceneChangeDetect": "TRANSITION_DETECTION",
                                        "FramerateControl": "SPECIFIED",
                                        "FramerateNumerator": 30,
                                        "FramerateDenominator": 1,
                                        "MaxBitrate": 5000000,
                                    },
                                },
                                "Width": 720,
                                "Height": 480,
                            },
                            "AudioDescriptions": [
                                {
                                    "CodecSettings": {
                                        "Codec": "AAC",
                                        "AacSettings": {
                                            "Bitrate": 96000,
                                            "CodingMode": "CODING_MODE_2_0",
                                            "SampleRate": 48000,
                                        },
                                    },
                                    "AudioSourceName": "Audio Selector 1",
                                }
                            ],
                            "ContainerSettings": {"Container": "MP4", "Mp4Settings": {}},
                        }
                    ],
                }
            ],
            "TimecodeConfig": {"Source": "ZEROBASED"},
        },
        "Role": "arn:aws:iam::956782569109:role/MediaConvertRole",
    }

    for edit in edit_session["currentEdit"][-1]:
        video = edit_session["videos"][edit["videoId"]]
        framerate = video["metadata"]["framerate"]
        start_time = edit_time_to_mediaconvert_time(edit["startTime"], framerate)
        end_time = edit_time_to_mediaconvert_time(edit["endTime"], framerate)
        input_config = {
            "TimecodeSource": "ZEROBASED",
            "AudioSelectors": {
                "Audio Selector 1": {
                    "DefaultSelection": "DEFAULT",
                }
            },
            "FileInput": f"s3://video-ai-videos-dev/{video['key']}",
            "InputClippings": [
                {
                    "StartTimecode": start_time,
                    "EndTimecode": end_time,
                }
            ],
        }
        job_settings["Settings"]["Inputs"].append(input_config)

    mediaconvert.create_job(**job_settings)

    edit_session_table.update_item(
        Key={"sessionId": session_id},
        UpdateExpression="SET #videoStatus = :videoStatus",
        ExpressionAttributeNames={"#videoStatus": "videoStatus"},
        ExpressionAttributeValues={":videoStatus": "PROCESSING"},
    )

    return {"statusCode": 200}
