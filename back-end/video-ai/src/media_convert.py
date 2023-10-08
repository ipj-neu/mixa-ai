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


class JobSettings(BaseModel):
    inputs: Sequence[Input] = Field(..., description="The inputs of the job")


class JobCreationInput(BaseModel):
    setting: JobSettings = Field(..., description="The settings of the job")


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

will use the conversational react agent to do this
conversational agent prompt can be modified to tell it when to ask clarifying questions
    need to look into what open ai function agent does, potentially has better output than the conversational agent and maybe more control
looking into the code, the open ai function agent does what i want
    it can use multi input tools and is a lot more customizable
    the conversation part of asking follow up question can be done with a tool that will send the message to the user and memory
tools have a field to stop the agent and return
the ai can call for the rek stuff if not available, the step function will call the job creation then call the agent lambda again.
    should probably not store it and create embeddings
        a stretch goal could be to create a vector database of rek results that the ai can query
        might not be that much of an improvement over just formatting the rek results and sending it to the tool
        the rek tool should be an ai that the formatted data gets sent to and processed into something the agent can turn into a convert job

the step function could be triggered by http directly or by a lambda that is triggered by http
    the lambda would probably be better because it can do some error checking, formatting, and auth before sending it to the step function
does the new messages need to be added to a queue to be processed by the step function?
    this might be unnecessary complexity because the step function can scale
step function:
needs the message sent by the user, the session id (chat id), and the user id (maybe more info about the user)
first it needs to determine where the request came from (lambda or the recall from the rek job)
if call is directly from the user, send to the agent the agent lambda
    - the agent can send it back to the user if it needs clarifying questions (conditions to ask clarifying questions can be added to the prompt)
    - request the rek info if it needs it and if not available creates the job and sends it back to the agent lambda when rek job is finished
        need to figure out how to set the waiting for completion and calling the agent lambda again
        needs to send updates to the user about what its doing so the user doesn't just sit there waiting
    - create a convert job from all available info and send it to the queue
if the call is from the rek job it can do all of the things above except it needs to remove the previous user message and ask it again given the new info from the rek job
    unless it keeps track of it's thought process and can just be told to continue from where it left off
    would need to remove the continue message from the db history
"""
