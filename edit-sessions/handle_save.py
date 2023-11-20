import boto3
import os
import json
from dataclasses import dataclass
from botocore.exceptions import ClientError


@dataclass
class Timestamp:
    hours: int
    minutes: int
    seconds: int
    milliseconds: int


@dataclass
class Edit:
    videoId: str
    startTime: Timestamp
    endTime: Timestamp


def handler(event, context):
    stage = os.environ["STAGE"]
    user_id = event["requestContext"]["authorizer"]["iam"]["cognitoIdentity"]["identityId"]
    params = event.get("pathParameters", {})
    body = json.loads(event.get("body", "{}"))
    if "sessionId" not in params or "edit" not in body:
        return {"statusCode": 400, "body": "sessionId or edit is missing"}
    session_id = params["sessionId"]
    edit = body["edit"]
    if not isinstance(edit, list):
        return {"statusCode": 400, "body": "edit must be a list"}
    if len(edit) == 0:
        return {"statusCode": 400, "body": "edit must not be empty"}

    edit_session_table_name = f"video-ai-{stage}-edit-session"
    edit_session_table = boto3.resource("dynamodb").Table(edit_session_table_name)

    # validate the edit
    try:
        edits = [Edit(**e) for e in edit]
    except ValueError as e:
        return {"statusCode": 400, "body": str(e)}

    # adds the edit ot the session if the user owns it
    try:
        edit_session_table.update_item(
            Key={"sessionId": session_id},
            UpdateExpression="SET currentEdit = list_append(if_not_exists(currentEdit, :empty_list), :edit)",
            ExpressionAttributeValues={
                ":edit": edit,
                ":empty_list": [],
            },
            ConditionExpression="userId = :userId",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {"statusCode": 403, "body": "User does not have access to this session"}
        else:
            raise
