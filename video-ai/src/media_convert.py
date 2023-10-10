from langchain.pydantic_v1 import BaseModel, Field
from typing import Sequence

# TODO need to look at the rek data because it will shape how this tools input should work
# TODO REWORK THIS
# NOTE OH MY GOD OH MY GOD the audio can be the main input and i can make it generate black video and then overlay many videos on top of it!!!
# works like a charm :) thank goodness i thought of this
# with this technique i can make way more complex videos
# NOTE realizing that this tool would not be the best complex video editing which is fine because the main appeal will be the analysis and the ability to create a job from that
# this needs to be an easy way to create a job based on human input and the rek data
# i can and should really do a lot to keep the output as simply as possible for the ai. the ai should be able to take the human input and the rek data and create a job easily
##############################################
# THINGS IT SHOULD BE ABLE TO FIGURE OUT BASED ON HUMAN OUTPUT
# - the clips from videos the user wants
#   - any clips to be over layed on top of the input video
# - what audio to use and where to put it
# example:
#   vid1: 1:20.33 - 1:30.00
#   vid2: 0:00.00 - 0:10.00
#   vid3: 0:00.00 - 0:10.00
#   aud1: vid1 1:21:00 - vid2 00:05:00 might need to change this. wondering what the user is likely to input


# NOTE data needed for the tool not coming from the ai that the i need to configure the job
# - the frame rate of the input video
# - the height and width (pixels) of the video. potential issue where the over layed videos of different sizes not will be scaled to the size of the input video
#   - could potentially scale all videos when uploaded to the s3 bucket, not great but it would work, more expensive, premium feature??


# NOTE will need to add some info pages to explain how to best use it not matter what i do


# These are typings for the AI to output, will be converted to the correct format for the API in the tool


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
