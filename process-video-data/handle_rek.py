import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    try:
        sf_client = boto3.client("stepfunctions")

        # get the job
        for record in event["Records"]:
            body = json.loads(record["body"])
            message = json.loads(body["Message"])

            status = message["Status"]
            task_token = message["JobTag"]
            job_id = message["JobId"]
            event_name = message["API"]
            job_type = event_name.removeprefix("Start").removesuffix("Detection").lower()

            output = {
                "jobId": job_id,
                "jobType": "rek",
                "rekType": job_type,
            }

            if status != "SUCCEEDED":
                output["errorMessage"] = f"{job_type} Rekognition job failed"
                sf_client.send_task_failure(taskToken=task_token, error=json.dumps(output))
                return

            sf_client.send_task_success(taskToken=task_token, output=json.dumps(output))

    except Exception as e:
        logger.error("Error when processing rekognition job", e, exc_info=True)
