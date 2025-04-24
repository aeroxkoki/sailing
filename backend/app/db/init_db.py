# -*- coding: utf-8 -*-
"""
データベース初期化
"""

import logging
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine


def init_db(db: Session) -> None:
    """初期データベース設定"""
    # テーブル作成
    Base.metadata.create_all(bind=engine)
    
    # ここに初期データ投入ロジックを追加
    logging.info("データベース初期化完了")
