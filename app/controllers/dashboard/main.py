from fastapi import APIRouter,Depends
from app.controllers.auth.main import oauth2_scheme
from app.controllers.forms.utils import get_image



from app.models import AsyncSession,get_db
dash=APIRouter(prefix='/dash',tags=['/dash'])

@dash.get('/property-details')
async def get_property_data(token:str=Depends(oauth2_scheme),db:AsyncSession=Depends(get_db)):
    # user = await get_current_user(token,db)
    data=[ 
        {
        "property_id":"10202",
        "name":"Srikanth Nilayam",
        "type":"resenditial",
        "area":"300sqward",
        "img_url":get_image('/user/demo/srikanth_nilayam/3.jpg')
    },
        {
        "property_id":"10222",
        "name":"Sangamesh Nilayam",
        "type":"resenditial",
        "area":"300sqward",
        "img_url":get_image('/user/demo/sangamesh_nilayam/2.jpg')
    },
        {
        "property_id":"10202",
        "name":"Appurva Nilayam",
        "type":"resenditial",
        "area":"300sqward",
        "img_url":get_image('/user/demo/appurva_nilayam/1.jpg')
    },
        {
        "property_id":"10202",
        "name":"Uppal Plot",
        "type":"resenditial",
        "area":"300sqward",
        "img_url":get_image('/user/demo/uppal_plot/3.jpg')
    }
    ]
    # print(data)
    return data



@dash.get('/monthly-photos')
async def get_property_data(token:str=Depends(oauth2_scheme),db:AsyncSession=Depends(get_db)):
    # user = await get_current_user(token,db)
    data=[ 
        {
        "property_id":"10202",
        "date":"JUNE 21, 2025",
        "name":"srikanth Nilayam",
        "type":"resenditial",
        "area":"300sqward",
        "img_url":get_image('/user/demo/srikanth_nilayam/3.jpg')
    },
        {
        "property_id":"10222",
        "name":"Sangamesh Nilayam",
       "date":"JUNE 21, 2025",
       
        "type":"resenditial",
        "area":"300sqward",
        "img_url":get_image('/user/demo/sangamesh_nilayam/2.jpg')
    },
        {
        "property_id":"10202",
        "name":"Appurva Nilayam",
        "date":"NOV 24, 2023",
        "type":"resenditial",
        "area":"300sqward",
        "img_url":get_image('/user/demo/appurva_nilayam/1.jpg')
    },
        {
        "property_id":"10202",
        "name":"Uppal Plot",
        "type":"Open-Plotz  ",
        "date":"JUNE 05, 2020",
        "area":"300sqward",
        "img_url":get_image('/user/demo/uppal_plot/3.jpg')
    }
    ]
    # print(data)
    return data