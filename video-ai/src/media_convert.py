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


class VideoOverlay(BaseModel):
    video_name: str = Field(..., description="The name of the video to overlay")
    # might need an end time, but i think it might just go until the end of the overlay video
    # if end time is required, then it can be calculated based on the length of the overlay video
    # start time needs to also match the start time of the input video so if the start of the input is 00:01:00:00 and the user wants it to start 5 secs into the secs into the clip
    # then the start time of the overlay needs to be 00:01:05:00
    start_time: Timecode = Field(
        ..., description="Where to put the overlay on the underlying video. 0 if it is the start of the video"
    )
    overlay_clippings: Sequence[Clipping] = Field([], description="The clippings of the overlay video, an be empty")


class ImageOverlay(BaseModel):
    # NOTE can add more to this if wanted, like opacity, size, etc
    # TODO might need to add size anyway
    image_name: str = Field(..., description="The name of the image to overlay")
    start_time: Timecode = Field(..., description="Where start the image overlay")
    duration: Timecode = Field(..., description="The duration of the image overlay")


class Input(BaseModel):
    video_name: str = Field(..., description="The name of the input video")
    input_clipping: Clipping = Field(..., description="The clipping of the input video")
    # this will checked used to find the correct video in the s3 bucket
    video_name: str = Field(..., description="The name of the input video")
    # adding multiple audio tracks is supported but can
    use_audio: bool = Field(
        True, description="Whether to use the audio of the input video or not, if not specified it should be true"
    )
    alternate_audio_name: str = Field(
        ..., description="The name of the audio to use if use_audio is false, can be empty"
    )
    video_overlays: Sequence[VideoOverlay] = Field([], description="Videos to overlay on top of input, can be empty")
    image_overlays: Sequence[ImageOverlay] = Field([], description="Images to overlay on top of input, can be empty")


class JobSettings(BaseModel):
    pass


class JobCreationInput(BaseModel):
    setting: JobSettings = Field(..., description="The settings of the job")
