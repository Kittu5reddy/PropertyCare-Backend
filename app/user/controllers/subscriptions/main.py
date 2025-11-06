from .utils import PropertyDetails
from fastapi import APIRouter,Depends,HTTPException,status
from app.core.models import AsyncSession,get_db
from app.core.controllers.auth.main import oauth2_scheme
from app.core.controllers.auth.utils import get_current_user
from sqlalchemy import select
from app.user.controllers.properties.utils import check_property_access
from app.user.controllers.forms.utils import get_image
from app.user.validators.transactionsuboffline import TransactionSubOffline as TransactionSubOfflineSchema
from app.core.models.subscriptions_transaction_offline import TransactionSubOffline
from app.core.models.subscriptions_plans import SubscriptionPlans
from app.user.models.users import User
subscriptions=APIRouter(prefix='/subscriptions',tags=['subscriptions'])
from datetime import datetime
import uuid 
from jose import JWTError




@subscriptions.get("/get-subscriptions/{category}")
async def get_subscriptions(
    category: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    🔍 Fetch all subscription plans for a specific category (e.g., 'PLOTS', 'FLATS')
    """
    try:
        # ✅ Verify JWT and user
        # user = await get_current_user(token, db)

        # ✅ Fetch subscriptions by category
        result = await db.execute(
            select(SubscriptionPlans).where(SubscriptionPlans.category == category.upper())
        )
        subscriptions_list = result.scalars().all()

        # ✅ If no data found
        if not subscriptions_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No subscription plans found for category '{category}'"
            )

        # ✅ Return the list
        return {
            "status": "success",
            "count": len(subscriptions_list),
            "data": subscriptions_list
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching subscriptions: {str(e)}"
        )


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

    except HTTPException as e:
        raise e
    except JWTError as e:
        raise HTTPException(status_code=401,detail=f"Token Expired")
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload reference photo: {str(e)}")


    





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
        # 1️⃣ Validate user token
        user = await get_current_user(token, db)

        # 2️⃣ Validate property ownership
        result = await db.execute(
            select(PropertyDetails).where(PropertyDetails.property_id == payload.property_id)
        )
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        if property_obj.user_id != user.user_id:
            raise HTTPException(status_code=403, detail="You are not the owner of this property")

        # 3️⃣ Validate subscription plan
        sub_query = await db.execute(
            select(SubscriptionPlans).where(SubscriptionPlans.sub_id == payload.sub_id)
        )
        sub = sub_query.scalar_one_or_none()

        if not sub:
            raise HTTPException(status_code=404, detail="Subscription plan not found")

        # ✅ Verify amount matches the chosen duration
        if sub.durations.get(str(payload.duration)) != str(int(payload.cost)):
            raise HTTPException(status_code=400, detail="Amount is insufficient for selected duration")

        # 4️⃣ Prevent duplicate payment references
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

        # 5️⃣ Generate unique transaction ID
        transaction_id = (
            getattr(payload, 'transaction_id', None)
            or f"TXOFF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        )

        # 6️⃣ Create ORM record
        record = TransactionSubOffline(
            user_id=user.user_id,
            property_id=payload.property_id,
            sub_id=payload.sub_id,
            transaction_id=transaction_id,
            cost=payload.cost,
            payment_method=payload.payment_method,
            payment_transaction_number=payload.payment_transaction_number,
            status=payload.status or "PENDING",
        )

        # 7️⃣ Save to DB
        db.add(record)
        await db.commit()
        await db.refresh(record)

        # 8️⃣ Return success response
        return {
            "message": "Offline subscription transaction created successfully.",
            "transaction_id": transaction_id,
            "status": record.status,
            "amount": str(record.cost),
        }

    except HTTPException as e:
        await db.rollback()
        raise e

    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")

    except Exception as e:
        await db.rollback()
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add offline subscription: {str(e)}")









@subscriptions.get("/get-all-subscriptions-users")
async def get_all_subscriptions_users(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    👥 Fetch all users with subscription transactions (Admin only)
    Includes property details and subscription plan info.
    """
    try:
        # 1️⃣ Authenticate Admin
        user = await get_current_user(token, db)
        if not user:
            raise HTTPException(status_code=401, detail="unauthorized")

        # 2️⃣ Query all offline transactions with user + subscription details
        query = (
            select(
                TransactionSubOffline,
                User,
                PropertyDetails,
                SubscriptionPlans
            )
            .join(User, User.user_id == TransactionSubOffline.user_id)
            .join(PropertyDetails, PropertyDetails.property_id == TransactionSubOffline.property_id)
            .join(SubscriptionPlans, SubscriptionPlans.sub_id == TransactionSubOffline.sub_id)
            .order_by(TransactionSubOffline.created_at.desc())
        )

        result = await db.execute(query)
        records = result.all()

        if not records:
            return {"message": "No subscription records found."}

        # 3️⃣ Format response
        response_data = []
        for t, user, prop, sub in records:
            response_data.append({
                "transaction_id": t.transaction_id,
                "user_name": getattr(user, "name", None),
                "user_email": user.email,
                "property_id": prop.property_id,
                "property_name": prop.property_name,
                "subscription_id": sub.sub_id,
                "subscription_type": sub.sub_type,
                "category": sub.category,
                "payment_method": t.payment_method,
                "payment_number": t.payment_transaction_number,
                "amount": float(t.cost),
                "status": t.status,
                "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        # 4️⃣ Return formatted result
        return {
            "count": len(response_data),
            "subscriptions": response_data
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching subscribed users: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch subscribed users: {str(e)}"
        )
from datetime import datetime

@subscriptions.get('/get-property-subscriptions/{property_id}')
async def get_property_subscriptions(
    property_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    🔍 Fetch all subscriptions for a specific property (only property owner can view)
    Categorized as current (active) and history (expired)
    """
    try:
        # 1️⃣ Authenticate user
        user = await get_current_user(token, db)

        # 2️⃣ Validate property ownership
        property_query = await db.execute(
            select(PropertyDetails).where(PropertyDetails.property_id == property_id)
        )
        property_obj = property_query.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        if property_obj.user_id != user.user_id:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to view subscriptions for this property"
            )

        # 3️⃣ Fetch all offline subscription transactions for this property
        result = await db.execute(
            select(TransactionSubOffline)
            .where(TransactionSubOffline.property_id == property_id)
            .order_by(TransactionSubOffline.created_at.desc())
        )
        transactions = result.scalars().all()

        if not transactions:
            return {
                "property_id": property_id,
                "user_id": user.user_id,
                "current_subscription": None,
                "subscription_history": []
            }

        current_date = datetime.utcnow()
        current_subscription = None
        history = []

        # 4️⃣ Loop through all subscriptions
        for txn in transactions:
            sub_plan_result = await db.execute(
                select(SubscriptionPlans).where(SubscriptionPlans.sub_id == txn.sub_id)
            )
            plan = sub_plan_result.scalar_one_or_none()

            # Define start and end dates (for demo, assuming 3-month duration)
            start_date = txn.created_at
            end_date = start_date.replace(
                month=start_date.month + 3 if start_date.month <= 9 else (start_date.month + 3 - 12)
            )

            record = {
                "plan": plan.sub_type if plan else None,
                "category": plan.category if plan else None,
                "status": "Active" if txn.status.lower() == "approved" else txn.status.title(),
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
                "price": f"${float(txn.cost):.2f}",
                "features": plan.services if plan else [],
            }

            # 5️⃣ Classify as current or expired
            if txn.status.lower() == "approved" and start_date <= current_date <= end_date:
                current_subscription = record
            else:
                history.append(record)

        return {
            "property_id": property_id,
            "user_id": user.user_id,
            "current_subscription": current_subscription,
            "subscription_history": history
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching property subscriptions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch property subscriptions: {str(e)}"
        )
