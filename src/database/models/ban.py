from ..database import Base
from sqlalchemy import Column, Integer, String, DateTime
from discord import Member
from datetime import datetime

class BanModel(Base):
    __tablename__ = 'bans'
    banId = Column(Integer, primary_key=True)
    memberId = Column(Integer)
    moderatorId = Column(Integer)
    reason = Column(String)
    time = Column(DateTime)
    expires = Column(DateTime, nullable=True) # Default is None
    def __init__(self, member: Member, moderator: Member, reason: str, expires: DateTime | None = None):
        self.memberId = member.id
        self.moderatorId = moderator.id
        self.reason = reason
        self.time = datetime.now()
        self.expires = expires
