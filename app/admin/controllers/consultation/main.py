from fastapi import APIRouter,Depends


from app.core.models.consultation import Consultation,ConsultationHistory
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,desc
from app.admin.validators.consultation.update_consultation import ConsultationUpdateRequest

from app.core.services.db import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")
admin_consultation=APIRouter(prefix="/admin-consultation",tags=['Admin Consultation'])



changed_by="ADMIN001"



# ==========================
#    G E T
# ==========================



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
    



# ==========================
#    P U T
# ==========================

@admin_consultation.put("/consultation/bulk-update")
async def bulk_update_consultation(
    payload: ConsultationUpdateRequest,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    # user = decode_token(token)  # your JWT decode
    # changed_by = user.get("sub")

    try:
        for item in payload.updates:
            result = await db.execute(
                select(Consultation).where(Consultation.id == item.id)
            )
            consultation = result.scalar_one_or_none()

            if not consultation:
                raise HTTPException(
                    status_code=404,
                    detail=f"Consultation ID {item.id} not found"
                )

            changes = {}

            # Only update fields that are present
            for field, new_value in item.dict(exclude_unset=True).items():
                if field == "id":
                    continue

                old_value = getattr(consultation, field)

                if old_value != new_value:
                    setattr(consultation, field, new_value)
                    changes[field] = {
                        "old": old_value,
                        "new": new_value
                    }

            # Save history only if something changed
            if changes:
                history = ConsultationHistory(
                    consultation_id=consultation.id,
                    changes=changes,
                    changed_by=changed_by
                )
                db.add(history)

        await db.commit()
        return {"message": "Consultations updated successfully"}

    except Exception as e:
        await db.rollback()
        raise e
