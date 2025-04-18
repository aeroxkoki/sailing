"""
�������
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, Float, DateTime, ForeignKey, Integer, Boolean, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base


class WindData(Base):
    """�������"""
    
    __tablename__ = "wind_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    
    # B��1
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Mn�1
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # ��
    wind_direction = Column(Float, nullable=False)  # �XM0-360	
    wind_speed = Column(Float, nullable=False)  # ���XM
    
    # �<'����1
    confidence = Column(Float, nullable=True)  # 0-1n$
    source = Column(String, nullable=True)  # 'estimated', 'measured', 'combined'
    estimation_method = Column(String, nullable=True)  # (W_������
    
    # ������
    metadata = Column(JSONB, nullable=True)
    
    # ��๿��
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ��������
    # session = relationship("Session", back_populates="wind_data")
    
    def __repr__(self):
        return f"<WindData {self.timestamp}: {self.wind_speed}kts @ {self.wind_direction}�>"


class WindField(Base):
    """�n4�����hSn��1	"""
    
    __tablename__ = "wind_fields"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    
    # B��1
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # �L�1
    min_latitude = Column(Float, nullable=False)
    max_latitude = Column(Float, nullable=False)
    min_longitude = Column(Float, nullable=False)
    max_longitude = Column(Float, nullable=False)
    
    # ����-�
    grid_size = Column(Float, nullable=False)  # ���ɵ���XM	
    resolution = Column(Integer, nullable=False)  # �Ϧ
    
    # �n4���Ф��WOoJSONg<	
    field_data = Column(JSONB, nullable=False)
    
    # ���
    generation_method = Column(String, nullable=True)  # 'interpolation', 'model', 'combined'
    
    # ��
    is_validated = Column(Boolean, default=False)
    
    # ��๿��
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ��������
    # session = relationship("Session", back_populates="wind_fields")
    
    def __repr__(self):
        return f"<WindField {self.timestamp} ({self.resolution}x{self.resolution})>"
