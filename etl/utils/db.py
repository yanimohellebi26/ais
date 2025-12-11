import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

DB_DRIVER = os.getenv("POSTGRES_DRIVER", "psycopg")  # Default psycopg
ENV = os.getenv("ENV_MODE", "local")
HOST = "localhost" if ENV == "local" else os.getenv("DB_HOST", "ais-db")

USER = os.getenv("POSTGRES_USER")
PASSWORD = quote_plus(os.getenv("POSTGRES_PASSWORD"))  # <== encode le mot de passe
PORT = os.getenv("POSTGRES_PORT")
DB = os.getenv("POSTGRES_DB")

DATABASE_URL = f"postgresql+{DB_DRIVER}://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}"

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
