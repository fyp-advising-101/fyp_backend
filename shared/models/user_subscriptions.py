from sqlalchemy import Column, String, ForeignKey
from shared.models.base import Base

class UserSubscriptions(Base):
    __tablename__ = 'user_subscriptions'
    phone_number = Column(String(255), ForeignKey('users.phone_number', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, )
    category = Column(String(255), primary_key=True) # TO DO: make foreign key
