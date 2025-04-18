"""
�÷��������
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base


class Session(Base):
    """�÷�����"""
    
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # �÷��n����
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    location = Column(String, nullable=True)
    weather_conditions = Column(String, nullable=True)
    boat_type = Column(String, nullable=True)
    
    # ���nq�1
    track_distance = Column(Float, nullable=True)  # ����XM
    max_speed = Column(Float, nullable=True)  # ���XM
    avg_speed = Column(Float, nullable=True)  # ���XM
    
    # ��1
    avg_wind_speed = Column(Float, nullable=True)  # ���XM
    avg_wind_direction = Column(Float, nullable=True)  # �XM0-360	
    
    # ��"�^(	
    tags = Column(JSONB, nullable=True)
    
    # ��
    is_processed = Column(Boolean, default=False)  # ������
    
    # ��๿��
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ��������
    # project = relationship("Project", back_populates="sessions")
    # user = relationship("User", back_populates="sessions")
    # track_points = relationship("TrackPoint", back_populates="session")
    # wind_data = relationship("WindData", back_populates="session")
    # strategy_points = relationship("StrategyPoint", back_populates="session")
    
    def __repr__(self):
        return f"<Session {self.name}>"
