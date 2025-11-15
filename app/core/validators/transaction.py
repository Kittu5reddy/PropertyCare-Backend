from pydantic import BaseModel


class Transaction(BaseModel):
    sub_id:str
    duration:int
    property_id:str
    