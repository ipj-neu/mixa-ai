import boto3
import os
import json


def handler(event, context):
    # TODO maybe add validation that the user has access to the session and the video exists
    stage = os.environ["STAGE"]
    user_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    params = event.get("pathParameters", {})
    body = json.loads(event.get("body", "{}"))
    if "sessionId" not in params or "videoId" not in body:
        return {"statusCode": 400, "body": "sessionId is required"}
    session_id = params["sessionId"]
    video_id = body["videoId"]

    edit_session_table_name = f"video-ai-{stage}-edit-session"
    edit_session_table = boto3.resource("dynamodb").Table(edit_session_table_name)

    try:
        response = edit_session_table.update_item(
            Key={
                "sessionId": session_id,
            },
            UpdateExpression="SET videos = list_append(videos, :newVideo)",
            ConditionExpression="NOT contains(videos, :newVideoValue)",
            ExpressionAttributeValues={
                ":newVideo": [video_id],
                ":newVideoValue": video_id,
            },
        )
        print(response)
    except boto3.exceptions.botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print(f"Item {video_id} already exists in the list.")
            return {"statusCode": 404}
        else:
            raise e

    return {
        "statusCode": 200,
    }
