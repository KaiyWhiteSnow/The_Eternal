from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from Database.Base import Base

class Warning(Base):
    __tablename__ = "warningModel"

    WarningID = Column(Integer, nullable=False, unique=True, primary_key=True)
    UID = Column(ForeignKey('userModel.UID', ondelete='CASCADE'), nullable=False)
    Reason = Column(String, nullable=False, unique=False)
    Count = Column(Integer, nullable=False, default=0)
    user = relationship('User', back_populates='Warnings')