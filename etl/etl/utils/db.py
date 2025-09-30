# db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

# Use psycopg default, set pg8000 for arm user in .env
DB_DRIVER = os.getenv("DB_DRIVER", "psycopg")  # Default psycopg
DATABASE_URL = (
    f"postgresql+{DB_DRIVER}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

# Engine global SQLAlchemy
engine = create_engine(DATABASE_URL, echo=False, future=True)

def get_session() -> Session:
    """
    Context manager SQLAlchemy :
        with get_session() as session:
            session.add(obj)   # ORM
            session.query(User).all()  # ORM
            session.execute(text(...)) # SQL brut
    """
    return Session(engine)
