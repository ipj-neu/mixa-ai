import boto3
import os
import json


def handler(event, context):
    stage = os.environ["STAGE"]
    user_id = event["requestContext"]["authorizer"]["iam"]["cognitoIdentity"]["identityId"]
    params = event.get("pathParameters", {})
    body = json.loads(event.get("body", "{}"))
    if "sessionId" not in params or "videoId" not in body:
        return {"statusCode": 400, "body": "sessionId is required"}
    session_id = params["sessionId"]
    video_id = body["videoId"]

    edit_session_table_name = f"video-ai-{stage}-edit-session"
    user_videos_table_name = f"video-ai-{stage}-user-videos"
    edit_session_table = boto3.resource("dynamodb").Table(edit_session_table_name)
    user_videos_table = boto3.resource("dynamodb").Table(user_videos_table_name)

    try:
        video_response = user_videos_table.get_item(Key={"videoId": video_id})
        if "Item" not in video_response:
            return {"statusCode": 404, "body": "video not found"}
        video = video_response["Item"]
        if video["userId"] != user_id:
            return {"statusCode": 403, "body": "user does not have access to this video"}

        session_video = {
            "name": video["key"].split("/")[-1],
            "key": video["key"],
            "metadata": video["metadata"],
        }

        response = edit_session_table.update_item(
            Key={
                "sessionId": session_id,
            },
            UpdateExpression="SET videos.#videoId = :video",
            ExpressionAttributeNames={"#videoId": video_id},
            ExpressionAttributeValues={":video": session_video},
        )
        print(response)
    except boto3.exceptions.botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print(f"Item {video_id} already exists in the list.")
            return {"statusCode": 404}
        else:
            raise e

    return {"statusCode": 200}
