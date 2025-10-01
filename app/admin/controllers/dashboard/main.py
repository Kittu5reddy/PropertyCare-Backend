from sqlalchemy import select, func, case
from fastapi import APIRouter, Depends
from app.user.models.users import User
from app.core.models import AsyncSession, get_db

admin_dash = APIRouter(prefix="/admin-dashboard", tags=['admin dashboard'])

@admin_dash.get('/user-data')
async def get_user_info(db: AsyncSession = Depends(get_db)):
    query = select(
        func.count(User.id).label("total"),
        func.sum(case((User.status == "active", 1), else_=0)).label("active"),
        func.sum(case((User.status == "inactive", 1), else_=0)).label("inactive")
    )
    result = await db.execute(query)
    counts = result.first()  # returns a tuple like (total, active, inactive)

    return {
        "total_users": counts.total,
        "active_users": counts.active if  counts.active else 0,
        "inactive_users": counts.inactive if counts.inactive else 0
    }