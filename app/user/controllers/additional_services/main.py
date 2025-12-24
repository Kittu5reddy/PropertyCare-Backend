from fastapi import APIRouter,Depends
from fastapi.security import OAuth2PasswordBearer
from app.core.services.db import AsyncSession,get_db
from app.user.controllers.auth.utils import get_current_user
from .utils import is_additional_services_available,get_property_by_id,has_existing_service,get_last_transaction_count,list_property_by_category,list_all_bookings
from app.user.validators.additional_services import AdditionalServiceCreate 
from app.core.models.additional_services_transactions import  AdditionalServiceTransaction
from app.core.business_logic.ids import generate_service_transaction_id
from fastapi import HTTPException
from jose import JWTError
additional_services=APIRouter(prefix='/additional-services',tags=['additional services'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")




async def get_all_bookings(token:str=Depends(oauth2_scheme),
                            db:AsyncSession=Depends(get_db)):
    try:
        user=await get_current_user(token,db)
        records=await list_all_bookings(user.user_id)
        return records

    except HTTPException as e:
        raise e
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail="Internal server error")



@additional_services.post('/add-additional-service')
async def post_additional_service(
    payload: AdditionalServiceCreate,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_current_user(token, db)

        service = await is_additional_services_available(
            payload.service_id,
            payload.category,
            db
        )

        property = await get_property_by_id(
            property_id=payload.property_id,
            user_id=user.user_id,
            db=db
        )

        if await has_existing_service(
            payload.service_id,
            payload.property_id,
            db
        ):
            raise HTTPException(
                status_code=400,
                detail="Another service request already exists for this property"
            )

        last_count = await get_last_transaction_count(db)
        transaction_id = generate_service_transaction_id(last_count + 1)

        record = AdditionalServiceTransaction(
            transaction_id=transaction_id,
            service_id=payload.service_id,
            property_id=payload.property_id,
            user_id=user.user_id,
            category=payload.category,
            alternate_name=payload.alternate_name,
            alternate_phone=payload.alternate_phone
        )

        db.add(record)
        await db.commit()
        await db.refresh(record)

        return {
            "status": "success",
            "transaction_id": transaction_id
        }

    except HTTPException:
        await db.rollback()
        raise

    except JWTError:
        await db.rollback()
        raise HTTPException(status_code=401, detail="Token expired or invalid")

    except Exception as e:
        await db.rollback()
        print("ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))



@additional_services.get('/list-property-category')
async def get_property_by_category(
                                  category: str,
                                  token:str=Depends(oauth2_scheme),
                                  db:AsyncSession=Depends(get_db)):
    try:
        user=await get_current_user(token,db)
        records=[]
        if category=="BOTH":
            records=await list_property_by_category(user_id=user.user_id,category="PLOT",db=db)
            records+=await list_property_by_category(user_id=user.user_id,category="FLAT",db=db)
        if  category!="BOTH":
            records=await list_property_by_category(user_id=user.user_id,category=category,db=db)
        return records
    except HTTPException as e:
        raise e
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
        