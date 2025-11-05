from app.admin.controllers.auth.utils import get_current_admin
from app.core.controllers.auth.main import oauth2_scheme
from app.core.models import get_db,redis_get_data,redis_set_data,AsyncSession
from fastapi import APIRouter,Depends
from sqlalchemy import select,func
from app.user.models.users import User
from app.core.models.property_details import PropertyDetails



admin_dash=APIRouter(prefix='/admin-dashboard',tags=["admin dashboard"])


# @admin_dash.post("/get-users-details")
# async def get_user_details(
#     token: str = Depends(oauth2_scheme),
#     db: AsyncSession = Depends(get_db)
# ):
#     try:
#         # ✅ Total users
#         total_stmt = select(func.count(User.id))
#         total_result = await db.execute(total_stmt)
#         total_users = total_result.scalar() or 0

#         # ✅ Active users (status == True)
#         active_stmt = select(func.count(User.id)).where(User.status.is_(True))
#         active_result = await db.execute(active_stmt)
#         active_users = active_result.scalar() or 0

#         # ✅ Inactive users
#         inactive_users = total_users - active_users

#         return {
#             "total_users": total_users,
#             "active_users": active_users,
#             "inactive_users": inactive_users,
#         }

#     except Exception as e:
#         print("❌ Exception in get_user_details:", repr(e))
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Something went wrong while fetching user stats."
#         )

# @admin_dash.post('/get-properties-details')
# async def get_properties_details(token:str=Depends(oauth2_scheme),
#                            db:AsyncSession=Depends(get_db)):
#     try:
#         total_stmt = select(func.count(PropertyDetails.id))
#         result = await db.execute(total_stmt)
#         total_count = result.scalar()

#         # ✅ active subscriptions
#         active_stmt = select(func.count(PropertyDetails.id)).where(PropertyDetails.active_sub == True)
#         result = await db.execute(active_stmt)
#         active_count = result.scalar()
#         return {
#             "total_users":total_count,
#             "active_users":active_count,
#             "Inactive":total_count-active_count
#                 }
#     except Exception as e:
#         print("excep")
        
