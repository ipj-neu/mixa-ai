import boto3
from uuid import uuid4
import json
import os


def handler(event, context):
    stage = os.environ["STAGE"]

    user_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    chat_uuid = str(uuid4())

    table = boto3.resource("dynamodb").Table(f"video-ai-{stage}-chat-sessions")

    chat_session = {"sessionId": chat_uuid, "userId": user_id, "History": [], "videos": {}}

    table.put_item(Item=chat_session)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"sessionId": chat_uuid}),
    }
