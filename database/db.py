import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def _build_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "appointments")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


DATABASE_URL = _build_database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)


def drop_db():
    Base.metadata.drop_all(bind=engine)


def drop_users_table():
    from users.models import User

    User.__table__.drop(bind=engine, checkfirst=True)
    init_db()


def drop_appointments_table():
    from appointments.models import Appointment

    Appointment.__table__.drop(bind=engine, checkfirst=True)
    init_db()


def drop_organizations_table():
    from organizations.models import Organization

    Organization.__table__.drop(bind=engine, checkfirst=True)
    init_db()


def drop_policies_table():
    from organizations.models import Policy

    Policy.__table__.drop(bind=engine, checkfirst=True)
    init_db()
