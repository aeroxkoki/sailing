# -*- coding: utf-8 -*-
"""
セッション詳細表示と編集機能のデモアプリ
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List, Callable
import uuid
import datetime
import os
import sys
import json

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sailing_data_processor.project.project_manager import ProjectManager, Project, Session
from sailing_data_processor.project.session_manager import SessionManager
from ui.components.project.session_list import detailed_session_list_view
from ui.components.project.session_details import SessionDetailsView
from ui.components.project.session_editor import SessionEditorView
from ui.pages.session_management import session_management_page

def create_demo_data(project_manager: ProjectManager) -> None:
    """デモ用のプロジェクトとセッションを作成"""
    # 既にデモデータが作成されているか確認
    if hasattr(st.session_state, 'demo_data_created') and st.session_state.demo_data_created:
        return
    
    # デモプロジェクトを作成
    project1 = Project(
        project_id=str(uuid.uuid4()),
        name="東京湾練習セッション",
        description="東京湾エリアでの練習セッション集",
        created_at=datetime.datetime.now().isoformat(),
        updated_at=datetime.datetime.now().isoformat()
    )
    
    project2 = Project(
        project_id=str(uuid.uuid4()),
        name="江の島レース2024",
        description="2024年江の島レースに関連するセッション",
        created_at=datetime.datetime.now().isoformat(),
        updated_at=datetime.datetime.now().isoformat()
    )
    
    # プロジェクトをプロジェクトマネージャーに保存
    project_manager.save_project(project1)
    project_manager.save_project(project2)
    
    # デモセッションを作成
    sessions = []
    
    # セッション1
    session1 = Session(
        session_id=str(uuid.uuid4()),
        name="東京湾練習 - 風強め",
        description="風速15ノット程度での練習セッション",
        metadata={
            "location": "東京湾",
            "event_date": datetime.datetime(2024, 3, 15).isoformat(),
            "boat_type": "470",
            "crew_info": "舵手: 山田, クルー: 田中",
            "wind_min": 12.5,
            "wind_max": 18.2,
            "weather": "晴れ",
            "sea_state": "やや波あり",
            "avg_wind_speed": 14.8
        },
        status="validated",
        category="training",
        tags=["training", "strong_wind", "upwind", "downwind"],
        created_at=datetime.datetime(2024, 3, 15, 10, 0).isoformat(),
        updated_at=datetime.datetime(2024, 3, 15, 16, 30).isoformat()
    )
    
    # セッション2
    session2 = Session(
        session_id=str(uuid.uuid4()),
        name="東京湾練習 - 風弱め",
        description="風速5-8ノット程度での練習セッション",
        metadata={
            "location": "東京湾",
            "event_date": datetime.datetime(2024, 3, 16).isoformat(),
            "boat_type": "470",
            "crew_info": "舵手: 山田, クルー: 田中",
            "wind_min": 5.2,
            "wind_max": 8.3,
            "weather": "晴れ",
            "sea_state": "穏やか",
            "avg_wind_speed": 6.7
        },
        status="validated",
        category="training",
        tags=["training", "light_wind", "tacking", "gybing"],
        created_at=datetime.datetime(2024, 3, 16, 10, 0).isoformat(),
        updated_at=datetime.datetime(2024, 3, 16, 15, 45).isoformat()
    )
    
    # セッション3
    session3 = Session(
        session_id=str(uuid.uuid4()),
        name="江の島レース - 予選1",
        description="江の島レース予選第1レース",
        metadata={
            "location": "江の島",
            "event_date": datetime.datetime(2024, 4, 10).isoformat(),
            "boat_type": "470",
            "crew_info": "舵手: 山田, クルー: 佐藤",
            "wind_min": 10.1,
            "wind_max": 12.8,
            "weather": "曇り",
            "sea_state": "中程度の波",
            "avg_wind_speed": 11.3,
            "result": "3位",
            "course_type": "olimpic"
        },
        status="analyzed",
        category="race",
        tags=["race", "qualification", "medium_wind"],
        created_at=datetime.datetime(2024, 4, 10, 9, 30).isoformat(),
        updated_at=datetime.datetime(2024, 4, 10, 14, 45).isoformat()
    )
    
    # セッション4
    session4 = Session(
        session_id=str(uuid.uuid4()),
        name="江の島レース - 予選2",
        description="江の島レース予選第2レース",
        metadata={
            "location": "江の島",
            "event_date": datetime.datetime(2024, 4, 10).isoformat(),
            "boat_type": "470",
            "crew_info": "舵手: 山田, クルー: 佐藤",
            "wind_min": 8.5,
            "wind_max": 11.2,
            "weather": "曇り時々晴れ",
            "sea_state": "中程度の波",
            "avg_wind_speed": 9.8,
            "result": "2位",
            "course_type": "olimpic"
        },
        status="analyzed",
        category="race",
        tags=["race", "qualification", "medium_wind"],
        created_at=datetime.datetime(2024, 4, 10, 15, 0).isoformat(),
        updated_at=datetime.datetime(2024, 4, 10, 17, 30).isoformat()
    )
    
    # セッション5
    session5 = Session(
        session_id=str(uuid.uuid4()),
        name="江の島レース - 決勝",
        description="江の島レース決勝レース",
        metadata={
            "location": "江の島",
            "event_date": datetime.datetime(2024, 4, 11).isoformat(),
            "boat_type": "470",
            "crew_info": "舵手: 山田, クルー: 佐藤",
            "wind_min": 14.2,
            "wind_max": 17.6,
            "weather": "晴れ",
            "sea_state": "やや荒れ気味",
            "avg_wind_speed": 15.9,
            "result": "1位",
            "course_type": "olimpic"
        },
        status="completed",
        category="race",
        tags=["race", "final", "strong_wind", "victory"],
        created_at=datetime.datetime(2024, 4, 11, 13, 0).isoformat(),
        updated_at=datetime.datetime(2024, 4, 11, 16, 45).isoformat()
    )
    
    sessions = [session1, session2, session3, session4, session5]
    
    # セッションをプロジェクトマネージャーに保存
    for session in sessions:
        project_manager.save_session(session)
    
    # セッションをプロジェクトに関連付け
    project1.add_session(session1.session_id)
    project1.add_session(session2.session_id)
    project2.add_session(session3.session_id)
    project2.add_session(session4.session_id)
    project2.add_session(session5.session_id)
    
    # 更新したプロジェクトを保存
    project_manager.save_project(project1)
    project_manager.save_project(project2)
    
    # デモデータ作成済みフラグを設定
    st.session_state.demo_data_created = True

def main():
    """メイン関数"""
    st.set_page_config(
        page_title="セッション詳細表示・編集デモ",
        page_icon="🚢",
        layout="wide"
    )
    
    # プロジェクト管理クラスとセッション管理クラスを初期化
    if "project_manager" not in st.session_state:
        st.session_state.project_manager = ProjectManager()
    
    if "session_manager" not in st.session_state:
        st.session_state.session_manager = SessionManager(st.session_state.project_manager)
    
    # デモデータを作成
    create_demo_data(st.session_state.project_manager)
    
    # セッション管理ページを表示
    session_management_page()

if __name__ == "__main__":
    main()
