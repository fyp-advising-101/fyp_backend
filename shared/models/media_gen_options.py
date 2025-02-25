from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from shared.models.base import Base

class MediaGenOptions(Base):
    __tablename__ = "media_gen_options"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(255), nullable=False)
    # Note: 'type' is a Python built-in name, so consider renaming to avoid confusion,
    # for example: `media_type = Column(String(255), nullable=False)`
    media_type = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)

    # Relationship back to MediaCategoryOptions (one-to-many)
    category_options = relationship("MediaCategoryOptions", back_populates="media_gen_option")
