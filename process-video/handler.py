import boto3
from urllib import parse
import os
from botocore.exceptions import ClientError
import subprocess
from decimal import Decimal


def on_new_video(event, context):
    stage = os.environ["STAGE"]

    # TODO Possibly get the tables from outputs
    table_name = f"video-ai-{stage}-chat-sessions-videos"
    s3_bucket = f"video-ai-videos-{stage}"

    table = boto3.resource("dynamodb").Table(table_name)
    s3_client = boto3.client("s3")

    # parse the key for the user id, session id, and video title
    key = parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"])
    user_id = key.split("/")[-3]
    session_id = key.split("/")[-2]
    video_title = key.split("/")[-1]
    print(f"key: {key}, user_id: {user_id}, session_id: {session_id}, video_title: {video_title}")

    # get the presigned url for the video
    # NOTE maybe change expiration time
    video_url = s3_client.generate_presigned_url("get_object", Params={"Bucket": s3_bucket, "Key": key}, ExpiresIn=300)

    # get the framerate, width, and height of the video using ffprobe layer
    # command generated by gpt
    cmd = [
        "/opt/bin/ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=r_frame_rate,width,height,duration",
        "-of",
        "default=nw=1:nk=1",
        video_url,
    ]

    output = subprocess.check_output(cmd, universal_newlines=True)
    width, height, framerate, duration = output.strip().split("\n")
    print(f"width: {width}, height: {height}, framerate: {framerate}, duration: {duration}")

    # convert framerate to a decimal
    framerate = framerate.split("/")
    framerate = Decimal(int(framerate[0]) / int(framerate[1]))

    # update the table with the metadata
    video_data = {
        "name": key,
        "availableData": {},
        "metadata": {"framerate": framerate, "width": width, "height": height, "duration": duration},
    }

    # should always be the first time the key video_title is used so will not overwrite
    table.update_item(
        Key={"sessionId": session_id, "userId": user_id},
        UpdateExpression="SET videos.#video_title = :data",
        ExpressionAttributeNames={"#video_title": video_title},
        ExpressionAttributeValues={":data": video_data},
    )


# def on_new_video_rek(event, context):
#     # TODO add checks, error handling, and a better way to get the table name

#     print("Starting on_new_video...")

#     # HACK
#     table_name = "video-ai-dev-chat-sessions"

#     table = boto3.resource("dynamodb").Table(table_name)

#     rek_sns_topic = os.environ["REK_SNS_TOPIC"]
#     rek_role = os.environ["REK_ROLE"]
#     key = parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"])
#     user_id = key.split("/")[-3]
#     session_id = key.split("/")[-2]
#     video_title = key.split("/")[-1]

#     print("Updating table...")
#     rek_client = boto3.client("rekognition")
#     table.update_item(
#         Key={"sessionId": session_id, "userId": user_id},
#         UpdateExpression="SET videos.#video_title = :data",
#         ExpressionAttributeNames={"#video_title": video_title},
#         ExpressionAttributeValues={":data": {}},
#     )

#     print("Starting label detection...")
#     rek_client.start_label_detection(
#         Video={
#             "S3Object": {
#                 "Bucket": event["Records"][0]["s3"]["bucket"]["name"],
#                 "Name": key,
#             }
#         },
#         NotificationChannel={
#             "SNSTopicArn": rek_sns_topic,
#             "RoleArn": rek_role,
#         },
#     )

#     print("Processing complete")
