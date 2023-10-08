# to unzip the requirements when deployed to AWS Lambda
try:
    import unzip_requirements  # type: ignore
except ImportError:
    pass

import json
import os
from typing import Dict

import boto3
from pprint import pprint

from langchain.memory.chat_message_histories import DynamoDBChatMessageHistory
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain.agents import OpenAIFunctionsAgent
from langchain.tools import Tool
from langchain.agents import AgentExecutor
from langchain.tools.render import format_tool_to_openai_function

import logging

from src.media_convert import JobSettings, JobCreationInput

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def testing_tool(input_settings: Dict) -> str:
    setting = JobSettings(**input_settings)
    print(type(setting))
    return f"I'll make that for you! It could take a second..."


def handle_message(event, context):
    stage = os.environ.get("STAGE", "dev")
    logger.info(f"Running in stage: {stage}")

    # this is all code for http stuff and will be moved when moved to step function
    body = json.loads(event.get("body", {}))
    message = body.get("message")
    session = body.get("session")
    table_name = f"video-ai-{stage}-chat-sessions"
    user_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]

    # this process of checking if the table exists and creating it should not need to happen later in development
    dynamodb = boto3.resource("dynamodb")

    table = dynamodb.Table(table_name)

    response = table.get_item(Key={"sessionId": session, "userId": user_id})

    if "Item" not in response:
        table.put_item(
            Item={
                "sessionId": session,
                "userId": user_id,
                "History": [],
            }
        )

    history = DynamoDBChatMessageHistory(
        table_name=table_name, session_id=session, key={"sessionId": session, "userId": user_id}
    )
    memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=history, return_messages=True)

    llm = ChatOpenAI()
    tools = [
        Tool.from_function(
            name="create_job",
            func=testing_tool,
            description="testing tool",
            args_schema=JobCreationInput,
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

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": message}),
    }


def blank_lambda(event: dict[str, any], context) -> dict[str, any]:
    pprint(event)
    pprint(context)
    return {
        "statusCode": 500,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": "Not implemented yet"}),
    }


def testing(event: dict[str, any], context) -> dict[str, any]:
    stage = os.environ.get("STAGE", "dev")
    logger.info(f"Running in stage: {stage}")

    # this is all code for http stuff and will be moved when moved to step function
    body = json.loads(event.get("body", {}))
    message = body.get("message")
    session = body.get("session")
    table_name = f"video-ai-{stage}-chat-sessions"
    user_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]

    llm = ChatOpenAI()
    tools = [
        Tool.from_function(
            name="create_job",
            func=testing_tool,
            description="testing tool",
            args_schema=JobCreationInput,
            return_direct=True,
        )
    ]

    agent: OpenAIFunctionsAgent = OpenAIFunctionsAgent.from_llm_and_tools(llm=llm, tools=tools)

    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    message = executor.run(
        {
            "input": "create a job from ThisVid.mp4 from 0:00:00 to 0:00:10 then create a different job for OtherVid.mp4 with timestamps 0:00:30 to 0:00:40"
        }
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": "This is a test function"}),
    }


if __name__ == "__main__":
    tools = [
        Tool.from_function(
            name="create_job",
            func=testing_tool,
            description="testing tool",
            args_schema=JobCreationInput,
            return_direct=True,
        )
    ]
    print(format_tool_to_openai_function(tools[0]))
