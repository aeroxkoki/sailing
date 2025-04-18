"""
&eݤ��������
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, Float, DateTime, ForeignKey, Integer, Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base


class StrategyPoint(Base):
    """&eݤ�����z�ńj@b	"""
    
    __tablename__ = "strategy_points"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    
    # B��1
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Mn�1
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # &e�1
    type = Column(String, nullable=False)  # 'tack', 'gybe', 'mark_rounding', 'layline', 'start', 'finish'
    subtype = Column(String, nullable=True)  # ��s0j^
    
    # U��1
    score = Column(Float, nullable=True)  # U����0-100	
    is_optimal = Column(Boolean, default=False)  #  ijx�`c_K
    optimal_timestamp = Column(DateTime, nullable=True)  #  ij����
    optimal_latitude = Column(Float, nullable=True)  #  ijMn�	
    optimal_longitude = Column(Float, nullable=True)  #  ijMnL�	
    time_loss = Column(Float, nullable=True)  # B�1�	
    distance_loss = Column(Float, nullable=True)  # ��1����	
    
    # ��ƭ���1
    boat_speed = Column(Float, nullable=True)  # G���	
    boat_heading = Column(Float, nullable=True)  # GM�	
    wind_speed = Column(Float, nullable=True)  # ����	
    wind_direction = Column(Float, nullable=True)  # ��	
    
    # �����
    notes = Column(Text, nullable=True)
    
    # s0���
    details = Column(JSONB, nullable=True)
    
    # ��๿��
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ��������
    # session = relationship("Session", back_populates="strategy_points")
    
    def __repr__(self):
        return f"<StrategyPoint {self.type} @ {self.timestamp}>"


class StrategyAnalysis(Base):
    """&e�P�����÷��hSn�	"""
    
    __tablename__ = "strategy_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, unique=True)
    
    # ��,�1
    analysis_version = Column(String, nullable=False)  # �����n�����
    
    # ����1
    overall_score = Column(Float, nullable=True)  # ����0-100	
    tacking_score = Column(Float, nullable=True)  # �ïU�
    sailing_line_score = Column(Float, nullable=True)  # ������U�
    mark_rounding_score = Column(Float, nullable=True)  # �����ǣ�U�
    start_score = Column(Float, nullable=True)  # ����U�
    
    # q�1
    total_strategy_points = Column(Integer, nullable=True)  # &eݤ���p
    optimal_strategy_points = Column(Integer, nullable=True)  #  i`c_&eݤ��p
    total_time_loss = Column(Float, nullable=True)  # �B�1�	
    
    # �s0���
    analysis_data = Column(JSONB, nullable=True)
    
    # �����1
    report_summary = Column(Text, nullable=True)
    improvement_suggestions = Column(JSONB, nullable=True)
    
    # ��๿��
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ��������
    # session = relationship("Session", back_populates="strategy_analysis")
    
    def __repr__(self):
        return f"<StrategyAnalysis {self.session_id}: {self.overall_score}>"
