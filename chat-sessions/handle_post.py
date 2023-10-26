import boto3
from uuid import uuid4
import json
import os


def handler(event, context):
    stage = os.environ["STAGE"]
    user_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    chat_uuid = str(uuid4())
    history_table = boto3.resource("dynamodb").Table(f"video-ai-{stage}-chat-sessions-history")
    videos_table = boto3.resource("dynamodb").Table(f"video-ai-{stage}-chat-sessions-videos")
    history_item = {"sessionId": chat_uuid, "userId": user_id, "History": []}
    videos_item = {"sessionId": chat_uuid, "userId": user_id, "videos": {}}

    history_table.put_item(Item=history_item)
    videos_table.put_item(Item=videos_item)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"sessionId": chat_uuid}),
    }
