import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def update_user_forms():
    async with SessionLocal() as session:
        query_true = """
        UPDATE "PropCare".users u
        SET is_pdfilled = TRUE
        FROM "PropCare".personal_details p
        WHERE u.id = p.user_id;
        """

        query_false = """
        UPDATE "PropCare".users u
        SET is_pdfilled = FALSE
        WHERE NOT EXISTS (
            SELECT 1
            FROM "PropCare".personal_details p
            WHERE p.user_id = u.id
        );
        """

        await session.execute(query_true)
        await session.execute(query_false)
        await session.commit()
        print("✅ Synced user form statuses successfully.")

if __name__ == "__main__":
    asyncio.run(update_user_forms())
