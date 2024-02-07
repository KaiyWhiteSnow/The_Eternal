from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from Database.Base import Base
from Database.Models.WarningModel import CustomWarning

class User(Base):
    __tablename__ = "userModel"

    UID = Column(Integer, nullable=False, unique=True, primary_key=True)
    Warnings = relationship('CustomWarning', back_populates='user', cascade='all, delete-orphan', passive_deletes=True)
    Banned = Column(Boolean, nullable=False, default=False, unique=False)