
from fastapi import Depends,Request,Response,APIRouter,HTTPException
from app.core.controllers.auth.main import oauth2_scheme,get_db,AsyncSession
from app.admin.controllers.auth import get_current_admin
from app.admin.models.admins import Admin
from sqlalchemy import select
from app.user.models.users import User
from app.core.models.property_details import PropertyDetails,PropertyHistory
from app.admin.validators.users import UserDynamicUpdate,ChangePassword,ChangeEmail
from app.admin.validators.property import PropertyDetailsBase
from app.core.controllers.auth.main import get_password_hash
admin_property = APIRouter(prefix="/admin/property", tags=["Admin property"])






@admin_property.post('/create-property/{user_id}')
async def admin_create_property(
    user_id: str,
    schema: PropertyDetailsBase,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Validate admin
        admin_data = await get_current_admin(token, db)
        admin_id = admin_data['admin_id']

        # Create property instance
        property_instance = PropertyDetails(
            user_id=user_id,
            property_id=str(uuid4()),  # Generate unique ID
            property_name=schema.property_name,
            plot_number=schema.plot_number,
            house_number=schema.house_number,
            project_name_or_venture=schema.project_name_or_venture,
            street=schema.street,
            city=schema.city,
            state=schema.state,
            country=schema.country,
            pin_code=schema.pin_code,
            size=schema.size,
            phone_number=schema.phone_number,
            land_mark=schema.land_mark,
            latitude=schema.latitude,
            longitude=schema.longitude,
            facing=schema.facing,
            type=schema.type,
            admin_id=admin_id,
            description=schema.description
        )

        db.add(property_instance)
        await db.commit()
        await db.refresh(property_instance)

        # Save to property history
        history = PropertyHistory(
            property_id=property_instance.id,  # FK to PropertyDetails PK
            updated_by_admin=admin_id,
            updated_by_user=user_id,
            action="CREATE",
            changes_made={field: getattr(property_instance, field) 
                          for field in schema.__fields__.keys()}
        )
        db.add(history)
        await db.commit()
        await db.refresh(history)

        return {"message": "Property added successfully", "property_id": property_instance.property_id}

    except Exception as e:
        return {"error": str(e)}
