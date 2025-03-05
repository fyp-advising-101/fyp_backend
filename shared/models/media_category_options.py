from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from shared.models.base import Base
class MediaCategoryOptions(Base):
    __tablename__ = "media_category_options"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    prompt_text = Column(Text, nullable=False)
    chroma_query = Column(Text, nullable=False)  # New column to store the question
    # Foreign key referencing MediaGenOptions.id
    option_id = Column(Integer, ForeignKey("media_gen_options.id"), nullable=False)
    # Relationship to the parent table
    media_gen_option = relationship("MediaGenOptions", back_populates="category_options") 