import boto3
import json
import os
from uuid import uuid4


# NOTE this might make sense to be a web socket handler instead of an http handler
def handle_message(event, context):
    state_machine_arn = os.environ["STATE_MACHINE_ARN"]
    stage = os.environ["STAGE"]
    user_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]

    body = json.loads(event.get("body", {}))
    message = body.get("message")
    session = body.get("sessionId")
    if not message or not session:
        return {"statusCode": 400, "body": "message and sessionId are required"}

    statuses_table_name = f"video-ai-{stage}-message-processing-statuses"
    db_client = boto3.resource("dynamodb")
    status_table = db_client.Table(statuses_table_name)
    new_item = {
        "sessionId": session,
        "userId": user_id,
        "status": "ai_processing",
    }

    # only allows one message to be processed at a time per session
    try:
        status_table.put_item(
            Item=new_item,
            ConditionExpression="attribute_not_exists(sessionId) OR #st = :complete_val",
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={":complete_val": "complete"},
        )
    except db_client.meta.client.exceptions.ConditionalCheckFailedException:
        return {
            "statusCode": 400,
            "body": "message processing already started for this session, please wait for it to finish",
        }

    sf_client = boto3.client("stepfunctions")
    parameters = {"userId": user_id, "message": message, "sessionId": session, "origin": "handle_message"}
    # NOTE don't really need the custom name, but it makes it easier to find the execution in the console
    sf_client.start_execution(
        name=str(uuid4()) + "-session-" + session,
        stateMachineArn=state_machine_arn,
        input=json.dumps(parameters),
    )

    return {
        "statusCode": 200,
        "body": "message processing started",
    }
