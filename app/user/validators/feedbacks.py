from pydantic import BaseModel


class FeedBack(BaseModel):
    user_id:str
    property_id:str
    category:str  
    stars:int  
    comment:str
