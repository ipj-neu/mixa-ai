import json


def hello(event, context):
    print("Body: ", json.loads(event["body"]))
    print("here")
    body = {
        "message": "Go Serverless v3.0! Your function executed successfully!",
        "input": event,
    }

    return {"statusCode": 200, "body": json.dumps(body)}
