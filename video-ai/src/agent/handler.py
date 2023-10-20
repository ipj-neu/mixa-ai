# to unzip the requirements when deployed to AWS Lambda
try:
    import unzip_requirements  # type: ignore
except ImportError:
    pass

import json
import os
from typing import Dict, Any, List
import boto3
import logging
from media_convert import ToolInput, Input

from langchain.memory import ConversationBufferMemory, DynamoDBChatMessageHistory
from langchain.chat_models import ChatOpenAI
from langchain.prompts import MessagesPlaceholder
from langchain.agents import OpenAIFunctionsAgent
from langchain.tools import Tool
from langchain.agents import AgentExecutor

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# TODO rewrite to fit in the step function
def video_agent(event: Dict[str, Any], context) -> Dict[str, Any]:
    stage = os.environ.get("STAGE", "dev")
    logger.info(f"starting handle_message video-ai-{stage}")

    # all information should always be there except for maybe the message depending on the origin
    user_id = event["userId"]
    session = event["sessionId"]
    message = event.get("message", None)
    origin = event["origin"]

    # NOTE better ways to get the table name
    table_name = f"video-ai-{stage}-chat-sessions"

    if origin == "process_rek":
        # TODO pop the most recent message from the db, and set it as the message
        #   kinda a hacky way to do it but it should work unless I make custom memory, maybe?
        session_table = boto3.resource("dynamodb").Table(table_name)
        pass

    # TODO needs to be made into a tool that inherits from BaseTool and moved to another file
    # will allow conditional return_direct and passing the tool variables from the function instead of relying on scope
    def testing_tool(input: str) -> str:
        return "no information available"

    history = DynamoDBChatMessageHistory(
        table_name=table_name, session_id=session, key={"sessionId": session, "userId": user_id}
    )
    memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=history, return_messages=True)

    llm = ChatOpenAI()
    tools = [
        Tool.from_function(
            name="testing_tool",
            func=testing_tool,
            description="should not be used for anything. exists to test the tool system",
            return_direct=True,
        )
    ]

    agent: OpenAIFunctionsAgent = OpenAIFunctionsAgent.from_llm_and_tools(
        llm=llm, tools=tools, extra_prompt_messages=[MessagesPlaceholder(variable_name="chat_history")]
    )

    executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
    )
    message = executor.run({"input": message})

    # TODO add return to direct the next step in the step function
