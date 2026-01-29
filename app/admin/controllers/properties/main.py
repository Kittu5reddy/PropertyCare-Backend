from app.core.models.property_details import PropertyDetails
from fastapi import APIRouter,HTTPException,Depends
from fastapi.security import OAuth2PasswordBearer
from app.admin.controllers.auth.utils import get_current_admin
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
from app.core.services.db import AsyncSession,get_db
admin_properties=APIRouter(prefix='/admin-properties',tags=['Admin Properties'])
from sqlalchemy import select
from app.core.services.s3 import get_image_cloudfront_signed_url
from jose import JWTError
from app.user.models.users import User
from app.user.models.personal_details import PersonalDetails
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import select, func
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.admin.validators.properties import UpdatePhysicalVerfication,AdminPropertyDetailForm as ChangePropertySchema

@admin_properties.put("/update-property-details")
async def update_property_details(
    payload: ChangePropertySchema,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        # 1️⃣ Authenticate user
        admin = await get_current_admin(token, db)

        # 2️⃣ Fetch property
        result = await db.execute(
            select(PropertyDetails).where(PropertyDetails.property_id == payload.property_id)
        )
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        # 4️⃣ Extract only allowed fields
        update_data = payload.dict(exclude_unset=True)

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")

        allowed_fields = set(PropertyDetails.__table__.columns.keys())

        for key, value in update_data.items():
            if key in allowed_fields:
                setattr(property_obj, key, value)

        # 5️⃣ Commit changes
        await db.commit()
        await db.refresh(property_obj)

        # 6️⃣ Clear Redis cache
        # cache_key = f"property:{property_id}:info"
        # await redis_delete_data(cache_key)

        return {
            "message": "Property details updated successfully",
            "property_id": payload.property_id
        }

    except HTTPException:
        # 👈 Let FastAPI handle it properly
        raise

    except Exception as e:
        print(str(e))
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error while updating property"
        )

@admin_properties.put("/update-physical-verification")
async def update_property_details(
    payload: UpdatePhysicalVerfication,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        # 1️⃣ Authenticate admin
        admin = await get_current_admin(token, db)

        # 2️⃣ Fetch property
        result = await db.execute(
            select(PropertyDetails)
            .where(PropertyDetails.property_id == payload.property_id)
        )
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        # 3️⃣ UPDATE FIELD (THIS WAS THE BUG)
        property_obj.is_verified = payload.is_verified

        # 4️⃣ Commit
        await db.commit()
        await db.refresh(property_obj)

        return {
            "message": f"Physical verification updated to {payload.is_verified}",
            "property_id": payload.property_id
        }

    except HTTPException:
        raise

    except Exception as e:
        print("ERROR:", e)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error while updating property"
        )




@admin_properties.get("/get-properties")
async def get_properties(
    db: AsyncSession = Depends(get_db),
    start: int = 0,
    limit: int = 10
):
    try:
        # 🛑 pagination safety
        if start < 0 or limit <= 0 or limit > 100:
            raise HTTPException(status_code=400, detail="Invalid pagination")

        # ✅ TOTAL COUNT (correct way)
        total_count = await db.scalar(
            select(func.count()).select_from(PropertyDetails)
        )

        # ✅ PAGINATED QUERY
        stmt = (
            select(PropertyDetails)
            .order_by(PropertyDetails.id.desc())
            .offset(start)
            .limit(limit)
        )

        result = await db.execute(stmt)
        properties = result.scalars().all()

        # ✅ async-safe response build
        response = []
        for record in properties:
            image_url = await get_image_cloudfront_signed_url(
                f"/property/{record.property_id}/legal_documents/property_photo.png"
            )

            response.append({
                "image_url": image_url,
                "is_active": record.active_sub,
                "property_id": record.property_id,
                "property_name": record.property_name,
                "user_id": record.user_id
            })

        return {
            "start": start,
            "limit": limit,
            "count": total_count,
            "data": response
        }
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))



@admin_properties.get("/get-user-details")
async def get_user_details(
    user_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
        
    try:
        admin = await get_current_admin(token=token, db=db)
        stmt = await db.execute(
            select(PersonalDetails)
            .where(PersonalDetails.user_id == user_id)
        )

        user = stmt.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User Details Not Found"
            )

        return {
            "user_id": user.user_id,
            "full_name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
            "user_name": user.user_name,
            "contact_number": user.contact_number,
            "location": user.city,
            # ✅ date only
            "member_from": user.created_at.date() if user.created_at else None,
            "nri": user.nri
        }
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))




@admin_properties.get("/get-property-detail")
async def get_property_detail(
    property_id:str,
    # token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),

):
    try:
        # admin = await get_current_admin(token=token, db=db)

        stmt = await db.execute(
            select(PropertyDetails)
            .where(PropertyDetails.property_id == property_id)
        )

        property = stmt.scalar_one_or_none()

        if not property:
            raise HTTPException(
                status_code=404,
                detail="Property Details Not Found"
            )

        return {
            "property_id": property.property_id,
            "plot_number": property.plot_number,
            "name":property.property_name,
            "project_name_or_venture": property.project_name_or_venture,
            "house_number": property.house_number,
            "street": property.street,
            "district": property.district,
            "mandal": property.mandal,
            "city": property.city,
            "pin_code": property.pin_code,
            "facing": property.facing,
            "state": property.state,
            "rental_income": property.rental_income,
            "physical_verification": property.is_verified,
            "type": property.type,
            "sub_type": property.sub_type,
            "scale": property.scale,
            "alternate_name": property.alternate_name,
            "alternate_contact": property.alternate_contact,
            "image_url": await get_image_cloudfront_signed_url(f"/property/{property.property_id}/legal_documents/property_photo.png"),
      
            "is_active": property.active_sub
        }
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))

# user details

 
# prop details

 