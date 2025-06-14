from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime

from sqlalchemy.orm import sessionmaker, Session,declarative_base
from datetime import datetime

Base = declarative_base()
DATABASE_URL = "sqlite:///./test.db"  # or PostgreSQL/MySQL URL
engine = create_engine(DATABASE_URL, echo=True)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)






class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)  # Set manually later
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, index=True,default="ACTIVE")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__=="__main__":

    from sqlalchemy import create_engine

    DATABASE_URL = "sqlite:///./test.db"  # or PostgreSQL/MySQL URL
    engine = create_engine(DATABASE_URL, echo=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

