from app.admin.controllers.auth.utils import get_current_admin
from app.core.controllers.auth.main import oauth2_scheme
from app.core.models import get_db,redis_get_data,redis_set_data,AsyncSession
from fastapi import APIRouter,Depends
from sqlalchemy import select,func
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.models import get_db
from app.admin.models.admins import Admin
from app.core.models.subscriptions_plans import SubscriptionPlans,SubscriptionPlansHistory
from datetime import datetime
from app.admin.validators.subscriptionplancreate import SubscriptionPlanCreate
admin_subscriptions=APIRouter(prefix='/admin-subscriptions',tags=["admin subscriptions"])
from .utils import generate_subscription_id
from jose import JWTError
from app.admin.validators.subscriptionplanupdate import SubscriptionPlanUpdate
from app.core.models.subscriptions_transactions import TransactionSubOffline

@admin_subscriptions.get("/get-subscriptions")
async def get_subscription_plans(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    🔍 Fetch all subscription plans (Admin only)
    """
    try:
        # 1️⃣ Verify admin token
        admin = await get_current_admin(token, db)
        if not admin:
            raise HTTPException(status_code=401, detail="Unauthorized admin access")

        # 2️⃣ Fetch all subscription plans
        result = await db.execute(select(SubscriptionPlans))
        plans = result.scalars().all()

        if not plans:
            raise HTTPException(status_code=404, detail="No subscription plans found")

        # 3️⃣ Return formatted response
        return {
            "count": len(plans),
            "plans": [
                {
                    "sub_id": plan.sub_id,
                    "sub_type": plan.sub_type,
                    "category": plan.category,
                    "services": plan.services,
                    "durations": plan.durations,
                    "rental_percentages": plan.rental_percentages,
                    "is_active": plan.is_active,
                    "comments": plan.comments,
                    "created_at": plan.created_at,
                    "updated_at": plan.updated_at,
                }
                for plan in plans
            ],
        }

    except HTTPException as e:
        raise e
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")
    except Exception as e:
        print(f"Error fetching required actions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_subscriptions.post('/add-subscription-plan')
async def add_subscription_plan(
    payload: SubscriptionPlanCreate,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    ➕ Create a new subscription plan (Admin only)
    """
    try:
        # 1️⃣ Validate Admin (you can re-enable later)
        admin = await get_current_admin(token, db)
        if not admin:
            raise HTTPException(status_code=401, detail="Unauthorized admin access")

        # 2️⃣ Generate Unique sub_id
        sub_id = generate_subscription_id(payload.category, payload.sub_type)

        # 3️⃣ Ensure it's unique in DB
        existing_plan = await db.execute(
            select(SubscriptionPlans).where(SubscriptionPlans.sub_id == sub_id)
        )
        if existing_plan.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Generated Subscription ID already exists (try again)")

        # 4️⃣ Create record
        record = SubscriptionPlans(
            sub_id=sub_id,
            sub_type=payload.sub_type,
            category=payload.category,
            services=payload.services,
            durations=payload.durations,
            rental_percentages=payload.rental_percentages,
            comments=payload.comments,
            created_by=admin.admin_id,
            is_active=payload.is_active or False,
            created_at=datetime.utcnow(),
        )

        db.add(record)
        await db.commit()
        await db.refresh(record)

        return {
            "message": "Subscription plan created successfully",
            "plan": {
                "sub_id": record.sub_id,
                "sub_type": record.sub_type,
                "category": record.category,
                "services": record.services,
                "renteral_percentages":record.rental_percentages,
                "durations": record.durations,
                "is_active": record.is_active
            }
        }


    except HTTPException as e:
        raise e
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")
    except Exception as e:
        print(f"Error fetching required actions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")




@admin_subscriptions.put("/update-subscription-plan/{sub_id}")
async def update_subscription_plan(
    sub_id: str,
    payload: SubscriptionPlanUpdate,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    ✏️ Update an existing subscription plan (Admin only)
    """
    try:
        # 1️⃣ Validate admin
        admin = await get_current_admin(token, db)

        # 2️⃣ Fetch existing plan
        result = await db.execute(select(SubscriptionPlans).where(SubscriptionPlans.sub_id == sub_id))
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=404, detail=f"Subscription plan '{sub_id}' not found")

        # 3️⃣ Save old version in history table before updating
        history = SubscriptionPlansHistory(
            plan_id=plan.id,
            sub_id=plan.sub_id,
            sub_type=plan.sub_type,
            category=plan.category,
            services=plan.services,
            durations=plan.durations,
            comments=plan.comments,
            is_active=plan.is_active,
            created_by=plan.created_by,
            action="UPDATE",
            changed_by=admin.admin_id,
        )
        db.add(history)

        # 4️⃣ Update fields dynamically
        update_fields = payload.model_dump(exclude_unset=True)
        for key, value in update_fields.items():
            setattr(plan, key, value)
        plan.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(plan)

        return {
            "message": "Subscription plan updated successfully",
            "updated_plan": {
                "sub_id": plan.sub_id,
                "sub_type": plan.sub_type,
                "category": plan.category,
                "services": plan.services,
                "durations": plan.durations,
                "is_active": plan.is_active,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating subscription plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update subscription plan: {str(e)}")



@admin_subscriptions.delete("/delete-subscription-plan/{sub_id}")
async def delete_subscription_plan(
    sub_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    ❌ Soft delete a subscription plan (Admin only)
    """
    try:
        # 1️⃣ Validate admin
        admin = await get_current_admin(token, db)

        # 2️⃣ Fetch existing plan
        result = await db.execute(select(SubscriptionPlans).where(SubscriptionPlans.sub_id == sub_id))
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=404, detail=f"Subscription plan '{sub_id}' not found")

        # 3️⃣ Log to history table
        history = SubscriptionPlansHistory(
            plan_id=plan.id,
            sub_id=plan.sub_id,
            sub_type=plan.sub_type,
            category=plan.category,
            services=plan.services,
            durations=plan.durations,
            comments=plan.comments,
            is_active=plan.is_active,
            created_by=plan.created_by,
            action="DELETE",
            changed_by=admin.admin_id,
        )
        db.add(history)

        # 4️⃣ Perform soft delete (deactivate)
        plan.is_active = False
        plan.comments = (plan.comments or "") + f" | Deactivated by admin {admin.admin_id} at {datetime.utcnow()}"
        plan.updated_at = datetime.utcnow()

        await db.commit()
        return {"message": f"Subscription plan '{sub_id}' deactivated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting subscription plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete subscription plan: {str(e)}")




from sqlalchemy import select, desc

@admin_subscriptions.get("/get-offline-payments")
async def get_offline_payments(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    🧾 Fetch all offline subscription payments (Admin only)
    Ordered by latest created_at
    """
    try:
        # 1️⃣ Authenticate admin
        admin = await get_current_admin(token, db)
        if not admin:
            raise HTTPException(status_code=401, detail="Unauthorized admin access")

        # 2️⃣ Fetch and order by latest first
        result = await db.execute(
            select(TransactionSubOffline).order_by(desc(TransactionSubOffline.created_at))
        )
        offline_payments = result.scalars().all()

        if not offline_payments:
            raise HTTPException(status_code=404, detail="No offline payments found")

        # 3️⃣ Format and return
        return {
            "count": len(offline_payments),
            "offline_payments": [
                {
                    "transaction_id": t.transaction_id,
                    "user_id": t.user_id,
                    "property_id": t.property_id,
                    "sub_id": t.sub_id,
                    "cost": str(t.cost),
                    "payment_method": t.payment_method,
                    "payment_transaction_number": t.payment_transaction_number,
                    "status": t.status,
                    "created_at": t.created_at,
                    "updated_at": t.updated_at,
                }
                for t in offline_payments
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching offline payments: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch offline payments: {str(e)}"
        )




@admin_subscriptions.put("/update-offline-payment-status/{transaction_id}")
async def update_offline_payment_status(
    transaction_id: str,
    new_status: str,  # e.g. "APPROVED", "REJECTED"
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    🔄 Update the status of an offline transaction (Admin Only)
    """
    try:
        # 1️⃣ Authenticate admin
        admin = await get_current_admin(token, db)
        if not admin:
            raise HTTPException(status_code=401, detail="Unauthorized admin access")

        # 2️⃣ Validate status value
        valid_statuses = {"PENDING", "APPROVED", "REJECTED"}
        if new_status.upper() not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of {', '.join(valid_statuses)}"
            )

        # 3️⃣ Fetch the transaction
        result = await db.execute(
            select(TransactionSubOffline).where(TransactionSubOffline.transaction_id == transaction_id)
        )
        transaction = result.scalar_one_or_none()

        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # 4️⃣ Update the record
        transaction.status = new_status.upper()
        transaction.updated_at = datetime.utcnow()

        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)

        # 5️⃣ Return success response
        return {
            "message": f"Transaction {transaction_id} status updated successfully",
            "transaction_id": transaction.transaction_id,
            "new_status": transaction.status,
            "updated_at": transaction.updated_at,
            "updated_by": admin.admin_id
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating transaction status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update transaction status: {str(e)}"
        )