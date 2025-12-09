from fastapi import APIRouter,Depends,HTTPException,UploadFile,File
from app.user.controllers.auth.utils import get_current_user
from sqlalchemy.ext.asyncio import (
    AsyncSession
)
from app.core.services.db import get_db
from app.user.models.feedbacks import FeedBack
from .utils import generate_feedback_number
from app.core.services.s3 import upload_feedback_image_as_png
from background_task.tasks.email_tasks import send_email_task
from jose import JWTError
feedback=APIRouter(prefix='/feedbacks',tags=['feed back'])
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
from fastapi import Form
@feedback.post("/feedback-submit")
async def feedback_submit(
    property_id: str = Form(None),
    category: str = Form(...),
    stars: int = Form(...),
    comment: str = Form(None),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    image: UploadFile | None = File(None)
):
    try:
        user = await get_current_user(token, db)


        # Step 1: Create feedback object
        feedback = FeedBack(
            property_id=property_id,
            category=category,
            stars=stars,
            comment=comment,
            user_id=user.user_id
        )

        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)

        feedback.feedback_number = generate_feedback_number(feedback.id)
        await db.commit()

        # Step 2: Upload image if exists
        if image:
            file_dict = {
                "bytes": await image.read(),
                "filename": image.filename,
                "content_type": image.content_type
            }

            upload_result = await upload_feedback_image_as_png(
                file=file_dict,
                feedback_id=feedback.feedback_number
            )

            if "error" not in upload_result:
                feedback.image_path = upload_result["file_path"]
                await db.commit()

        # ⭐ Step 3: Send email to admin
        admin_email = "kaushikpalvai2004@gmail.com"  # <-- CHANGE THIS
        context = {
        "feedback_number": str(feedback.feedback_number),
        "user_id": str(user.user_id),
        "category": str(feedback.category),
        "stars": int(feedback.stars),
        "comment": str(feedback.comment),
        "property_id": str(feedback.property_id)
        }

        send_email_task.delay(
    "New Feedback Received",
    admin_email,
    "feedback_alert.html",
    context,
    header="Vibhoos PropCare"
)


        return {
            "message": "Feedback submitted successfully",
            "feedback_id": feedback.id,
            "feedback_number": feedback.feedback_number
        }
    except HTTPException:
        raise
    except JWTError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except Exception as e:
        print(str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

