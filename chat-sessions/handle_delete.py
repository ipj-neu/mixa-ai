import boto3
import os


def handler(event, context):
    # TODO also remove all the videos stored in the bucket for this session
    stage = os.environ["STAGE"]
    user_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    params = event.get("pathParameters", {})
    if "sessionId" not in params:
        return {"statusCode": 400, "body": "sessionId is required"}
    session_id = params["sessionId"]
    history_table = boto3.resource("dynamodb").Table(f"video-ai-{stage}-chat-sessions-history")
    videos_table = boto3.resource("dynamodb").Table(f"video-ai-{stage}-chat-sessions-videos")
    key = {"sessionId": session_id, "userId": user_id}
    history_table.delete_item(Key=key)
    videos_table.delete_item(Key=key)
    return {"statusCode": 200, "body": "Items deleted successfully"}
