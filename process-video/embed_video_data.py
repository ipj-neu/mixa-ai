import boto3
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    logger.info("Starting to embed video data")
    logger.info(event)
