# db.py
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()


DB_DRIVER = os.getenv("POSTGRES_DRIVER", "psycopg")  # Default psycopg
DATABASE_URL = (
    f"postgresql+{DB_DRIVER}://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)
print(DATABASE_URL)

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
