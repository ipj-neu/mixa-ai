# to unzip the requirements when deployed to AWS Lambda
try:
    import unzip_requirements  # type: ignore
except ImportError:
    pass

import json
import os

import boto3

from langchain.memory.chat_message_histories import DynamoDBChatMessageHistory
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def testing_new(event: dict[str, any], context: dict[str, any]) -> dict[str, any]:
    stage = os.environ.get("STAGE", "dev")
    logger.info(f"Running in stage: {stage}")

    body = json.loads(event.get("body", {}))
    message = body.get("message")
    session = body.get("session")
    table_name = f"video-ai-{stage}-chat-sessions"

    dynamodb = boto3.resource("dynamodb")

    table = dynamodb.Table(table_name)

    response = table.get_item(Key={"SessionId": session})

    if "Item" not in response:
        table.put_item(
            Item={
                "SessionId": session,
                "History": [],
            }
        )

    history = DynamoDBChatMessageHistory(table_name=table_name, session_id=session)
    memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=history, return_messages=True)

    return {
        "statusCode": 500,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": "Not implemented yet"}),
    }


def testing(event: dict[str, any], context: dict[str, any]) -> dict[str, any]:
    stage = os.environ.get("STAGE", "dev")
    logger.info(f"Running in stage: {stage}")

    body = json.loads(event.get("body", {}))
    message = body.get("message")
    session = body.get("session")
    table_name = f"video-ai-{stage}-chat-sessions"

    # this process of checking if the table exists and creating it should not need to happen later in development
    dynamodb = boto3.resource("dynamodb")

    table = dynamodb.Table(table_name)

    response = table.get_item(Key={"SessionId": session})

    if "Item" not in response:
        table.put_item(
            Item={
                "SessionId": session,
                "History": [],
            }
        )

    history = DynamoDBChatMessageHistory(table_name=table_name, session_id=session)
    memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=history, return_messages=True)

    llm = ChatOpenAI()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Your name is Steveo and you are a quirky guy that loves to have funny conversations. You are known to always make puns, but you have some anger issues.",
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ]
    )

    llm_chain = LLMChain(llm=llm, memory=memory, prompt=prompt)

    logger.info(f"Running with message: {message}")
    result = llm_chain.run({"input": message})
    logger.info(f"Result: {result}")

    return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"message": result})}


def on_message(event, context):
    pass
