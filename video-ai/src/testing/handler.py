import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def step_function_testing(event, context):
    print(event)
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
                "videoName": "private/us-east-1:d0ac9c0c-bd51-4d08-a72c-28cc64993441/84c81408-2091-7017-9115-d5882b7deeed/testing_session/Command_Vid.mp4",
            },
            {
                "type": "label",
                "videoName": "private/us-east-1:d0ac9c0c-bd51-4d08-a72c-28cc64993441/84c81408-2091-7017-9115-d5882b7deeed/testing_session/Lemmings_Jumping_off_Cliffs.mp4",
            },
        ]
    }
