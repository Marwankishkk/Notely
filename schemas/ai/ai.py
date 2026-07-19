from pydantic import BaseModel


class SummarizeRequest(BaseModel):
    category_id: int


class SummarizeResponse(BaseModel):
    summary: str
