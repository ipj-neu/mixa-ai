from langchain.pydantic_v1 import BaseModel, Field
from typing import Sequence


class Timecode(BaseModel):
    hours: int = Field(..., description="The hours of the timecode")
    minutes: int = Field(..., description="The minutes of the timecode")
    seconds: int = Field(..., description="The seconds of the timecode")
    # the frame rate will be stored in the chat db and can be used to convert the timecode to milliseconds
    milliseconds: int = Field(..., description="The milliseconds of the timecode")


class Clipping(BaseModel):
    start_time: Timecode = Field(..., description="The start time of the clipping. 0 if it is the start of the video")
    end_time: Timecode = Field(..., description="The end time of the clipping. 0 if it is the end of the video")


class Input(BaseModel):
    video_name: str = Field(..., description="The name of the input video")
    input_clipping: Clipping = Field(..., description="The clipping of the input video")


class ToolInput(BaseModel):
    inputs: Sequence[Input] = Field(..., description="The inputs to the job")
