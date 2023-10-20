import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def step_function_testing(event, context):
    stage = os.environ.get("STAGE", "dev")
    logger.info(f"starting handle_message video-ai-{stage}")

    # all information should always be there except for maybe the message depending on the origin
    user_id = event["userId"]
    session = event["sessionId"]
    message = event.get("message", None)
    origin = event["origin"]

    logger.info(f"user_id: {user_id}")
    logger.info(f"session: {session}")
    logger.info(f"message: {message}")
    logger.info(f"origin: {origin}")

    return {
        "jobs": [
            {
                "type": "label",
                "s3Bucket": {"Bucket": "bucket_name", "Name": "file_name"},
                "notificationChannel": {"RoleArn": "role_arn", "snsTopicArn": "sns_topic_arn"},
            },
            {
                "type": "video",
                "s3Bucket": {"Bucket": "bucket_name", "Name": "file_name"},
                "notificationChannel": {"RoleArn": "role_arn", "snsTopicArn": "sns_topic_arn"},
            },
        ]
    }
