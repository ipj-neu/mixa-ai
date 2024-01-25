import boto3
import logging
import pinecone
import openai
import json
import tiktoken
import requests
import os
import itertools
from uuid import uuid4

"""
JOB_DATA_TYPE = {
    "jobId": "string",
    "jobType": "label, transcribe",
    "videoId": "string",
}

METADATA_TYPE = {
    "video": "videoId",
    "text": "the text embedded",
    "type": "label, transcribe",
    "start": "start time in milliseconds",
    "end": "end time in milliseconds",
}
"""

MAX_TOTAL_TOKENS = 8191
EMBEDDING_MODEL = "text-embedding-ada-002"
SCREEN_TIME_MIN_MILLIS = 1000

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def num_tokens(text):
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def rek_paginate(method, job_id, **kwargs):
    job_config = {"JobId": job_id, **kwargs}
    while True:
        response = method(**job_config)
        yield response
        if response.get("NextToken", "") == "":
            return
        job_config["NextToken"] = response["NextToken"]


def process_rek_labels(job_id, video_id):
    rekognition_client = boto3.client("rekognition")

    labels = []
    for response in rek_paginate(rekognition_client.get_label_detection, job_id, SortBy="NAME", AggregateBy="SEGMENTS"):
        labels.extend(response["Labels"])

    metadata = [[]]
    texts = [[]]
    current_tokens = 0
    for label in labels:
        if label["DurationMillis"] < SCREEN_TIME_MIN_MILLIS:
            continue

        start_time = label["StartTimestampMillis"]
        end_time = label["EndTimestampMillis"]

        obj = label["Label"]
        name = obj["Name"]
        parents = ",".join([parent["Name"] for parent in obj["Parents"]])
        aliases = ",".join([alias["Name"] for alias in obj["Aliases"]])
        categories = ",".join([category["Name"] for category in obj["Categories"]])
        text = ",".join([cat for cat in [name, parents, aliases, categories] if cat != ""])

        tokens = num_tokens(text)
        if tokens + current_tokens > MAX_TOTAL_TOKENS:
            metadata.append([])
            texts.append([])
            current_tokens = 0

        metadata_obj = {
            "video": video_id,
            "text": text,
            "type": "label",
            "start": start_time,
            "end": end_time,
        }
        metadata[-1].append(metadata_obj)
        texts[-1].append(text)

        current_tokens += tokens

    return texts, metadata


def process_transcribe(job_id, video_id):
    transcription_job = boto3.client("transcribe").get_transcription_job(TranscriptionJobName=job_id)
    uri = transcription_job["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
    transcript = requests.get(uri).json()

    items = transcript["results"]["items"]

    metadata = [[]]
    texts = [[]]
    sentence_metadata = {}
    sentence = []
    current_tokens = 0
    for item in items:
        if item["type"] == "punctuation":
            if item["alternatives"][0]["content"] in [".", "?", "!"]:
                text = " ".join(sentence)
                tokens = num_tokens(text)
                if tokens + current_tokens > MAX_TOTAL_TOKENS:
                    metadata.append([])
                    texts.append([])
                    current_tokens = 0

                metadata_obj = {
                    "video": video_id,
                    "text": text,
                    "type": "transcribe",
                    **sentence_metadata,
                }
                print(text)
                print(metadata_obj)

                metadata[-1].append(metadata_obj)
                texts[-1].append(text)

                sentence_metadata.clear()
                sentence.clear()
                current_tokens += tokens
        else:
            sentence.append(item["alternatives"][0]["content"])

            start_time = int(round(float(item["start_time"]) * 1000))
            end_time = int(round(float(item["end_time"]) * 1000))
            if "start" not in sentence_metadata:
                sentence_metadata["start"] = start_time
            sentence_metadata["end"] = end_time

    return texts, metadata


# Code from the Pinecone docs
def chunk(iterable, batch=100):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, batch))
        if not chunk:
            return
        yield chunk


def handler(event, context):
    logger.info("Starting to embed video data")

    pinecone_api_key = os.environ["PINECONE_API_KEY"]
    pinecone_environment = os.environ["PINECONE_ENVIRONMENT"]

    task_token = event["taskToken"]
    video_id = event["videoId"]
    job = event["job"]
    job_id = job["jobId"]
    job_type = job["jobType"]

    processors = {
        "label": process_rek_labels,
        "transcribe": process_transcribe,
    }

    pinecone.init(api_key=pinecone_api_key, environment=pinecone_environment)
    sfn_client = boto3.client("stepfunctions")

    try:
        logger.info(f"Processing job: {job_id}")

        if "videos" not in pinecone.list_indexes():
            raise Exception("Pinecone index not found")
        index = pinecone.Index("videos")

        batched_text, batched_metadata = processors[job_type](job_id, video_id)
        print(f"batched_text: {len(batched_text)}, batched_metadata: {len(batched_metadata)}")

        to_upsert = []
        for texts, metadata in zip(batched_text, batched_metadata):
            # Create embeddings for each text
            print("creating embeddings...")
            response = openai.Embedding.create(input=texts, model=EMBEDDING_MODEL)
            print("created embeddings")
            embeddings = [record["embedding"] for record in response["data"]]

            # Create ids
            ids = [str(uuid4()) for _ in range(len(texts))]

            # Create records
            records = list(zip(ids, embeddings, metadata))
            to_upsert.extend(records)

        # Upsert records
        print("starting upsert...")
        for vectors_chunk in chunk(to_upsert):
            index.upsert(vectors=vectors_chunk)
        print("finished upsert")

        logger.info(f"Finished processing job: {job_id}")

        output = {
            "jobId": job_id,
            "jobType": job_type,
            "videoId": video_id,
        }
        sfn_client.send_task_success(taskToken=task_token, output=json.dumps(output))

    except Exception as e:
        logger.error(f"Error processing: {job_id}", exc_info=True)
        error_output = {"error": f"Error processing {job_type} job: {job_id}"}
        sfn_client.send_task_failure(taskToken=task_token, error=json.dumps(error_output))
