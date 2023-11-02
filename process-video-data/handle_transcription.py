import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    try:
        for record in event["Records"]:
            message = json.loads(record["Sns"]["Message"])
            job_id = message["detail"]["TranscriptionJobName"]
            status = message["detail"]["TranscriptionJobStatus"]

            transcribe_client = boto3.client("transcribe")
            sfn_client = boto3.client("stepfunctions")

            job = transcribe_client.get_transcription_job(TranscriptionJobName=job_id)
            task_token = job["TranscriptionJob"]["Tags"][0]["Value"]
            print("Task Token", task_token)

            output = {"jobId": job_id, "jobType": "transcribe"}

            if status == "FAILED":
                print("Transcription job failed")
                output["errorMessage"] = "Transcription job failed"
                sfn_client.send_task_failure(taskToken=task_token, error=json.dumps(output))
                return

            sfn_client.send_task_success(taskToken=task_token, output=json.dumps(output))
    except Exception as e:
        logger.error("Error when processing transcription job", e, exc_info=True)
