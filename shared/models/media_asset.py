from sqlalchemy import Column, Integer, String, Text
from shared.models.base import Base

class MediaAsset(Base):
    __tablename__ = "media_asset"

    id = Column(Integer, primary_key=True, autoincrement=True)
    media_blob_url = Column(Text, nullable=False)
    caption = Column(Text, nullable=True)
    media_type = Column(String(50), nullable=False)
