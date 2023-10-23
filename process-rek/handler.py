import boto3
import json
import os


def handler(event, context):
    # TODO add checks and error handling

    stage = os.environ["STAGE"]
    rek_client = boto3.client("rekognition")

    print(event)
    # body = json.loads(event["Records"][0]["body"])
    # msg = json.loads(body["Message"])

    # get the job
    # job_id = msg["JobId"]
    # job = rek_client.get_label_detection(JobId=job_id)

    # # update the session table
    # s3_name = job["Video"]["S3Object"]["Name"]
    # video_title = s3_name.split("/")[-1]
    # session_id = s3_name.split("/")[-2]
    # user_id = s3_name.split("/")[-3]
