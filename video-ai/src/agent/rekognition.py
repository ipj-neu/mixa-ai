import boto3
from langchain.pydantic_v1 import BaseModel, Field, root_validator
from typing import Sequence, Dict, Any, Type

from enum import Enum

from langchain.tools import BaseTool
from langchain.tools.base import ToolException


class VideoDataTypes(Enum):
    "The types of data that can be gotten from a video. Can only be 'face', 'shot', or 'label'"
    FACE = "face"
    SHOT = "shot"
    LABEL = "label"


class GetVideoDataTool(BaseTool):
    name = "get_video_data"
    description = "Tool to get analysis data from videos."
    args_schema: Type[BaseModel]
    handle_tool_error = True
    videos: Dict[str, Any] = {}

    # NOTE for testing
    return_direct = True

    @classmethod
    def from_videos(cls, videos: Dict[str, Any]) -> "GetVideoDataTool":
        enum_members = {video.replace(".", "_").upper(): video for video in videos.keys()}
        available_videos = Enum("AvailableVideos", enum_members)
        available_videos.__doc__ = "The videos available to get data from"

        class DataRequest(BaseModel):
            video_name: available_videos
            data_type_value: str = Field(
                description="The type of data to get from the video. Must be 'face', 'shot', or 'label'"
            )

            @root_validator
            def validate_data_type(cls, values):
                data_type = values["data_type_value"]
                if data_type not in ["face", "shot", "label"]:
                    raise ValueError({"error": "error here", "message": "message for the user here"})
                return values

            @property
            def data_type(self):
                return VideoDataTypes(self.data_type_value)

        class GetVideoDataInput(BaseModel):
            requests: Sequence[DataRequest] = Field(description="The requests to get data from the video")

        return cls(
            videos=videos,
            args_schema=GetVideoDataInput,
        )

    def return_job_requests(self, missing_data):
        self.return_direct = True
        return {
            "rekJobs": [
                {"type": request.data_type.value, "videoName": self.videos[request.video_name.value]["name"]}
                for request in missing_data
            ],
        }

    def job_paginator(self, job_id, getter, **kwargs):
        job_request = {"JobId": job_id, **kwargs}
        while True:
            response = getter(**job_request)
            yield response
            if response.get("NextToken", "") == "":
                return
            job_request["NextToken"] = response["NextToken"]

    def get_job_results(self, data_request, rek_client=boto3.client("rekognition")):
        getter = None
        formatter = None
        extra_kwargs = {}
        match data_request.data_type.value:
            case "face":
                getter = rek_client.get_face_detection
            case "shot":
                getter = rek_client.get_segment_detection
            case "label":
                getter = rek_client.get_label_detection
                extra_kwargs = {"SortBy": "NAME", "AggregateBy": "SEGMENTS"}
            case _:
                raise ToolException("Invalid data type")

        # TODO format data for gpt and return
        job_id = self.videos[data_request.video_name.value]["availableData"][data_request.data_type.value]
        for response in self.job_paginator(job_id, getter, **extra_kwargs):
            print("response")

    def _run(self, **kwargs) -> Any:
        args = self.args_schema(**kwargs)
        requests = args.requests

        missing_data = list(
            filter(
                lambda request: request.data_type.value
                not in self.videos[request.video_name.value]["availableData"].keys(),
                requests,
            )
        )
        if not missing_data:
            return self.return_job_requests(missing_data)

        rek_client = boto3.client("rekognition")
        for data_request in requests:
            self.get_job_results(data_request, rek_client=rek_client)

        return {"data": "fake data"}
