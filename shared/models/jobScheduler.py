from sqlalchemy import Column, Integer, String, Float , Text ,DateTime
from shared.models.base import Base
from sqlalchemy.orm import relationship

class JobScheduler(Base):
    __tablename__ = 'job_scheduler'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(255), nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    status = Column(String(255), nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


