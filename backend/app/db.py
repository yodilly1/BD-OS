import os

from sqlmodel import Session, SQLModel, create_engine

sqlite_file_name = "bd_os.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
database_url = os.getenv("DATABASE_URL", sqlite_url)

# Fix for Heroku/Railway Postgres URLs starting with postgres://
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in database_url else {}
engine = create_engine(database_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
