import boto3
import os


def start_job(event, context):
    sns_topic_arn = os.environ["REKOGNITION_ROLE_ARN"]
    role_arn = os.environ["REKOGNITION_TOPIC_ARN"]
    bucket = os.environ["VIDEO_BUCKET"]

    job_type = event["type"]
    video_name = event["videoName"]
    task_token = event["taskToken"]

    job = {
        "JobTag": task_token,
        "Video": {"S3Object": {"Bucket": bucket, "Name": video_name}},
        "NotificationChannel": {"SNSTopicArn": sns_topic_arn, "RoleArn": role_arn},
    }

    rekognition = boto3.client("rekognition")

    print(f"Starting {job_type} job for {video_name.split('/')[-1]})")

    if job_type == "label":
        rekognition.start_label_detection(**job)
    elif job_type == "face":
        rekognition.start_face_detection(**job)
