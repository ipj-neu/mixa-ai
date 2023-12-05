import boto3
import json
import os


def handler(event, context):
    stage = os.environ["STAGE"]
    messages_topic_arn = os.environ["MESSAGES_TOPIC_ARN"]

    message = json.loads(event["Records"][0]["Sns"]["Message"])

    edit_session_table_name = f"video-ai-{stage}-edit-session"
    edit_session_table = boto3.resource("dynamodb").Table(edit_session_table_name)

    if message["detail"]["status"] != "COMPLETE":
        return

    session_id = (
        message["detail"]["outputGroupDetails"][0]["outputDetails"][0]["outputFilePaths"][0]
        .split("/")[-1]
        .split(".")[0]
    )
    user_id = message["detail"]["outputGroupDetails"][0]["outputDetails"][0]["outputFilePaths"][0].split("/")[-2]
    print(f"session_id: {session_id}, user_id: {user_id}")

    edit_session_table.update_item(
        Key={"sessionId": session_id},
        UpdateExpression="SET #videoStatus = :videoStatus",
        ExpressionAttributeNames={"#videoStatus": "videoStatus"},
        ExpressionAttributeValues={":videoStatus": "AVAILABLE"},
    )

    messages_sns = boto3.client("sns")
    messages_sns.publish(
        TopicArn=messages_topic_arn,
        Message=json.dumps(
            {
                "userId": user_id,
                "message": {
                    "action": "mediaConvertCompleted",
                    "sessionId": session_id,
                },
            }
        ),
    )
