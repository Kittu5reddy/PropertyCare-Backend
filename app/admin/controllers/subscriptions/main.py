from app.core.models.property_details import PropertyDetails
from fastapi import APIRouter,HTTPException,Depends
from fastapi.security import OAuth2PasswordBearer
from app.admin.controllers.auth.utils import get_current_admin
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
from app.core.services.db import AsyncSession,get_db
admin_subscriptions=APIRouter(prefix='/admin-subscriptions',tags=['Admin Subscriptions'])
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
from app.core.models.subscriptions_plans import SubscriptionPlans

@admin_subscriptions.get("/get-subscriptions")
async def get_subscriptions_details(
    type: str,
    # token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        # 🔐 Auth
        # admin = await get_current_admin(token, db)

        # 📦 Fetch plans
        result = await db.execute(
            select(SubscriptionPlans)
            .where(SubscriptionPlans.category.ilike(type))
            .where(SubscriptionPlans.is_active == True)
        )

        plans = result.scalars().all()

        if not plans:
            return {"message": "No subscription plans found"}

        response = []

        for plan in plans:
            response.append({
                "subscription_id": plan.sub_id,
                "subscription_name": plan.sub_type,
                "features": plan.services or [],
                "rental_income_percentage": plan.rental_percentages,
                "prices": plan.durations
            })

        return {
            "status": "success",
            "count": len(response),
            "data": response
        }
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))





# @admin_subscriptions.get("/add-subscription")
# async def get_subscriptions_details(
#     # token: str = Depends(oauth2_scheme),
#     db: AsyncSession = Depends(get_db)
# ):
#     try:
#         # 🔐 Auth
#         # admin = await get_current_admin(token, db)

