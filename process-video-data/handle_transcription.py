import boto3
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    stage = os.environ["STAGE"]
    try:
        for record in event["Records"]:
            message = json.loads(record["Sns"]["Message"])
            job_id = message["detail"]["TranscriptionJobName"]
            status = message["detail"]["TranscriptionJobStatus"]

            task_token_table_name = f"video-ai-{stage}-transcription-task-token"
            task_token_table = boto3.resource("dynamodb").Table(task_token_table_name)
            sfn_client = boto3.client("stepfunctions")

            task_token = task_token_table.delete_item(Key={"transcribeJobName": job_id}, ReturnValues="ALL_OLD")[
                "Attributes"
            ]["taskToken"]

            output = {"jobId": job_id, "jobType": "transcribe"}

            if status == "FAILED":
                logger.error("Transcription job failed: ", job_id)
                output["errorMessage"] = "Transcription job failed"
                sfn_client.send_task_failure(taskToken=task_token, error=json.dumps(output))
                return

            logger.info(f"Transcription job succeeded: {job_id}")
            sfn_client.send_task_success(taskToken=task_token, output=json.dumps(output))
    except Exception as e:
        logger.error("Error when processing transcription job", exc_info=True)
