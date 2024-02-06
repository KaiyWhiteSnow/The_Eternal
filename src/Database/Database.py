from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.orm.state import InstanceState

from Database.Models import UserModel
from Database.Base import Base  
from Config.config import DiscordConfig


engine = create_engine("sqlite:///DataBase.db", echo=True)
Session = sessionmaker(bind=engine)
session = Session()
Base.metadata.create_all(engine)

class Database:    
    @classmethod
    async def syncDatabase(cls, session_instance, server_users):
        existing_users = session_instance.query(UserModel.User).all()

        for user in server_users:
            existing_user = next((u for u in existing_users if u.UID == user.id), None)

            if existing_user is None:
                new_user = UserModel.User(UID=user.id)
                session_instance.add(new_user)
                session_instance.commit()
                print(f"{DiscordConfig.getDatabasePrefix()} Added user {user.id} to the database.")
