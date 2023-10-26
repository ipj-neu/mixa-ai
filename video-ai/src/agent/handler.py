# to unzip the requirements when deployed to AWS Lambda
try:
    import unzip_requirements  # type: ignore
except ImportError:
    pass

import os
from typing import Dict, Any, List
import boto3
import logging

from langchain.memory import ConversationBufferMemory, DynamoDBChatMessageHistory
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import MessagesPlaceholder, SystemMessagePromptTemplate
from langchain.agents import OpenAIFunctionsAgent
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class TestingTool(BaseTool):
    name = "testing_tool"
    description = "testing tool do not use"

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def _arun(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


def video_agent(event: Dict[str, Any], context) -> Dict[str, Any]:
    stage = os.environ.get("STAGE", "dev")
    logger.info(f"starting handle_message video-ai-{stage}")

    # all information should always be there except for maybe the message depending on the origin
    user_id = event["userId"]
    session = event["sessionId"]
    message = event.get("message", None)
    origin = event["origin"]

    # NOTE better ways to get the table name
    table_name = f"video-ai-{stage}-chat-sessions-history"

    history = DynamoDBChatMessageHistory(
        table_name=table_name, session_id=session, key={"sessionId": session, "userId": user_id}
    )

    # NOTE might need to add more origins, this is the only one rn that needs to be handled differently
    if origin == "fetch_rek":
        message_history = history.messages
        session_table = boto3.resource("dynamodb").Table(table_name)
        response = session_table.update_item(
            Key={"sessionId": session, "userId": user_id},
            UpdateExpression=f"REMOVE History[{len(message_history) - 2}], History[{len(message_history) - 1}]",
            ReturnValues="UPDATED_OLD",
        )
        message = response["Attributes"]["History"][0]["data"]["content"]
    logger.info(f"message: {message}")

    memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=history, return_messages=True)
    # TODO set temp of ai. want it to be low enough to use the tools correctly, but high enough create good videos.
    llm = ChatOpenAI()
    # TODO define tools in other file
    tools = [TestingTool()]

    # TODO create better prompts for the agent
    #   system prompt needs work
    agent = OpenAIFunctionsAgent.from_llm_and_tools(
        llm,
        tools,
        system_message=SystemMessagePromptTemplate.from_template(
            "You are a helpful AI assistant that is amazing at editing videos."
        ),
        extra_prompt_messages=[MessagesPlaceholder(variable_name="chat_history")],
    )

    executor = AgentExecutor.from_agent_and_tools(agent, tools, memory=memory, verbose=True)

    output = executor.run({"input": message})
    logger.info(f"agent final output: {output}")
