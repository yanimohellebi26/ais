import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()


DB_DRIVER = os.getenv("POSTGRES_DRIVER", "psycopg")  # Default psycopg
ENV = os.getenv("ENV_MODE","local")
HOST = "localhost" if ENV == "local" else os.getenv("DB_HOST", "ais-db")
DATABASE_URL = (
    f"postgresql+{DB_DRIVER}://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{HOST}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
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
