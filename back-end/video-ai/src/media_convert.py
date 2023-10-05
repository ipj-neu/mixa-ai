from langchain.pydantic_v1 import BaseModel, Field, validator
from typing import Sequence


class InputClipping(BaseModel):
    """The input clipping object (a segment of an input file). Start and end timecodes are in HH:MM:SS:FF format. One of the two must be specified, the other is optional."""

    StartTimecode: str = Field(description="The start timecode of the input clipping. In HH:MM:SS:FF format.")
    EndTimecode: str = Field(description="The end timecode of the input clipping. In HH:MM:SS:FF format.")


class Input(BaseModel):
    """An input video for the job."""

    FileInput: str = Field(..., description="The name of the input file.")
    InputClippings: Sequence[InputClipping] = Field(..., description="The input clippings for the input file.")


class Settings(BaseModel):
    """The settings for cutting a video"""

    Inputs: Sequence[Input] = Field(..., description="The inputs for the job.")


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
