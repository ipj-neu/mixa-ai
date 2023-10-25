import boto3
import os


def start_job(event, context):
    # TODO need to send an update to the status table here
    print(event)
    role_arn = os.environ["REKOGNITION_ROLE_ARN"]
    sns_topic_arn = os.environ["REKOGNITION_TOPIC_ARN"]
    bucket = os.environ["VIDEO_BUCKET"]

    task_token = event["taskToken"]
    job = event["job"]

    job_type = job["type"]
    video_name = job["videoName"]

    job = {
        "JobTag": task_token,
        "Video": {"S3Object": {"Bucket": bucket, "Name": video_name}},
        "NotificationChannel": {"SNSTopicArn": sns_topic_arn, "RoleArn": role_arn},
    }

    rekognition = boto3.client("rekognition")

    print(f"Starting {job_type} job for {video_name.split('/')[-1]})")

    # Use match statement to check job_type
    match job_type:
        case "label":
            rekognition.start_label_detection(**job)
        case "face":
            rekognition.start_face_detection(**job)
        case "segment":
            rekognition.start_segment_detection(**job, SegmentTypes=["SHOT"])
