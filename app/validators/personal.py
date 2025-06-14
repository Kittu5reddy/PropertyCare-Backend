from pydantic import BaseModel


class UserDetails(BaseModel):
    first_name:str
    last_name:str
    phone_number:int
    aadhar_number:int
    pan_card:int
    
