import boto3
import os

"""
DATA_TYPE = {
    "jobType": {"type": "rek, transcribe", "rekType": "label"},
    "videoKey": "string",
    "videoUri": "string",
}
"""


def handler(event, context):
    role_arn = os.environ["REKOGNITION_ROLE_ARN"]
    sns_topic_arn = os.environ["REKOGNITION_TOPIC_ARN"]
    bucket = os.environ["VIDEO_BUCKET"]

    task_token = event["taskToken"]
    job = event["job"]

    job_type = job["jobType"]["rekType"]
    video_key = job["videoKey"]

    job = {
        "JobTag": task_token,
        "Video": {"S3Object": {"Bucket": bucket, "Name": video_key}},
        "NotificationChannel": {"SNSTopicArn": sns_topic_arn, "RoleArn": role_arn},
    }

    rekognition = boto3.client("rekognition")

    print(f"Starting {job_type} job for {video_key.split('/')[-1]})")

    # Use match statement to check job_type
    match job_type:
        case "label":
            rekognition.start_label_detection(**job, MinConfidence=75)
