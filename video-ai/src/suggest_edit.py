import boto3
from typing import Type, Dict, Any, Sequence
import os

from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool


class Timestamp(BaseModel):
    hours: int = Field(description="The hours of the timestamp")
    minutes: int = Field(description="The minutes of the timestamp")
    seconds: int = Field(description="The seconds of the timestamp")
    milliseconds: int = Field(description="The milliseconds of the timestamp")


class Edit(BaseModel):
    videoName: str = Field(description="The name of the video to edit")
    startTime: Timestamp = Field(description="The start time of the edit")
    endTime: Timestamp = Field(description="The end time of the edit")


class SuggestEditInput(BaseModel):
    edits: Sequence[Edit] = Field(description="The edits to suggest")


class SuggestEditTool(BaseTool):
    name = "suggest_edit"
    description = "Suggest an of the video to the user. Always suggest edits when done analyzing the data."
    args_schema: Type[BaseModel] = SuggestEditInput
    session: Dict[str, Any] = {}

    @classmethod
    def from_session(cls, session: Dict[str, Any]) -> "SuggestEditTool":
        return cls(session=session)

    def _run(self, edits: Sequence[Dict[str, Any]]):
        edit_session_table_name = f"video-ai-{os.environ['STAGE']}-edit-session"
        edit_session_table = boto3.resource("dynamodb").Table(edit_session_table_name)
        key = {"sessionId": self.session["sessionId"]}

        for edit in edits:
            edit["videoId"] = next(
                (video_id for video_id, video in self.session["videos"].items() if video["name"] == edit["videoName"]),
                None,
            )
            if edit["videoId"] is None:
                return f"Video {edit['videoName']} not found."

            del edit["videoName"]

        print(f"edits: {edits}")

        edit_session_table.update_item(
            Key=key,
            UpdateExpression="SET currentEdit = list_append(currentEdit, :edit)",
            ExpressionAttributeValues={":edit": [edits]},
        )

        return "Successfully created the edit."
