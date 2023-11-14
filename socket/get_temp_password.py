import boto3
import os
import json
import time
from uuid import uuid4


def handler(event, context):
    stage = os.environ["STAGE"]
    user_id = event["requestContext"]["authorizer"]["iam"]["cognitoIdentity"]["identityId"]

    temp_password_table_name = f"video-ai-{stage}-websocket-preflight"
    temp_password_table = boto3.resource("dynamodb").Table(temp_password_table_name)

    temp_password = str(uuid4())
    ttl_seconds = 60 * 5
    expiration_time = int(time.time() + ttl_seconds)

    item = {
        "tempPassword": temp_password,
        "userId": user_id,
        "ttl": expiration_time,
    }
    temp_password_table.put_item(Item=item)

    body = {"tempPassword": temp_password}

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
