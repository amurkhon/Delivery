from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL, IS_PRODUCTION

engine = create_engine(DATABASE_URL, echo=not IS_PRODUCTION)

Base = declarative_base()
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency injection for database session
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()
