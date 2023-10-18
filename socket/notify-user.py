import boto3
import os
import json


def send_message(action, data, connections):
    stage = os.environ["STAGE"]
    domain_name = os.environ["DOMAIN"]
    region = os.environ["REGION"]

    url = f"https://{domain_name}.execute-api.{region}.amazonaws.com/{stage}"
    print(url)
    client = boto3.client(
        "apigatewaymanagementapi",
        endpoint_url=url,
    )

    data = {"action": action, "data": data}
    data = json.dumps(data).encode("utf-8")

    for item in connections:
        try:
            client.post_to_connection(ConnectionId=item["connectionId"], Data=data)
        except Exception as e:
            print(e)


def handler(event, context):
    print(event)
    table_name = f"video-ai-{os.environ['STAGE']}-connections"
    table = boto3.resource("dynamodb").Table(table_name)
    user_id = event["Records"][0]["dynamodb"]["Keys"]["userId"]["S"]
    connections = table.query(
        IndexName="UserIdIndex", KeyConditionExpression="userId = :value", ExpressionAttributeValues={":value": user_id}
    )
    if "Items" not in connections:
        return
    connections = connections["Items"]

    for record in event["Records"]:
        if record["eventName"] == "MODIFY":
            old_document = record["dynamodb"]["OldImage"]
            new_document = record["dynamodb"]["NewImage"]
            if "status" not in old_document or old_document["status"]["S"] != new_document["status"]["S"]:
                status = new_document["status"]["S"]
                print(f"new status: {status}")
                send_message(status, {}, connections)
