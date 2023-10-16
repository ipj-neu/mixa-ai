import boto3
from urllib import parse
import os
from botocore.exceptions import ClientError


def on_new_video(event, context):
    # TODO add checks, error handling, and a better way to get the table name
    # HACK

    print("Starting on_new_video...")

    table_name = "video-ai-dev-chat-sessions"

    table = boto3.resource("dynamodb").Table(table_name)

    rek_sns_topic = os.environ["REK_SNS_TOPIC"]
    rek_role = os.environ["REK_ROLE"]
    key = parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"])
    user_id = key.split("/")[-3]
    session_id = key.split("/")[-2]
    video_title = key.split("/")[-1]

    print("Updating table...")
    rek_client = boto3.client("rekognition")
    table.update_item(
        Key={"sessionId": session_id, "userId": user_id},
        UpdateExpression="SET videos.#video_title = :data",
        ExpressionAttributeNames={"#video_title": video_title},
        ExpressionAttributeValues={":data": {}},
    )

    print("Starting label detection...")
    rek_client.start_label_detection(
        Video={
            "S3Object": {
                "Bucket": event["Records"][0]["s3"]["bucket"]["name"],
                "Name": key,
            }
        },
        NotificationChannel={
            "SNSTopicArn": rek_sns_topic,
            "RoleArn": rek_role,
        },
    )

    print("Processing complete")
