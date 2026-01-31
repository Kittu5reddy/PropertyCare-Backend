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
from app.core.models.subscriptions import Subscriptions
from app.admin.validators.subscriptions import AddSubscription,AddPlan

from datetime import datetime

from sqlalchemy import asc
from datetime import datetime
from sqlalchemy import asc
from fastapi import HTTPException

@admin_subscriptions.get("/get-next-available-date")
async def get_next_available_date(
    property_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        # 🔐 Auth
        admin = await get_current_admin(token, db)

        result = await db.execute(
            select(Subscriptions)
            .where(
                Subscriptions.property_id == property_id,
                Subscriptions.is_active == True
            )
            .order_by(asc(Subscriptions.sub_end_date))
            .limit(1)
        )

        subscription = result.scalar_one_or_none()

        # No active subscription → available today
        if not subscription:
            today = datetime.today().date()
            return {
                "property_id": property_id,
                "next_available_date": today.strftime("%d-%m-%Y"),
                "message": "No active subscription"
            }

        next_date = subscription.sub_end_date.date()

        return {
            "property_id": property_id,
            "next_available_date": next_date.strftime("%d-%m-%Y"),
            "message": "Next available date"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@admin_subscriptions.get("/get-subscriptions")
async def get_subscriptions_details(
    type: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        # 🔐 Auth
        admin = await get_current_admin(token, db)

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
from decimal import Decimal



from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from dateutil.relativedelta import relativedelta


@admin_subscriptions.post("/add-subscription")
async def add_subscription(
    payload: AddSubscription,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        # 🔐 Auth (optional)
        admin = await get_current_admin(token, db)

        # 📦 Check existing active subscription
        smt = await db.execute(
            select(Subscriptions)
            .where(
                Subscriptions.property_id == payload.property_id,
                Subscriptions.is_active == True
            )
        )
        existing = smt.scalar_one_or_none()
        if existing and existing.sub_end_date.date() > payload.start_date:
            
            raise HTTPException(
    status_code=403,
    detail=f"Existing subscription upto {existing.sub_end_date.date().strftime('%d-%m-%Y')}"
)



        # 📦 Fetch subscription plan
        result = await db.execute(
            select(SubscriptionPlans)
            .where(
                SubscriptionPlans.sub_id == payload.subscription_id,
                SubscriptionPlans.is_active == True
            )
        )
        sub = result.scalar_one_or_none()

        if not sub:
            raise HTTPException(status_code=404, detail="Subscription plan not found")

        # 🏠 Fetch property
        result = await db.execute(
            select(PropertyDetails)
            .where(
                PropertyDetails.property_id == payload.property_id,
                PropertyDetails.user_id == payload.user_id
            )
        )
        property = result.scalar_one_or_none()

        if not property:
            raise HTTPException(status_code=404, detail="Property not found")

        if not property.is_verified:
            raise HTTPException(status_code=403, detail="Property is not verified")

        # ❗ Validate property vs plan
        if str(property.type).upper() != str(sub.category).upper():
            raise HTTPException(
                status_code=400,
                detail="Subscription plan not valid for this property type"
            )

        # 👤 Fetch user
        result = await db.execute(
            select(User).where(User.user_id == payload.user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 📅 Calculate end date
        sub_end_date = payload.start_date + relativedelta(months=payload.duration)

        # 💰 Calculate amount (Decimal-safe)
        duration_amount = Decimal(str(sub.durations[str(payload.duration)]))
        baesd_on="PLAN" # plan
        if str(property.type).upper() == "FLAT":
            weekly_income = property.rental_income * Decimal("0.07")
            if weekly_income>=duration_amount:
                amount=weekly_income
                baesd_on="RENTAL" # based on rental income

        else:
            if property.size < 400:
                amount = duration_amount
            else:
                extra_units = property.size // 400
                amount = duration_amount + (Decimal(extra_units) * Decimal("1000"))

        # 🧾 Create subscription
        new_record = Subscriptions(
            # admin_id="ADMIN001",  # replace with real admin later
            admin_id=admin.admin_id,
            user_id=user.user_id,
            sub_id=sub.sub_id,
            property_id=property.property_id,
            sub_name=sub.sub_type,
            services=sub.services,
            sub_start_date=payload.start_date,
            sub_end_date=sub_end_date,
            durations=payload.duration,
            amount=amount,
            baesd_on=baesd_on,
            payment_method=payload.payment_method,
            comment=payload.comment,
            is_active=True
        )

        # 🔄 Update property
        property.active_sub = True

        # 💾 Save everything
        db.add(new_record)
        await db.commit()
        await db.refresh(new_record)

        return {
            "status": "success",
            "subscription_id": new_record.id,
            "message": "Subscription added successfully"
        }

    except HTTPException:
        raise
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




                     
                     
async def send_plans(payload:AddPlan,
                     token:str=Depends(oauth2_scheme),
                     db:AsyncSession=Depends(get_db)):
    try:
        admin=await get_current_admin(token,db)
        
    except:
        pass