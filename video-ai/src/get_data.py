from langchain.pydantic_v1 import BaseModel, Field
from typing import Dict, Any, Type
from langchain.tools import BaseTool
import os
from langchain.vectorstores.pinecone import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
import pinecone


class VideoDataRetrievalInput(BaseModel):
    query: str = Field(description="The query to search for the available videos data with")


def convert_milliseconds_to_timecode(milliseconds: float) -> str:
    milliseconds = int(milliseconds)
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


class VideoDataRetrievalTool(BaseTool):
    name = "get_video_data"
    description = "Get relevant data for the videos."
    args_schema: Type[BaseModel] = VideoDataRetrievalInput
    videos: Dict[str, Any] = {}
    store: Pinecone = None

    @classmethod
    def from_videos(cls, videos: Dict[str, Any]) -> "VideoDataRetrievalTool":
        pinecone.init(
            api_key=os.environ["PINECONE_API_KEY"],
            environment=os.environ["PINECONE_ENVIRONMENT"],
        )
        embeddings = OpenAIEmbeddings()
        store = Pinecone.from_existing_index("videos", embeddings)
        return cls(videos=videos, store=store)

    def _run(self, query: str):
        metadata_filer = {
            "video": {"$in": list(self.videos.keys())},
        }

        results = self.store.similarity_search(query, k=50, filter=metadata_filer)

        # Format the results to be easily readable by the AI
        results = "\n".join(
            [
                f"content: {doc.page_content}, data_type: {doc.metadata['type']}, video_name: {self.videos[doc.metadata['video']]['name']}, start_time: {convert_milliseconds_to_timecode(doc.metadata['start'])}, end_time: {convert_milliseconds_to_timecode(doc.metadata['end'])}"
                for doc in results
            ]
        )

        return results
