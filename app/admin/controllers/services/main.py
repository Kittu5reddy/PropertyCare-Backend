from app.core.models.services import Services,ServicesHistory
from app.core.validators.services import ServiceCreate
from app.core.models import get_db,redis_delete_data,redis_delete_pattern,AsyncSession

from fastapi import APIRouter,Depends,Response,Request,HTTPException
from app.admin.controllers.auth.utils import get_current_admin_refresh_token
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

admin_services=APIRouter(prefix='/admin-services',tags=['admin-services'])


@admin_services.post('/create-services')
async def create_service(payload: ServiceCreate, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        token = request.cookies.get('refresh_token')
        if not token:
            raise HTTPException(status_code=403, detail="No refresh token provided")
        
        admin = get_current_admin_refresh_token(token)
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        # Create new service
        new_service = Services(service_id="sv004",created_by=admin.get('email'),**payload.dict())
        db.add(new_service)
        await db.commit()
        await db.refresh(new_service)

        # Log creation in ServicesHistory
        history_entry = ServicesHistory(
            service_id= "sv004",
            edited_by=admin.get("admin_id"),
            changes_made=payload.dict(),
            action="CREATED"
        )
        db.add(history_entry)
        await db.commit()
        await db.refresh(history_entry)
        cache_key = "services:list"
        await redis_delete_data(cache_key = "services:list")
        return {"status": "success", "service": new_service.service_name, "history_id": history_entry.id}

    except SQLAlchemyError as db_err:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_err)}")
    except HTTPException:
        # Re-raise known HTTPExceptions
        raise
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    


@admin_services.put('/update-service/{service_id}')
async def update_service(
    service_id: int,
    payload: ServiceCreate,  # you can create a separate schema for update if needed
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Get token from cookies
        token = request.cookies.get('refresh_token')
        if not token:
            raise HTTPException(status_code=403, detail="No refresh token provided")
        
        admin = get_current_admin_refresh_token(token)
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        # Fetch existing service
        result = await db.execute(select(Services).where(Services.id == service_id))
        service = result.scalar_one_or_none()
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")

        # Store old data for history
        old_data = {
            "service_name": service.service_name,
            "category": service.category,
            "services": service.services,
            "is_active": service.is_active,
            "approx_cost_usd": service.approx_cost_usd,
            "approx_cost_inr": service.approx_cost_inr,
            "durations": service.durations,
            "applicable_to": service.applicable_to,
            "comments": service.comments
        }

        # Update service fields
        for key, value in payload.dict(exclude_unset=True).items():
            setattr(service, key, value)
        
        db.add(service)
        await db.commit()
        await db.refresh(service)

        # Log changes in ServicesHistory
        changes = {}
        for key, old_value in old_data.items():
            new_value = getattr(service, key)
            if old_value != new_value:
                changes[key] = {"old": old_value, "new": new_value}

        if changes:
            history_entry = ServicesHistory(
                service_id=service.id,
                edited_by=admin.get("admin_id"),
                changes_made=changes,
                action="UPDATED"
            )
            db.add(history_entry)
            await db.commit()
            await db.refresh(history_entry)
        else:
            history_entry = None

        return {
            "status": "success",
            "service": service.service_name,
            "history_id": history_entry.id if history_entry else None
        }

    except SQLAlchemyError as db_err:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_err)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
