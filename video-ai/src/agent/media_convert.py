from langchain.pydantic_v1 import BaseModel, Field, validator
from typing import Sequence, Dict, Any, Type
from langchain.tools import BaseTool
from langchain.callbacks.human import HumanApprovalCallbackHandler
import boto3
from decimal import Decimal


class Timecode(BaseModel):
    hours: int = Field(description="The hours of the timecode")
    minutes: int = Field(description="The minutes of the timecode")
    seconds: int = Field(description="The seconds of the timecode")
    # the frame rate will be stored in the chat db and can be used to convert the timecode to milliseconds
    milliseconds: int = Field(description="The milliseconds of the timecode")

    def milliseconds_to_frames(self, frame_rate: Decimal) -> int:
        return round((self.milliseconds / 1000) * float(frame_rate))

    def convert_timecode(self, frame_rate: Decimal) -> str:
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}:{self.milliseconds_to_frames(frame_rate):02d}"


class Clipping(BaseModel):
    start_time: Timecode = Field(description="The start time of the clipping.")
    end_time: Timecode = Field(description="The end time of the clipping.")


class Input(BaseModel):
    video_name: str = Field(description="The name of the input video")
    input_clipping: Clipping = Field(description="The clipping of the input video")
    use_full_video: bool = Field(default=False, description="If the full video should be used instead of the clipping")


class ToolInput(BaseModel):
    inputs: Sequence[Input] = Field(description="The inputs to the job")


class MediaConvertTool(BaseTool):
    name = "edit_video"
    description = "Tool to edit a video. Can take multiple input videos and/or video clips and put them together."
    args_schema: Type[BaseModel] = ToolInput
    videos: Dict[str, Any] = {}

    # NOTE for testing
    return_direct = True

    def _run(self, inputs):
        inputs: Sequence[Input] = [Input(**clipping) for clipping in inputs]
        incorrect_inputs = []
        for clipping in inputs:
            if clipping.video_name not in self.videos:
                incorrect_inputs.append(clipping.video_name)
        if incorrect_inputs:
            self.return_direct = True
            return {
                "status": "error",
                "message": f"Could not find the video(s) {', '.join(incorrect_inputs)}. Make sure the names match one of these {', '.join(list(self.videos.keys()))}",
            }

        media_convert_client = boto3.client(
            "mediaconvert", endpoint_url="https://vasjpylpa.mediaconvert.us-east-1.amazonaws.com"
        )

        job = {
            "Settings": {
                "Inputs": [],
                "OutputGroups": [
                    {
                        "Name": "File Group",
                        "OutputGroupSettings": {
                            "Type": "FILE_GROUP_SETTINGS",
                            "FileGroupSettings": {
                                "Destination": "s3://video-ai-videos-dev/private/us-east-1:d0ac9c0c-bd51-4d08-a72c-28cc64993441/84c81408-2091-7017-9115-d5882b7deeed/testing_session/new_video"
                            },
                        },
                        "Outputs": [
                            {
                                "VideoDescription": {
                                    "CodecSettings": {
                                        "Codec": "H_264",
                                        "H264Settings": {
                                            "RateControlMode": "QVBR",
                                            "SceneChangeDetect": "TRANSITION_DETECTION",
                                            "FramerateControl": "SPECIFIED",
                                            "FramerateNumerator": 30,
                                            "FramerateDenominator": 1,
                                            "MaxBitrate": 5000000,
                                        },
                                    },
                                    "Width": 720,
                                    "Height": 480,
                                },
                                "AudioDescriptions": [
                                    {
                                        "CodecSettings": {
                                            "Codec": "AAC",
                                            "AacSettings": {
                                                "Bitrate": 96000,
                                                "CodingMode": "CODING_MODE_2_0",
                                                "SampleRate": 48000,
                                            },
                                        },
                                        "AudioSourceName": "Audio Selector 1",
                                    }
                                ],
                                "ContainerSettings": {"Container": "MP4", "Mp4Settings": {}},
                            }
                        ],
                    }
                ],
                "TimecodeConfig": {"Source": "ZEROBASED"},
            },
            # TODO change this to the arn given in the environment variables
            "Role": "arn:aws:iam::956782569109:role/MediaConvertRole",
        }

        for clipping in inputs:
            input_config = {
                "TimecodeSource": "ZEROBASED",
                "AudioSelectors": {"Audio Selector 1": {"DefaultSelection": "NOT_DEFAULT"}},
                "FileInput": f"s3://video-ai-videos-dev/{self.videos[clipping.video_name]['name']}",
            }
            if not clipping.use_full_video:
                frame_rate = self.videos[clipping.video_name]["metadata"]["framerate"]
                input_config["InputClippings"] = [
                    {
                        "StartTimecode": clipping.input_clipping.start_time.convert_timecode(frame_rate),
                        "EndTimecode": clipping.input_clipping.end_time.convert_timecode(frame_rate),
                    }
                ]
            job["Settings"]["Inputs"].append(input_config)

        media_convert_client.create_job(**job)

        return {"message": "Job created.", "convertJob": job}
