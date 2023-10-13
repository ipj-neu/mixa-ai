import boto3
from urllib import parse


def on_new_video(event, context):
    # TODO add checks, error handling, and a better way to get the table name
    # HACK
    table_name = "video-ai-dev-chat-sessions"
    table = boto3.resource("dynamodb").Table(table_name)

    key = parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"])
    user_id = key.split("/")[2]
    session_id = key.split("/")[3]

    table.update_item(
        Key={"sessionId": session_id, "userId": user_id},
        UpdateExpression="ADD videoFiles :file",
        ExpressionAttributeValues={":file": set([key.split("/")[4]])},
    )
