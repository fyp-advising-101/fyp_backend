from sqlalchemy import Column, String
from shared.models.base import Base

class Users(Base):
    __tablename__ = 'users'
    phone_number = Column(String(255), primary_key=True)
    name = Column(String(255))
