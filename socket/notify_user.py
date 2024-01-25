import boto3
import os
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    stage = os.environ["STAGE"]
    region = os.environ["REGION"]
    domain_name = os.environ["DOMAIN"]

    url = f"https://{domain_name}.execute-api.{region}.amazonaws.com/{stage}"
    socket_client = boto3.client("apigatewaymanagementapi", endpoint_url=url)

    table_name = f"video-ai-{stage}-user-connections"
    table = boto3.resource("dynamodb").Table(table_name)

    try:
        for record in event["Records"]:
            sns_message = json.loads(record["Sns"]["Message"])
            socket_message = json.dumps(sns_message["message"]).encode("utf-8")
            user_id = sns_message["userId"]
            connections = table.query(
                IndexName="UserIdIndex",
                KeyConditionExpression="userId = :userId",
                ExpressionAttributeValues={":userId": user_id},
            )
            if "Items" not in connections:
                return
            connections = connections["Items"]
            for item in connections:
                try:
                    socket_client.post_to_connection(ConnectionId=item["connectionId"], Data=socket_message)
                except socket_client.exceptions.GoneException:
                    table.delete_item(Key={"connectionId": item["connectionId"]})
    except:
        logger.error("Error when sending socket message to user", exc_info=True)
