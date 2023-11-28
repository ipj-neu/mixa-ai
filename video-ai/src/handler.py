# to unzip the requirements when deployed to AWS Lambda
try:
    import unzip_requirements  # type: ignore
except ImportError:
    pass

import os
from typing import Dict, Any, List, Tuple
import boto3
import logging
import json
import sys

from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    SystemMessagePromptTemplate,
)
from langchain.agents import OpenAIFunctionsAgent
from langchain.agents import AgentExecutor

from src.get_data import VideoDataRetrievalTool
from src.suggest_edit import SuggestEditTool

# from get_data import VideoDataRetrievalTool
# from suggest_edit import SuggestEditTool


logger = logging.getLogger()
logger.setLevel(logging.INFO)

MODEL = "gpt-4-0613"

SYSTEM_PROMPT = """
You are a helpful AI that is amazing at editing videos. You can edit videos according to the users requests.
You can create themed videos by searching for data that is relevant to the users request.
You can retrieve data about the video. 
    The query is the data that would be relevant to the users request.
    The data is either 'label' data which is the object in the time segments, or 'transcript' data which is the transcript of the segments.
You can also suggest edits the video according to the data and users requests.
    When editing the video you should only refer to the video by the 'video_name'.
    Always use the 'video_name' to refer to the video.
    Always suggest edits when done analyzing the data.
"""


def video_agent(event: Dict[str, Any], context) -> Dict[str, Any]:
    # HACK try is here temporarily to stop retrying on error for now
    try:
        stage = os.environ.get("STAGE", "dev")
        messages_topic_arn = os.environ.get("MESSAGES_TOPIC_ARN")

        # NOTE will always be one record
        record = event["Records"][0]
        body = json.loads(record["body"])
        message = body["message"]
        session = body["session"]
        user_id = session["userId"]
        session_id = session["sessionId"]
        videos = session["videos"]

        logger.info(f"starting handle_message video-ai-{stage}, session: {session_id}, user_id: {user_id}")

        llm = ChatOpenAI(model=MODEL)

        video_data_retrieval_tool = VideoDataRetrievalTool.from_videos(videos)
        suggest_edit_tool = SuggestEditTool.from_session(session)
        tools = [video_data_retrieval_tool, suggest_edit_tool]

        system_prompt = SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT)

        agent = OpenAIFunctionsAgent.from_llm_and_tools(
            llm,
            tools,
            system_message=system_prompt,
        )

        executor = AgentExecutor.from_agent_and_tools(agent, tools, verbose=True)

        output = executor.run({"input": message})
        print(output)
        logger.info(f"agent final output: {output}")

        messages_sns = boto3.client("sns")
        messages_sns.publish(
            TopicArn=messages_topic_arn,
            Message=json.dumps(
                {
                    "userId": user_id,
                    "message": {
                        "action": "agentCompleted",
                        "sessionId": session_id,
                        "output": output,
                    },
                }
            ),
        )

        return output
    except Exception as e:
        print(e)
        logger.error("Error in handle_message", exc_info=True)


# if __name__ == "__main__":
#     from dotenv import load_dotenv
#     import openai

#     load_dotenv()
#     openai.api_key = os.environ["OPENAI_API_KEY"]
#     os.environ["STAGE"] = "dev"
#     event = {
#         "Records": [
#             {
#                 "body": json.dumps(
#                     {
#                         "message": "give me your edit suggestion with timestamps for a video highlighting the animals in the video",
#                         "session": {
#                             "userId": "us-east-1:d0ac9c0c-bd51-4d08-a72c-28cc64993441",
#                             "sessionId": "952f57ba-c6f6-4916-80de-7ff94d7d91fe",
#                             "videos": {
#                                 "71cd3193-d155-49f0-8d58-eb11612f055d": {
#                                     "name": "Travel_Video.mp4",
#                                     "key": "private/us-east-1:d0ac9c0c-bd51-4d08-a72c-28cc64993441/user-videos/Travel_Video.mp4",
#                                     "metadata": {
#                                         "width": "1280",
#                                         "duration": "134.467667",
#                                         "framerate": "24",
#                                         "height": "720",
#                                     },
#                                 }
#                             },
#                         },
#                     }
#                 )
#             }
#         ]
#     }
#     video_agent(event, None)
