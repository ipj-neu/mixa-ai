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
    table = boto3.resource("dynamodb").Table(f"video-ai-{stage}-chat-sessions-history")
    chat = table.get_item(Key={"sessionId": session_id, "userId": user_id}, ProjectionExpression="History")
    if "Item" not in chat and "History" not in chat["Item"]:
        return {"statusCode": 404, "body": "Item not found"}
    history = chat["Item"]["History"]
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"history": history}),
    }
