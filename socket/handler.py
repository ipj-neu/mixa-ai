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


def send_message(event, context):
    # HACK this function needs to be changed to be used in the step function
    #   DO NOT FOCUS ON THIS NOT A PRIORITY RIGHT NOW
    """This function is made to be used in te step function to send users updates"""
    print("send_message")
    stage = os.getenv("STAGE")
    domain_name = os.getenv("DOMAIN_NAME")
    region = os.getenv("REGION")
    print(type(domain_name))

    # TODO figure out how i want to get the user id and data in the step function
    userId = ""
    data = {}

    table_name = f"video-ai-{stage}-connections"
    table = boto3.resource("dynamodb").Table(table_name)

    connections = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key("userId").eq(userId))

    url = f"https://{domain_name}.execute-api.{region}.amazonaws.com/{stage}"
    print(url)
    client = boto3.client(
        "apigatewaymanagementapi",
        endpoint_url=url,
    )

    for connection in connections["Items"]:
        try:
            client.post_to_connection(ConnectionId=connection["connectionId"], Data=data)
        except client.exceptions.GoneException:
            connections.delete_item(Key={"connectionId": connection["connectionId"], "userId": userId})
            print("connection does not exist: " + connection["connectionId"])

    return {"statusCode": 200}
