import pinecone
import os


def handler(event, context):
    pinecone_api_key = os.environ["PINECONE_API_KEY"]
    pinecone_environment = os.environ["PINECONE_ENVIRONMENT"]
    video_id = event["videoId"]

    pinecone.init(api_key=pinecone_api_key, environment=pinecone_environment)

    output = {"videoId": video_id}

    if video_id not in pinecone.list_indexes():
        output["message"] = "creating index"
        pinecone.create_index(name=video_id, dimension=1536, metric="cosine")
    else:
        output["message"] = "index already exists"

    return output
