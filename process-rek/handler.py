import boto3
import json
import os
import decimal


def handler(event, context):
    # TODO add checks and error handling

    stage = os.environ["STAGE"]
    rek_client = boto3.client("rekognition")
    session_table = boto3.resource("dynamodb").Table(f"video-ai-{stage}-chat-sessions")

    # load the message from the SNS event
    body = json.loads(event["Records"][0]["body"])
    msg = json.loads(body["Message"])

    # get the job
    job_id = msg["JobId"]
    job = rek_client.get_label_detection(JobId=job_id)

    # convert floats to decimals
    metadata = job["VideoMetadata"]
    metadata["FrameRate"] = decimal.Decimal(metadata["FrameRate"])

    # update the session table
    s3_name = job["Video"]["S3Object"]["Name"]
    video_title = s3_name.split("/")[-1]
    session_id = s3_name.split("/")[-2]
    user_id = s3_name.split("/")[-3]
    session_table.update_item(
        Key={"sessionId": session_id, "userId": user_id},
        UpdateExpression="SET videos.#video_title.metadata = :metadata",
        ExpressionAttributeNames={"#video_title": video_title},
        ExpressionAttributeValues={":metadata": metadata},
    )
