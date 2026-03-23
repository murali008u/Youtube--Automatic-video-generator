from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base

class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    scenes = relationship("Scene", back_populates="script", cascade="all, delete-orphan")
    videos = relationship("Video", back_populates="script", cascade="all, delete-orphan")

class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id"))
    scene_number = Column(Integer)
    narration_text = Column(Text)
    image_prompt = Column(Text)
    duration_estimate = Column(Float, nullable=True)
    
    script = relationship("Script", back_populates="scenes")

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id"))
    status = Column(String, default="pending") # pending, generated, uploaded
    youtube_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    script = relationship("Script", back_populates="videos")
    analytics = relationship("Analytics", back_populates="video", uselist=False, cascade="all, delete-orphan")

class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    views = Column(Integer, default=0)
    watch_time_hours = Column(Float, default=0.0)
    ctr_percent = Column(Float, default=0.0)
    retention_percent = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    video = relationship("Video", back_populates="analytics")
