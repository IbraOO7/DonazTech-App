from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from services.config import configs
from services.log_config import logger

engine = create_engine(
    configs.POSTGRES_URI, 
    pool_size=20,
    max_overflow=50,
    pool_timeout=30,
    pool_recycle=3600, 
    echo=False
)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    from databases.models.user import User
    from databases.models.services import Donation, ZakatConsultation
    from databases.models.charity import Charity
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database berhasil di buat")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)