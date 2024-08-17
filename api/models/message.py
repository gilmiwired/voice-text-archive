from pydantic import BaseModel


class NotionRequest(BaseModel):
    message: str


class NotionResponse(BaseModel):
    response_message: str
