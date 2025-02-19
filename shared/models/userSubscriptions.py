from sqlalchemy import Column, String, ForeignKey
from shared.models.base import Base

class UserSubscriptions(Base):
    __tablename__ = 'user_subscriptions'
    phone_number = Column(String(255), ForeignKey('users.phone_number', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, )
    category = Column(String(255), ForeignKey('media_gen_options.category', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
