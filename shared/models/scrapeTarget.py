from sqlalchemy import Column, Integer, String, Float , Text ,DateTime
from shared.models.base import Base
from sqlalchemy.orm import relationship

class ScrapeTarget(Base):
    __tablename__ = 'scrape_targets'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False)
    type = Column(String(255), nullable=False)
    frequency = Column(Float, nullable=False)
    created_at = Column(DateTime)