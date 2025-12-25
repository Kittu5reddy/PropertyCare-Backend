from fastapi import APIRouter,Depends


from app.core.models.consultation import Consultation,ConsultationHistory
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,desc


from app.core.services.db import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")
admin_consultation=APIRouter(prefix="/admin-consultation",tags=['Admin Consultation'])

@admin_consultation.get('/get-consultation-list')
async def get_consultation_list(
    start: int = 0,
    limit: int = 10,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(Consultation)
            .order_by(desc(Consultation.id))
            .offset(start)
            .limit(limit)
        )   
        data= result.scalars().all()
        return data

    except Exception as e:
        raise e