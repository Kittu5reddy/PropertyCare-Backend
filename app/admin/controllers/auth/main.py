from fastapi import APIRouter,HTTPException,Depends,Response
from app.admin.validators.auth.login import AdminLogin
from app.core.services.db import get_db,AsyncSession
from sqlalchemy import select
from app.admin.models.admin import Admin
from app.core.controllers.auth.utils import create_access_token,create_refresh_token,verify_password,verify_access_token,verify_refresh_token
admin_auth=APIRouter(prefix='/admin-auth',tags=['Admin Auth'])

@admin_auth.post('/login')
async def login(payload:AdminLogin,response:Response,db:AsyncSession=Depends(get_db)):
    try:
        smt=await db.execute(select(Admin).where(Admin.email==payload.email))
        admin=smt.scalar_one_or_none()
        if not admin:
            raise HTTPException(status_code=404,detail="Admin Not Found")
        if not verify_password(payload.password,admin.hashed_password):
            raise HTTPException(status_code=401,detail="email or password is not correct")
        if not admin.MFA:
            raise HTTPException(status_code=307,detail="redirect to generte page") # mfa activation
        
        raise HTTPException(status_code=308,detail="redirect to verify page")
            
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))


