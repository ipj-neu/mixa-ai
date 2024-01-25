import os
import boto3


def handler(event, context):
    stage = os.environ["STAGE"]
    temp_password = event["queryStringParameters"]["tempPassword"]
    print(f"authorizing temp password: {temp_password}")

    temp_password_table_name = f"video-ai-{stage}-websocket-preflight"
    temp_password_table = boto3.resource("dynamodb").Table(temp_password_table_name)
    response = temp_password_table.delete_item(Key={"tempPassword": temp_password}, ReturnValues="ALL_OLD")
    if "Attributes" not in response:
        return generate_policy("user", "Deny", event["methodArn"])
    user_id = response["Attributes"]["userId"]
    return generate_policy(user_id, "Allow", event["methodArn"])


def generate_policy(principal_id, effect, resource):
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{"Action": "execute-api:Invoke", "Effect": effect, "Resource": resource}],
        },
    }
