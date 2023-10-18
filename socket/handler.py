import boto3
import os


def on_connect(event, context):
    print("on_connect")
    stage = os.getenv("STAGE")
    user_id = event["requestContext"]["authorizer"]["principalId"]
    table_name = f"video-ai-{stage}-connections"

    table = boto3.resource("dynamodb").Table(table_name)
    table.put_item(Item={"connectionId": event["requestContext"]["connectionId"], "userId": user_id})

    return {"statusCode": 200}


def on_disconnect(event, context):
    print("on_disconnect")
    stage = os.getenv("STAGE")
    table_name = f"video-ai-{stage}-connections"

    table = boto3.resource("dynamodb").Table(table_name)
    connectionId = event["requestContext"]["connectionId"]

    try:
        connections = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key("connectionId").eq(connectionId))
        for item in connections["Items"]:
            table.delete_item(Key={"connectionId": connectionId, "userId": item["userId"]})
    except Exception as e:
        print(e)

    return {"statusCode": 200}
