import boto3
import json


def handler(event, context):
    message = json.loads(event["Records"][0]["Sns"]["Message"])
    print(message)
