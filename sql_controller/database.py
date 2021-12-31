from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import Settings

# SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
settings = Settings()

SQLALCHEMY_DATABASE_URL = "postgresql:"+":".join(settings.database_url.split(":")[1:])

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

#sqllite
# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
# )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()