import boto3
import json


def handler(event, context):
    for record in event["Records"]:
        message = json.loads(record["Sns"]["Message"])
        print(message)
        # TODO check status and send callback to step function
        #   need to get the job to get the tags :(
