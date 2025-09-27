
from fastapi import Depends,Request,Response,APIRouter,HTTPException
from app.core.controllers.auth.main import oauth2_scheme,get_db,AsyncSession
from app.admin.controllers.auth import get_current_admin
from app.admin.models.admins import Admin
from sqlalchemy import select
from app.user.models.users import User
from app.user.models.personal_details import PersonalDetails,PersonalDetailsHistory
from app.admin.validators.users import UserDynamicUpdate,ChangePassword,ChangeEmail
from app.core.controllers.auth.main import get_password_hash
admin_user = APIRouter(prefix="/admin/user", tags=["Admin User"])



from sqlalchemy import select

@admin_user.get('/get-users-details')
async def get_user_details(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        get_current_admin(token, db)

        # Assuming you want to select all users
        result = await db.execute(select(User.user_id))
        users = result.scalars().all()
        return {"users": users}

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))


@admin_user.put("/update/{user_id}")
async def update_user(
    user_id: str,
    schema: UserDynamicUpdate,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Validate admin
        admin_data = await get_current_admin(token, db)
        if not admin_data:
            raise HTTPException(status_code=404, detail="Admin not found")
        admin_id = admin_data["admin_id"]

        # Fetch user details
        result = await db.execute(
            select(PersonalDetails).where(PersonalDetails.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get update data
        update_data = schema.dict(exclude_unset=True)

        # Track changes
        changes = {}
        for field, new_value in update_data.items():
            old_value = getattr(user, field, None)
            if old_value != new_value:
                changes[field] = {"old": old_value, "new": new_value}
                setattr(user, field, new_value)

        if not changes:
            return {"message": "No changes detected"}

        await db.commit()
        await db.refresh(user)

        # Save history
        history = PersonalDetailsHistory(
              # use PK of PersonalDetails
            user_id=user.user_id,          # keep mapping to User
            updated_by_admin=admin_id,
            action="UPDATE",
            changes_made=changes,
            remarks="Admin updated user details"
        )

        db.add(history)
        await db.commit()
        await db.refresh(history)

        return {"message": "User updated successfully", "changes": changes}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_user.put("/update/{user_id}/change-password")
async def change_password(
    user_id: str,
    schema: ChangePassword,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Validate admin
        admin_data = await get_current_admin(token, db)
        if not admin_data:
            raise HTTPException(status_code=404, detail="Admin not found")
        admin_id = admin_data["admin_id"]

        # Fetch user from main User table
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update password
        user.hashed_password = get_password_hash(schema.new_password)
        await db.commit()
        await db.refresh(user)

        # Save to history
        history = PersonalDetailsHistory(
            user_id=user.user_id,
            updated_by_admin=admin_id,
            action="PASSWORD_CHANGE",
            changes_made={"password": {"old": "********", "new": "********"}},
            remarks="Admin changed user password"
        )
        db.add(history)
        await db.commit()

        return {"message": "User password changed successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@admin_user.put("/update/{user_id}/change-email")
async def change_email(
    user_id: str,
    schema: ChangeEmail,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Validate admin
        admin_data = await get_current_admin(token, db)
        if not admin_data:
            raise HTTPException(status_code=404, detail="Admin not found")
        admin_id = admin_data["admin_id"]

        # Fetch user
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Save old email
        old_email = user.email

        # Update email
        user.email = schema.new_email
        await db.commit()
        await db.refresh(user)

        # Save to history
        history = PersonalDetailsHistory(
            user_id=user.user_id,
            updated_by_admin=admin_id,
            action="EMAIL_CHANGE",
            changes_made={"email": {"old": old_email, "new": user.email}},
            remarks=f"Admin changed email from {old_email} to {user.email}"
        )
        db.add(history)
        await db.commit()
        await db.refresh(history)

        return {"message": "User email changed successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@admin_user.delete("/delete/{user_id}")
async def delete_user(
    user_id: str,  # match your model type
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Validate admin
        admin_data = await get_current_admin(token, db)
        if not admin_data:
            raise HTTPException(status_code=404, detail="Admin not found")
        admin_id = admin_data["admin_id"]

        # Ensure admin exists
        result = await db.execute(select(Admin).where(Admin.admin_id == admin_id))
        admin = result.scalar_one_or_none()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")

        # Fetch user
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Soft delete → mark inactive instead of deleting
        user.status = False

        # Save history BEFORE committing
        history = PersonalDetailsHistory(
            user_id=user.user_id,
            updated_by_admin=admin_id,
            action="DELETE",
            changes_made={"user_name": user.user_name, "status": "inactive"},
            remarks=f"Admin deleted user {user.user_name}"
        )
        db.add(history)

        # Commit changes
        await db.commit()

        # Refresh objects
        await db.refresh(user)
        await db.refresh(history)

        return {"message": "User soft-deleted successfully", "history_id": history.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
