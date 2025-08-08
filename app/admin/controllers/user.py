
from fastapi import Depends,Request,Response,APIRouter,HTTPException
from app.user.controllers.auth.main import oauth2_scheme,get_db,AsyncSession
from app.admin.controllers.auth import get_current_admin
from sqlalchemy import select
from app.user.models.users import User
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
