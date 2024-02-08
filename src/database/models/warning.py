from ..database import Base
from sqlalchemy import Column, Integer, String, DateTime
from discord import Member
from datetime import datetime

class WarningModel(Base):
    __tablename__ = 'warnings'
    warningId = Column(Integer, primary_key=True)
    memberId = Column(Integer)
    moderatorId = Column(Integer)
    reason = Column(String)
    time = Column(DateTime)
    def __init__(self, member: Member, moderator: Member, reason: str):
        self.memberId = member.id
        self.moderatorId = moderator.id
        self.reason = reason
        self.time = datetime.now()
