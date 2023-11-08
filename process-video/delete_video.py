import boto3
from botocore.exceptions import ClientError
import os
import json
import pinecone
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    stage = os.environ["STAGE"]
    pinecone_api_key = os.environ["PINECONE_API_KEY"]
    pinecone_environment = os.environ["PINECONE_ENVIRONMENT"]
    user_id = event["requestContext"]["authorizer"]["iam"]["cognitoIdentity"]["identityId"]
    params = event.get("pathParameters", "{}")
    if "videoId" not in params:
        return {"statusCode": 400, "body": "videoId is required"}
    video_id = params["videoId"]
    print(user_id)

    # remove video from table if the user owns it
    video_table_name = f"video-ai-{stage}-user-videos"
    video_table = boto3.resource("dynamodb").Table(video_table_name)
    item = None
    try:
        response = video_table.delete_item(
            Key={"videoId": video_id},
            ConditionExpression="userId = :userId",
            ExpressionAttributeValues={":userId": user_id},
            ReturnValues="ALL_OLD",
        )
        item = response.get("Attributes")
    except ClientError as e:
        logger.error("Failed to delete video", exc_info=True)
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {"statusCode": 403, "body": "user does not have access to this video"}
        else:
            raise

    if item is None:
        return {"statusCode": 404, "body": "video not found"}

    # deleting by filter is a payed feature of pinecone and is not available in the free tier
    try:
        # remove video from pinecone index
        pinecone.init(api_key=pinecone_api_key, environment=pinecone_environment)
        index = pinecone.Index(index_name="videos")
        metadata_filter = {"video": item["videoId"]}
        index.delete(filter=metadata_filter)
    except:
        logger.error("Failed to delete video from pinecone", exc_info=True)

    # remove the video from the s3 bucket
    bucket_name = os.environ["VIDEO_BUCKET"]
    s3_client = boto3.client("s3")
    s3_client.delete_object(Bucket=bucket_name, Key=item["key"])

    return "Successfully deleted the video."
