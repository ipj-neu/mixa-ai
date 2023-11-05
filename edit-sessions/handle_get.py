import boto3
import os
import json


def handler(event, context):
    stage = os.environ["STAGE"]
    user_id = event["requestContext"]["authorizer"]["iam"]["cognitoIdentity"]["identityId"]
    params = event.get("pathParameters", {})
    if "sessionId" not in params:
        return {"statusCode": 400, "body": "sessionId is required"}
    session_id = params["sessionId"]
    edit_session_table_name = f"video-ai-{stage}-edit-session"
    edit_session_table = boto3.resource("dynamodb").Table(edit_session_table_name)
    result = edit_session_table.get_item(Key={"sessionId": session_id})
    if "Item" not in result:
        return {"statusCode": 404, "body": "Session not found"}

    if result["Item"]["userId"] != user_id:
        return {"statusCode": 403, "body": "User does not have access to this session"}

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(result["Item"]),
    }
