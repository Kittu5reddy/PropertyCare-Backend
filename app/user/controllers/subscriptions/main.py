from .utils import PropertyDetails,get_image_or_default
from fastapi import APIRouter,Depends,HTTPException,status
from app.core.models import AsyncSession,get_db
from app.core.controllers.auth.main import oauth2_scheme
from app.core.controllers.auth.utils import get_current_user
from sqlalchemy import select
from app.user.controllers.properties.utils import check_property_access

from app.user.validators.transactionsuboffline import TransactionSubOffline as TransactionSubOfflineSchema
from app.core.models.subscriptions_transaction_offline import TransactionSubOffline
from app.core.models.subscriptions_plans import SubscriptionPlans
from app.core.models.subscriptions import Subscriptions,SubscriptionHistory
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
            print(subscriptions_list)
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
        print(str(e))
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
    """
    ✅ Fetch properties of a specific category for the logged-in user.
    Example: /get-properties?category=flats
    """
    try:
        # 1️⃣ Authenticate user
        user = await get_current_user(token, db)

        # 2️⃣ Validate category input
        if not category:
            raise HTTPException(status_code=400, detail="Category is required")

        # 3️⃣ Fetch properties matching category + user
        result = await db.execute(
            select(PropertyDetails).where(
                PropertyDetails.type.ilike(category),  # case-insensitive match
                PropertyDetails.user_id == user.user_id
            )
        )
        properties = result.scalars().all()

        # 4️⃣ Handle empty results
        if not properties:
            raise HTTPException(
                status_code=404,
                detail=f"No properties found for category '{category}'."
            )

        # 5️⃣ Format response
        response = {
            "user_id": user.user_id,
            "category": category,
            "count": len(properties),
            "properties": [
                {
                    "property_id": p.property_id,
                    "property_name": p.property_name,
                    "type": p.type,
                    "city": p.city,
                    "state": p.state,
                    "property_image_url":await get_image_or_default(
                        f"/property/{p.property_id}/legal_documents/property_photo.png"
                    ),
                }
                for p in properties
            ],
        }

        return response

    except HTTPException as e:
        raise e
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")
    except Exception as e:
        print(f"❌ Error in get_properties: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch properties: {str(e)}")






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
        # print(sub)
        # ✅ Verify amount matches the chosen duration
# Safely extract the required price from the plan's durations dict
        plan_price = int(sub.durations.get(str(payload.duration), 0))
        paid_amount = int(payload.cost)
        
        # Validate that cost covers the selected plan duration
        if paid_amount < plan_price:
            print(f"❌ Paid: {paid_amount}, Required: {plan_price}")
            raise HTTPException(
                status_code=400,
                detail=f"Amount {paid_amount} is insufficient for selected duration ({payload.duration} months). Required: {plan_price}."
            )
        

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
            duration=int(payload.duration),
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
    👥 Fetch all users with active subscription transactions (Admin only)
    Includes user, property, and plan details.
    """
    try:
        # 1️⃣ Authenticate Admin
        user = await get_current_user(token, db)
        if not user or user.role.lower() != "admin":
            raise HTTPException(status_code=401, detail="Unauthorized access")

        # 2️⃣ Query: fetch all offline subscription transactions + related data
        query = (
            select(
                TransactionSubOffline,
                User,
                PropertyDetails,
                SubscriptionPlans,
                Subscriptions
            )
            .join(User, User.user_id == TransactionSubOffline.user_id)
            .join(PropertyDetails, PropertyDetails.property_id == TransactionSubOffline.property_id)
            .join(SubscriptionPlans, SubscriptionPlans.sub_id == TransactionSubOffline.sub_id)
            .join(Subscriptions, Subscriptions.sub_id == TransactionSubOffline.sub_id)
            .where(Subscriptions.is_active == True)
            .order_by(TransactionSubOffline.created_at.desc())
        )

        result = await db.execute(query)
        records = result.all()

        if not records:
            return {"message": "No subscription records found."}

        # 3️⃣ Format response
        response_data = []
        for t, user, prop, sub, subscription in records:
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
                "is_active": subscription.is_active,
                "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        # 4️⃣ Return formatted result
        return {
            "count": len(response_data),
            "subscriptions": response_data
        }

    except HTTPException as e:
        raise e
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




@subscriptions.get("/is-property-eligible")
async def get_eligible_rental_percentage(
    property_id: str,
    sub_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    ✅ Check if a property is eligible for rental percentage benefits
    based on the subscription plan and property details.
    """
    try:
        # 1️⃣ Validate user token
        user = await get_current_user(token, db)

        # 2️⃣ Validate property ownership
        result = await db.execute(
            select(PropertyDetails).where(PropertyDetails.property_id == property_id)
        )
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        if property_obj.user_id != user.user_id:
            raise HTTPException(status_code=403, detail="You are not the owner of this property")

        # 3️⃣ Validate subscription plan
        sub_query = await db.execute(
            select(SubscriptionPlans).where(SubscriptionPlans.sub_id == sub_id)
        )
        sub = sub_query.scalar_one_or_none()

        if not sub:
            raise HTTPException(status_code=404, detail="Subscription plan not found")

        # 4️⃣ Check if subscription applies to this property type
        if sub.category.upper() != property_obj.type.upper():
            print(sub.category)
            print(property_obj.type)
            raise HTTPException(status_code=400, detail="Subscription is not applicable for this property")

        # 5️⃣ Logic based on property type
        from decimal import Decimal

        if property_obj.type.upper() == "FLAT":
            if property_obj.rental_income and property_obj.rental_income > 15000:
                
                rental_percent = getattr(sub, "rental_percent", 0)
        
                # Default to 7% if not defined
                if not rental_percent:
                    rental_percent = 7
        
                rental_income = Decimal(property_obj.rental_income)
                percent = Decimal(rental_percent) / Decimal(100)
        
                durations = {
                    "3": float(round(rental_income * percent * Decimal(3), 2)),
                    "6": float(round(rental_income * percent * Decimal(6), 2)),
                    "12": float(round(rental_income * percent * Decimal(12), 2)),
                }
        
                return {
                    "status": "eligible",
                    "extra_amount": float(rental_percent),
                    "message": "your rates has been changed as per property",
                    "estimated_returns": durations
                }

        

        elif property_obj.type.upper() == "PLOT":
            scale_factor = 1
            if property_obj.scale.upper() == "ACRES":
                scale_factor = 4840
            elif property_obj.scale.upper() == "GUNTAS":
                scale_factor = 120

            extra_amount = ((scale_factor * property_obj.size) / 400) * 1000

            # Ensure durations field exists and is dictionary-like
            sub_durations = getattr(sub, "durations", {})
            if not isinstance(sub_durations, dict):
                raise HTTPException(status_code=500, detail="Invalid subscription duration format")

            durations = {
                "3": int(sub_durations.get("3", 0)) + int(extra_amount),
                "6": int(sub_durations.get("6", 0)) + int(extra_amount),
                "12": int(sub_durations.get("12", 0)) + int(extra_amount),
            }

            return {
                "status": "eligible",
                "estimated_returns": durations
            }

        else:
            raise HTTPException(status_code=400, detail="Unsupported property type")

    except HTTPException as e:
        raise e
    except Exception as e:
        print(str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check eligibility: {str(e)}"
        )


@subscriptions.get("/get-all-sub-transactions")
async def get_active_sub(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    ✅ Fetch all active property subscriptions for the current user
    """
    try:
        # 1️⃣ Authenticate user
        user = await get_current_user(token, db)
        total_transactions=await db.execute(select(TransactionSubOffline).where(TransactionSubOffline.user_id==user.user_id))
        total_transactions=total_transactions.all()
        print(total_transactions)
        return {"total_transactions":total_transactions}
    except HTTPException as e:
        raise e
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")
    except Exception as e:
        print(f"❌ Error in get_active_sub: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch active subscriptions: {str(e)}")



from datetime import datetime
from sqlalchemy import select, desc

@subscriptions.get("/get-current-property-sub/{property_id}")
async def get_current_property_sub(
    property_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    ✅ Fetch the latest subscription (end date, status, and remaining days)
    for a specific property owned by the logged-in user.
    """
    try:
        # 1️⃣ Authenticate user
        user = await get_current_user(token, db)

        # 2️⃣ Validate property ownership
        result = await db.execute(
            select(PropertyDetails).where(PropertyDetails.property_id == property_id)
        )
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        if property_obj.user_id != user.user_id:
            raise HTTPException(status_code=403, detail="You are not the owner of this property")

        # 3️⃣ Fetch latest subscription record for this property
        sub_result = await db.execute(
            select(Subscriptions)
            .where(Subscriptions.property_id == property_id)
            .order_by(desc(Subscriptions.sub_end_date))
        )

        sub = sub_result.scalar_one_or_none()

        if not sub:
            return {
                "status": "no_subscription",
                "message": "No subscription records found for this property."
            }

        # 4️⃣ Calculate remaining days
        now = datetime.utcnow()
        remaining_days = None
        if sub.sub_end_date:
            remaining_days = (sub.sub_end_date - now).days

        # 5️⃣ Build response
        response = {
            "property_id": property_id,
            "subscription_id": sub.usub_id,
            "sub_id": sub.sub_id,
            "is_active": sub.is_active,
            "start_date": sub.sub_start_date.isoformat(),
            "end_date": sub.sub_end_date.isoformat(),
            "method": sub.method,
            "comments": sub.comments,
            "remaining_days": remaining_days if remaining_days >= 0 else 0,
            "status": "active" if sub.is_active and remaining_days > 0 else "expired",
        }

        return response

    except HTTPException as e:
        raise e
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")
    except Exception as e:
        print(f"❌ Error in get_current_property_sub: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch subscription: {str(e)}")


@subscriptions.get('/get-current-property-subscription/{property_id}')
async def get_current_property_subscription(
    property_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1️⃣ Validate and get user
        user = await get_current_user(token, db)

        # 2️⃣ Fetch user's active subscription for this property
        result = await db.execute(
            select(Subscriptions)
            .where(
                Subscriptions.property_id == property_id,
                Subscriptions.user_id == user.user_id,
                Subscriptions.is_active == True
            )
        )
        data = result.scalar_one_or_none()

        # 3️⃣ If no active subscription found
        if not data:
            return {
                "is_active": False,
                "sub_name": None,
                "ends_on": None,
                "features": []
            }

        # 4️⃣ Fetch subscription plan details
        sub_result = await db.execute(
            select(SubscriptionPlans).where(SubscriptionPlans.sub_id == data.sub_id)
        )
        sub = sub_result.scalar_one_or_none()

        if not sub:
            raise HTTPException(status_code=404, detail="Subscription plan not found")

        # 5️⃣ Return subscription info
        return {
            "is_active": True,
            "sub_name": sub.sub_type,
            "ends_on": data.sub_end_date,
            "features": sub.services
        }

    except HTTPException as e:
        raise e
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Error fetching subscription details: {str(e)}")



@subscriptions.get('/get-current-property-subscription-history/{property_id}')
async def get_current_property_subscription_history(
    property_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1️⃣ Validate and get user
        user = await get_current_user(token, db)

        # 2️⃣ Fetch all subscription records (past + present)
        result = await db.execute(
            select(Subscriptions)
            .where(
                Subscriptions.property_id == property_id,
                Subscriptions.user_id == user.user_id
            )
            .order_by(Subscriptions.sub_start_date.desc())
        )
        subscriptions = result.scalars().all()

        # 3️⃣ If no history found
        if not subscriptions:
            return {"message": "No subscription history found", "history": []}

        # 4️⃣ Build a detailed response
        history = []
        for sub_record in subscriptions:
            # Fetch corresponding plan details
            plan_result = await db.execute(
                select(SubscriptionPlans).where(SubscriptionPlans.sub_id == sub_record.sub_id)
            )
            plan = plan_result.scalar_one_or_none()

            history.append({
                "sub_name": plan.sub_type if plan else None,
                "is_active": sub_record.is_active,
                "started_on": sub_record.sub_start_date,
                "ended_on": sub_record.sub_end_date
            })

        # 5️⃣ Return complete history
        return {
            "property_id": property_id,
            "user_id": user.user_id,
            "total_subscriptions": len(history),
            "history": history
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired")
    except HTTPException as e:
        raise e
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Error fetching subscription history: {str(e)}")


@subscriptions.get("/get-all-transactions")
async def get_all_transactions(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    💰 Fetch all transactions (Admin only)
    Includes user, property, and subscription plan details for both online & offline payments.
    """
    try:
        # 1️⃣ Authenticate Admin
        user = await get_current_user(token, db)
        if not user or user.role.lower() != "admin":
            raise HTTPException(status_code=401, detail="Unauthorized access")

        # 2️⃣ Query transactions (both online and offline, if applicable)
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
            return {"message": "No transactions found."}

        # 3️⃣ Format the response
        response_data = []
        for t, user, prop, sub in records:
            response_data.append({
                "transaction_id": t.transaction_id,
                # "user_name": getattr(user, "name", None),
                # "user_email": user.email,
                "property_id": prop.property_id,
                # "property_name": prop.property_name,
                "subscription_type": sub.sub_type,
                "category": sub.category,
                "amount": float(t.cost),
                "payment_method": t.payment_method,
                "payment_number": t.payment_transaction_number,
                "status": t.status,
                "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        # 4️⃣ Return the final formatted response
        return {
            "count": len(response_data),
            "transactions": response_data
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Error fetching all transactions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch transactions: {str(e)}"
        )
