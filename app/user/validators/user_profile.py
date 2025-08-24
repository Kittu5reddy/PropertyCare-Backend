from pydantic import BaseModel



class ChangeFirstName(BaseModel):
    first_name:str

class ChangeLastName(BaseModel):
    last_name:str
class ChangeUsername(BaseModel):
    user_name:str
class ChangeContactNumber(BaseModel):
    contact_number:str
class ChangeHouseNumber(BaseModel):
    house_number:str
class ChangeStreet(BaseModel):
    street:str
class ChangeCity(BaseModel):
    city:str
class ChangeState(BaseModel):
    state:str
class ChangePinCode(BaseModel):
    pin_code:int
class ChangeCountry(BaseModel):
    country:str