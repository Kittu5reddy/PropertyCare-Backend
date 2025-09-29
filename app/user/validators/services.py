from pydantic import BaseModel


class AddService(BaseModel):
    user_id:str
    service_id:str