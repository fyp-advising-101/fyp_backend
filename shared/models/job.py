from sqlalchemy import Column, Integer, String, Date
from shared.models.base import Base

class Job(Base):
    __tablename__ = 'job'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(255), nullable=False)
    task_id = Column(String(255), nullable=False)
    status = Column(Integer, nullable=False)
    scheduled_date = Column(Date, nullable=False)
    error_message = Column(String(255), nullable=True)
    created_at = Column(Date, nullable=False)
    updated_at = Column(Date, nullable=False)
