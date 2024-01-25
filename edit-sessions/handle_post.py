import boto3
from uuid import uuid4
import json
import os


def handler(event, context):
    stage = os.environ["STAGE"]
    user_id = event["requestContext"]["authorizer"]["iam"]["cognitoIdentity"]["identityId"]
    edit_session_uuid = str(uuid4())
    edit_session_table_name = f"video-ai-{stage}-edit-session"
    edit_session_table = boto3.resource("dynamodb").Table(edit_session_table_name)

    starting_session = {
        "sessionId": edit_session_uuid,
        "userId": user_id,
        "name": "New Edit",
        "videos": {},
        "currentEdit": [],
        "status": "IDLE",
        "videoStatus": "NOT AVAILABLE",
    }
    edit_session_table.put_item(Item=starting_session)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"sessionId": edit_session_uuid}),
    }
