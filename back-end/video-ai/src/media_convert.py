from langchain.pydantic_v1 import BaseModel, Field
from typing import Sequence

# TODO change vim setting to add a scroll offset and change the color of easy motion

# These are typings for the AI to output, will be converted to the correct format for the API in the tool


class Timecode(BaseModel):
    hours: int = Field(..., description="The hours of the timecode")
    minutes: int = Field(..., description="The minutes of the timecode")
    seconds: int = Field(..., description="The seconds of the timecode")
    # SOLUTION need to make a frontend that will allow the user to scroll frame by frame and select a timecode
    # TODO come up with a solution
    # the media convert job needs uses frames instead of milliseconds or other time stamp
    # this might be a problem for the user and/or the ai to figure out so i will leave it out for now
    # frames: int = Field(..., description="The frames of the timecode")


class Clipping(BaseModel):
    start_time: Timecode = Field(..., description="The start time of the clipping. 0 if it is the start of the video")
    end_time: Timecode = Field(..., description="The end time of the clipping. 0 if it is the end of the video")


class Input(BaseModel):
    video_name: str = Field(..., description="The name of the input video")
    input_clipping: Clipping = Field(..., description="The clipping of the input video")
    # this will checked used to find the correct video in the s3 bucket
    video_name: str = Field(..., description="The name of the input video")


"""
the ai need to determine whether it needs to ask clarifying questions or not
first step determine if the request needs any clarifying questions
    ie if the request is vague or not, if the time stamps are not clear
if it does need clarifying questions, then it needs to determine what questions to ask and send it
if it does not need clarifying questions, then it needs to process the request with the tools
    tools:
        sending the actual job to the queue
        probably a tool to do math just in case
        
Component flow:
create a chain that will determine if the request needs clarifying questions
    and create the clarifying question
create an agent with the correct tools
create a runnable map that will run the chain will feed to route the request to the agent or to the clarifying question
    the map will have the agent and a lambda that will set the message to be returned to the user

well fuck they have exactly what i need
"""
