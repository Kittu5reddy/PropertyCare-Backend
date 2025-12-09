from sqlalchemy import select
# from app.core.models import async_session
from app.admin.models.admin import Admin      
from app.core.controllers.auth.utils import pwd_context
import uuid

# async def create_admin(email: str, password: str):
#     async with async_session() as db:
#         # Check if admin already exists
#         result = await db.execute(select(Admin).where(Admin.email == email))
#         existing_admin = result.scalar_one_or_none()

#         if existing_admin:
#             print(f"⚠️ Admin with email {email} already exists.")
#             return

#         admin = Admin(
#             admin_id=str(uuid.uuid4()),
#             email=email,
#             hashed_password=pwd_context.hash(password),
#             MFA=False
#         )

#         db.add(admin)
#         await db.commit()
#         print(f"✅ Admin created successfully: {email}")
