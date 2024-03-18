from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create engine
engine = create_engine("sqlite:///database.db", echo=False, logging_name="sqlalchemy")

# Create session maker
Session = sessionmaker(bind=engine)

# Create declarative base
Base = declarative_base()

from .models.ban import BanModel  # noqa
# Import models here
from .models.warning import WarningModel  # noqa

# Create tables
Base.metadata.create_all(engine)


# Function to get a session with rollback capability
@contextmanager
def get_session() -> Session: # type: ignore
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
