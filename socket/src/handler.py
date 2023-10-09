import boto3
import os


def on_connect(event, context):
    print("on_connect")
    stage = os.getenv("STAGE")
    user_id = event["queryStringParameters"]["userId"]
    table_name = f"video-ai-{stage}-connections"

    table = boto3.resource("dynamodb").Table(table_name)
    table.put_item(Item={"connectionId": event["requestContext"]["connectionId"], "userId": user_id})

    return {"statusCode": 200}


def on_disconnect(event, context):
    print("on_disconnect")
    stage = os.getenv("STAGE")
    table_name = f"video-ai-{stage}-connections"

    table = boto3.resource("dynamodb").Table(table_name)
    table.delete_item(Key={"connectionId": event["requestContext"]["connectionId"]})
    return {"statusCode": 200}


def send_message(event, context):
    """This function is made to be used in te step function to send users updates"""
    print("send_message")
    domain_name = os.getenv("DOMAIN_NAME")
    region = os.getenv("REGION")
    stage = os.getenv("STAGE")
    print(type(domain_name))

    # TODO figure out how i want to get the user id in the step function
    userId = ""

    # TODO after getting the user id query the connections table and send the message to the correct connections
    # remove connectionId
    connectionId = ""
    table_name = f"video-ai-{stage}-connections"
    table = boto3.resource("dynamodb").Table(table_name)

    url = f"https://{domain_name}.execute-api.{region}.amazonaws.com/{stage}"
    print(url)
    client = boto3.client(
        "apigatewaymanagementapi",
        endpoint_url=url,
    )

    try:
        client.post_to_connection(ConnectionId=connectionId, Data="testing")
    except client.exceptions.GoneException:
        print("connection does not exist: " + connectionId)

    return {"statusCode": 200}
