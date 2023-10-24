import boto3
import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    # TODO better error handling
    # need to handle errors so sqs doesn't retry
    try:
        sf_client = boto3.client("stepfunctions")
        rek_client = boto3.client("rekognition")

        # get the job
        body = json.loads(event["Records"][0]["body"])
        message = json.loads(body["Message"])

        status = message["Status"]
        task_token = message["JobTag"]
        job_id = message["JobId"]
        event_name = message["API"]

        print(f"Getting {event_name} job {job_id}")

        if status != "SUCCEEDED":
            output = {
                "jobId": job_id,
                "status": status,
                "jobType": event_name,
                "message": f"Job {event_name} {message['JobId']} failed",
            }
            sf_client.send_task_failure(taskToken=task_token, error=json.dumps(output))
            return

        # TODO update the snf status table
        output = {
            "jobId": job_id,
            "status": status,
            "jobType": event_name,
            "message": f"Job {event_name} {message['JobId']} succeeded",
        }
        sf_client.send_task_success(taskToken=task_token, output=json.dumps(output))
    except Exception as e:
        logger.error("Error: ", exc_info=True)
