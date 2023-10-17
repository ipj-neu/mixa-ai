import boto3
import os
import json


def handler(event, context):
    stage = os.environ["STAGE"]

    user_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]

    params = event.get("pathParameters", {})
    if "sessionId" not in params:
        return {"statusCode": 400, "body": "sessionId is required"}
    session_id = params["sessionId"]

    table = boto3.resource("dynamodb").Table(f"video-ai-{stage}-chat-sessions")

    table.delete_item(Key={"sessionId": session_id, "userId": user_id})

    return {"statusCode": 200, "body": "Item deleted successfully"}
