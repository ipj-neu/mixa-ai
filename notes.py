# do i need a chat history for the ai?
# would it better to make it more like bing dall-e where it's not chat based, instead of trying to emulate gpt


# might need to add a way for the user to prefetch the rek data they want

# i feel like i am doing this backwards, i should be making it able to do the rek stuff, i think that is what is cool about this
# SCRATCH ALL OF THIS, starting from making a tool that can take multiple inputs and make themed short form videos like i wanted to in the first place
#   a tool ai chat based tool is cool but not what i thought would be cool
#   basic video editing skills are enough


# TODO need to look at the rek data because it will shape how this tools input should work
#   rek data will work fine with whatever i think
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

# NOTE because tool is meant to be used with natural language i keep thinking that it should be able to handle any input
#   which actually might be true, i don't think that i am trusting the ai enough, given the right tools it should be able to handle any input
#   the issue is how do i make a tools design that will allow it to handle any input? that is where the trust comes in and i need to trust that the ai will be able to handle it
#   for now i wll make a tool as i think it should be used and then the ai can pull the rest of the weight

# NOTE data needed for the tool not coming from the ai that the i need to configure the job
# - the frame rate of the input video
# - the height and width (pixels) of the video. potential issue where the over layed videos of different sizes not will be scaled to the size of the input video
#   - could potentially scale all videos when uploaded to the s3 bucket, not great but it would work, more expensive, premium feature??

# TODO there are a couple of ways i can do this stuff because the rek data contains the height, width, and frame rate of the video
#   because of this there are a couple of ways i can do this. the only difference is cost and complexity
#   especially when it comes to my resolution issue
#   having different resolutions could be a premium feature
#   also do i want to have the video analyzed when uploaded or do my own analysis when uploaded


# NOTE will need to add some info pages to explain how to best use it not matter what i do


# These are typings for the AI to output, will be converted to the correct format for the API in the tool


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
