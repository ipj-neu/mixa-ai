def testing(event, context):
    print(event)
    print(context)
    return {"statusCode": 200, "body": "pong"}
