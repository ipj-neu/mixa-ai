import boto3
import os
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    stage = os.environ["STAGE"]
    user_id = event["requestContext"]["authorizer"]["iam"]["cognitoIdentity"]["identityId"]
    params = event.get("pathParameters", {})
    if "sessionId" not in params:
        return {"statusCode": 400, "body": "sessionId is required"}
    session_id = params["sessionId"]

    edit_session_table_name = f"video-ai-{stage}-edit-session"
    edit_session_table = boto3.resource("dynamodb").Table(edit_session_table_name)

    # remove session from table if the user owns it
    try:
        edit_session_table.delete_item(
            Key={"sessionId": session_id},
            ConditionExpression="userId = :userId",
            ExpressionAttributeValues={":userId": user_id},
        )
    except ClientError as e:
        logger.error("Failed to delete video", exc_info=True)
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {"statusCode": 403, "body": "User does not have access to this session"}
        else:
            raise

    return {"statusCode": 200, "body": "Successfully deleted the session."}
