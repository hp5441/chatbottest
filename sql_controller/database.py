from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import Settings

# SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
settings = Settings()

SQLALCHEMY_DATABASE_URL = settings.database_url + ":5432/db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()