import boto3
import os

"""
DATA_TYPE = {
    "jobType": {"type": "rek, transcribe", "rekType": "label"},
    "videoKey": "string",
    "videoUri": "string",
    "videoId": "string",
}
"""


def send_transcribe_job(job, task_token):
    stage = os.environ["STAGE"]

    video_uri = job["videoUri"]
    video_id = job["videoId"]

    transcribe = boto3.client("transcribe")
    task_token_table = boto3.resource("dynamodb").Table(f"video-ai-{stage}-transcription-task-token")

    task_token_table.put_item(Item={"transcribeJobName": video_id, "taskToken": task_token})

    job = {
        "TranscriptionJobName": video_id,
        "LanguageCode": "en-US",
        "Media": {"MediaFileUri": video_uri},
    }

    transcribe.start_transcription_job(**job)


def send_rek_job(job, task_token):
    role_arn = os.environ["REKOGNITION_ROLE_ARN"]
    sns_topic_arn = os.environ["REKOGNITION_TOPIC_ARN"]
    bucket = os.environ["VIDEO_BUCKET"]

    job_type = job["jobType"]["rekType"]
    video_key = job["videoKey"]

    job = {
        "JobTag": task_token,
        "Video": {"S3Object": {"Bucket": bucket, "Name": video_key}},
        "NotificationChannel": {"SNSTopicArn": sns_topic_arn, "RoleArn": role_arn},
    }

    rekognition = boto3.client("rekognition")

    print(f"Starting {job_type} job for {video_key.split('/')[-1]})")

    match job_type:
        case "label":
            rekognition.start_label_detection(**job, MinConfidence=75)
        case _:
            raise ValueError("Invalid rekognition job type")


def handler(event, context):
    task_token = event["taskToken"]
    job = event["job"]

    match job["jobType"]["type"]:
        case "transcribe":
            send_transcribe_job(job, task_token)
        case "rek":
            send_rek_job(job, task_token)
        case _:
            raise ValueError("Invalid job type")
