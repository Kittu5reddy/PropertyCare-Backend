from .utils import PropertyDetails
from fastapi import APIRouter,Depends,HTTPException
from app.core.models import AsyncSession,get_db
from app.core.controllers.auth.main import oauth2_scheme
from app.core.controllers.auth.utils import get_current_user
from sqlalchemy import select
from app.user.controllers.properties.utils import check_property_access
from app.user.controllers.forms.utils import get_image
from app.user.validators.transactionsuboffline import TransactionSubOffline as TransactionSubOfflineSchema
from app.core.models.subscriptions_transaction_offline import TransactionSubOffline
from app.core.models.subscriptions_plans import SubscriptionPlans
subscriptions=APIRouter(prefix='/subscriptions',tags=['subscriptions'])
from datetime import datetime
import uuid 
@subscriptions.get("/get-properties")
async def get_properties(
    category: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Fetch properties of a specific category for the logged-in user."""

    try:
        user = await get_current_user(token, db)
        # Query all matching properties
        result = await db.execute(
            select(PropertyDetails).where(PropertyDetails.type == category.lower())
        )
        properties = result.scalars().all()

        if not properties:
            raise HTTPException(
                status_code=404,
                detail=f"No properties found for category '{category}'."
            )

        return {
            "user_id": user.user_id,
            "count": len(properties),
            "properties": [
                {
                    "property_id": p.property_id,
                    "property_name": p.property_name,
                    "type": p.type,
                    "city": p.city,
                    "state": p.state,
                    "property_image_url":get_image(f'/property/{ p.property_id}/legal_documents/property_photo.png')
                }
                for p in properties
            ],
        }

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=401,
            detail=f"Failed to fetch properties: {str(e)}"
        )
    




@subscriptions.post("/add-offline-subscriptions")
async def add_offline_subscriptions(
    payload: TransactionSubOfflineSchema,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    Add an offline subscription transaction (cash, cheque, UPI, etc.)
    """
    try:
        # 1️⃣ Validate and get current user
        user = await get_current_user(token, db)

        # 2️⃣ Validate property ownership/access
        result = await db.execute(
            select(PropertyDetails).where(PropertyDetails.property_id == payload.property_id)
        )
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        # ✅ Correct: block only non-owners
        if property_obj.user_id != user.user_id:
            raise HTTPException(status_code=403, detail="You are not the owner of this property")

        # 3️⃣ Validate subscription plan
        sub_query = await db.execute(
            select(SubscriptionPlans).where(SubscriptionPlans.sub_id == payload.sub_id)
        )
        sub = sub_query.scalar_one_or_none()

        if not sub:
            raise HTTPException(status_code=404, detail="Subscription plan not found")
        existing_txn = await db.execute(
                                        select(TransactionSubOffline).where(
                                        TransactionSubOffline.payment_transaction_number == payload.payment_transaction_number
                                        )
                                        )
        if existing_txn.scalar_one_or_none():
            raise HTTPException(
        status_code=400,
        detail=f"Payment reference '{payload.payment_transaction_number}' already exists. Please use a unique reference."
        )
        # 4️⃣ Generate unique transaction_id if not provided
        transaction_id = (
            payload.transaction_id if getattr(payload, 'transaction_id', None) else f"TXOFF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        )

        # 5️⃣ Create ORM record
        record = TransactionSubOffline(
            user_id=user.user_id,
            property_id=payload.property_id,
            sub_id=payload.sub_id,
            transaction_id=transaction_id,
            cost=payload.cost,  # use cost from payload
            payment_method=payload.payment_method,
            payment_transaction_number=payload.payment_transaction_number,
            status=payload.status or "PENDING",
        )

        # 6️⃣ Save to DB
        db.add(record)
        await db.commit()
        await db.refresh(record)

        # 7️⃣ Return success response
        return {
            "message": "Offline subscription transaction created successfully.",
            "transaction_id": transaction_id,
            "status": record.status,
            "amount": str(record.cost),
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error while creating offline transaction: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add offline subscription: {str(e)}"
        )
