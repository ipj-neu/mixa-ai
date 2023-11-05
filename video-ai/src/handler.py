# to unzip the requirements when deployed to AWS Lambda
try:
    import unzip_requirements  # type: ignore
except ImportError:
    pass

import os
from typing import Dict, Any, List, Tuple
import boto3
import logging

from langchain.memory import ConversationBufferMemory, DynamoDBChatMessageHistory, ReadOnlySharedMemory
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate,
)
from langchain.agents import OpenAIFunctionsAgent
from langchain.tools import BaseTool
from langchain.tools.render import format_tool_to_openai_function
from langchain.agents import AgentExecutor
from langchain.schema.agent import AgentAction, AgentActionMessageLog

from media_convert import MediaConvertTool
from rekognition import GetVideoDataTool

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def random_test(agent_actions: List[Tuple[AgentAction, str]]) -> List[Tuple[AgentAction, str]]:
    print(agent_actions)
    return agent_actions


class TestingTool(BaseTool):
    name = "testing_tool"
    description = "testing tool do not use"

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def _arun(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


def video_agent(event: Dict[str, Any], context) -> Dict[str, Any]:
    stage = os.environ.get("STAGE", "dev")

    user_id = event["userId"]
    session = event["sessionId"]
    message = event["message"]
    origin = event["origin"]

    logger.info(f"starting handle_message video-ai-{stage}, session: {session}, user_id: {user_id}")

    # NOTE better ways to get the table names
    videos_table_name = f"video-ai-{stage}-chat-sessions-videos"

    videos_table = boto3.resource("dynamodb").Table(videos_table_name)
    response = videos_table.get_item(Key={"sessionId": session, "userId": user_id})
    if "Item" not in response:
        raise Exception("No videos found for this session")
    videos: Dict[str, Any] = response["Item"]["videos"]

    logger.info(f"message: {message}")

    llm = ChatOpenAI(model="gpt-3.5-turbo-0613")
    media_convert_tool = MediaConvertTool.from_videos(videos)
    rekognition_tool = GetVideoDataTool.from_videos(videos)

    tools = [media_convert_tool, rekognition_tool]

    system_prompt = SystemMessagePromptTemplate.from_template(
        f"You are a helpful AI assistant that is amazing at editing videos.\nContext: You have the following videos that you can use {', '.join(list(videos.keys()))}\nThe only valid data type for video data are 'label', 'face', and 'shot'"
    )

    agent = OpenAIFunctionsAgent.from_llm_and_tools(
        llm,
        tools,
        system_message=system_prompt,
    )

    executor = AgentExecutor.from_agent_and_tools(agent, tools, verbose=True)
    # executor.trim_intermediate_steps = random_test
    # executor.return_intermediate_steps = True

    output = executor.run({"input": message})
    print(output)
    logger.info(f"agent final output: {output}")
    return output
