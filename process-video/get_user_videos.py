import boto3
import os
import json
from decimal import Decimal


def converter(o):
    if isinstance(o, Decimal):
        return float(o)
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


def handler(event, handler):
    stage = os.environ["STAGE"]
    user_id = event["requestContext"]["authorizer"]["iam"]["cognitoIdentity"]["identityId"]

    videos_table_name = f"video-ai-{stage}-user-videos"
    videos_table = boto3.resource("dynamodb").Table(videos_table_name)

    result = videos_table.query(
        IndexName="UserIdIndex",
        KeyConditionExpression="userId = :userId",
        ExpressionAttributeValues={":userId": user_id},
    )

    if "Items" not in result:
        return {"statusCode": 404, "body": "User has no videos"}
    videos = result["Items"]

    for video in videos:
        video["name"] = video["key"].split("/")[-1]
        del video["userId"]

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(videos, default=converter),
    }
