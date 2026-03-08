from pydantic import BaseModel


class CreateRequest(BaseModel):
    agent_id: str
    api_url: str
    sk_value: str


class KillRequest(BaseModel):
    agent_id: str


class DeleteRequest(BaseModel):
    agent_id: str


def format_response(success: bool, message: str, data=None):
    return {"success": success, "message": message, "data": data}
