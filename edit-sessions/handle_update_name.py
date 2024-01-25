import os
import boto3
import json


def handler(event, context):
    stage = os.environ["STAGE"]
    user_id = event["requestContext"]["authorizer"]["iam"]["cognitoIdentity"]["identityId"]

    params = event.get("pathParameters", {})
    body = json.loads(event.get("body", "{}"))
    if "sessionId" not in params or "name" not in body:
        return {"statusCode": 400, "body": "sessionId and name are required"}
    session_id = params["sessionId"]
    name = body["name"]

    edit_session_table_name = f"video-ai-{stage}-edit-session"
    edit_session_table = boto3.resource("dynamodb").Table(edit_session_table_name)

    try:
        edit_session_table.update_item(
            Key={"sessionId": session_id},
            UpdateExpression="SET #name = :name",
            ConditionExpression="userId = :userId",
            ExpressionAttributeNames={"#name": "name"},
            ExpressionAttributeValues={":name": name, ":userId": user_id},
        )
    except boto3.exceptions.botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print(f"Item {session_id} already exists in the list.")
            return {"statusCode": 404}
        else:
            raise e

    return {"statusCode": 200, "body": "Successfully updated the session name."}
