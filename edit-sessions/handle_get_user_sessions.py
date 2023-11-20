import boto3
import os
import json
from decimal import Decimal


def converter(o):
    if isinstance(o, Decimal):
        return float(o)
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


def format_session(session):
    if session["currentEdit"]:
        session["currentEdit"] = session["currentEdit"][-1]
    del session["userId"]
    return session


def handler(event, context):
    stage = os.environ["STAGE"]
    user_id = event["requestContext"]["authorizer"]["iam"]["cognitoIdentity"]["identityId"]
    edit_session_table_name = f"video-ai-{stage}-edit-session"
    edit_session_table = boto3.resource("dynamodb").Table(edit_session_table_name)

    result = edit_session_table.query(
        IndexName="UserIdIndex",
        KeyConditionExpression="userId = :userId",
        ExpressionAttributeValues={":userId": user_id},
    )

    if "Items" not in result:
        return {"statusCode": 404, "body": "User has no edit sessions"}
    sessions = result["Items"]
    sessions = [format_session(session) for session in sessions]

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(sessions, default=converter),
    }
