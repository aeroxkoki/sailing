# -*- coding: utf-8 -*-
"""
拡張されたセッション管理UIコンポーネントのデモアプリ

拡張されたセッションリストおよび詳細表示コンポーネントをテストします。
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
from ui.components.session.session_list import SessionListComponent
from ui.components.session.session_detail import SessionDetailComponent

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
            "avg_wind_speed": 14.8,
            "importance": "high",
            "completion_percentage": 100
        },
        status="active",
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
            "avg_wind_speed": 6.7,
            "importance": "normal",
            "completion_percentage": 85
        },
        status="active",
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
            "course_type": "olimpic",
            "importance": "high",
            "completion_percentage": 100
        },
        status="in_progress",
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
            "course_type": "olimpic",
            "importance": "high",
            "completion_percentage": 100
        },
        status="in_progress",
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
            "course_type": "olimpic",
            "importance": "critical",
            "completion_percentage": 100
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
    
    # 関連セッションを設定
    session_manager = SessionManager(project_manager)
    
    # session3とsession4を関連付け（同じ日のレース）
    session_manager.add_related_session(session3.session_id, session4.session_id, "related")
    session_manager.add_related_session(session4.session_id, session3.session_id, "related")
    
    # session3とsession5を関連付け（予選と決勝）
    session_manager.add_related_session(session3.session_id, session5.session_id, "related")
    session_manager.add_related_session(session5.session_id, session3.session_id, "related")
    
    # session4とsession5を関連付け（予選と決勝）
    session_manager.add_related_session(session4.session_id, session5.session_id, "related")
    session_manager.add_related_session(session5.session_id, session4.session_id, "related")
    
    # デモデータ作成済みフラグを設定
    st.session_state.demo_data_created = True
    st.success("デモデータを作成しました")

def main():
    """メイン関数"""
    st.set_page_config(
        page_title="拡張セッション管理UIデモ",
        page_icon="🚢",
        layout="wide"
    )
    
    st.title("拡張セッション管理UI コンポーネントデモ")
    st.caption("セッションリストコンポーネントとセッション詳細コンポーネントの機能デモンストレーション")
    
    # プロジェクト管理クラスとセッション管理クラスを初期化
    if "project_manager" not in st.session_state:
        st.session_state.project_manager = ProjectManager()
    
    if "session_manager" not in st.session_state:
        st.session_state.session_manager = SessionManager(st.session_state.project_manager)
    
    # デモデータを作成
    create_demo_data(st.session_state.project_manager)
    
    # 状態管理
    if "view_state" not in st.session_state:
        st.session_state.view_state = "list"  # list または detail
    
    if "selected_session_id" not in st.session_state:
        st.session_state.selected_session_id = None
    
    # サイドバー（状態切り替え）
    with st.sidebar:
        st.subheader("表示モード")
        
        if st.session_state.view_state == "detail" and st.session_state.selected_session_id:
            if st.button("セッションリストに戻る", use_container_width=True):
                st.session_state.view_state = "list"
                st.session_state.selected_session_id = None
                st.rerun()
                
            # セッション選択情報の表示
            st.divider()
            st.info(f"セッションID: {st.session_state.selected_session_id}")
            
            session = st.session_state.project_manager.get_session(st.session_state.selected_session_id)
            if session:
                st.write(f"セッション名: {session.name}")
        
        # デモ用の設定変更
        st.divider()
        st.subheader("デモ設定")
        
        # カード表示/リスト表示の切り替え
        if st.session_state.view_state == "list":
            view_type = st.radio(
                "表示タイプ",
                options=["カード表示", "リスト表示"],
                index=0 if not hasattr(st.session_state, "demo_view_type") or st.session_state.demo_view_type == "card" else 1,
                key="demo_view_type_selector"
            )
            st.session_state.demo_view_type = "card" if view_type == "カード表示" else "list"
    
    # セッション選択時のコールバック
    def on_session_select(session_id):
        st.session_state.selected_session_id = session_id
        st.session_state.view_state = "detail"
        st.rerun()
    
    # セッションアクション時のコールバック
    def on_session_action(session_id, action):
        if action == "edit":
            st.info(f"セッション {session_id} の編集がリクエストされました")
        elif action == "delete":
            st.warning(f"セッション {session_id} の削除がリクエストされました")
    
    # 詳細画面から戻るコールバック
    def on_close():
        st.session_state.view_state = "list"
        st.session_state.selected_session_id = None
        st.rerun()
    
    # リストビューの表示
    if st.session_state.view_state == "list":
        # 拡張されたセッションリストコンポーネントを使用
        session_list = SessionListComponent(
            key="demo_session_list",
            session_manager=st.session_state.session_manager,
            on_session_select=on_session_select,
            on_session_action=on_session_action
        )
        
        # カードビュー/リストビューの設定を反映
        if hasattr(st.session_state, "demo_view_type"):
            st.session_state[f"demo_session_list_view_type"] = st.session_state.demo_view_type
        
        # セッションリストを表示
        session_list.render()
    
    # 詳細ビューの表示
    elif st.session_state.view_state == "detail" and st.session_state.selected_session_id:
        # 拡張されたセッション詳細コンポーネントを使用
        session_detail = SessionDetailComponent(
            key="demo_session_detail",
            session_manager=st.session_state.session_manager,
            project_manager=st.session_state.project_manager,
            on_edit=lambda session_id: on_session_action(session_id, "edit"),
            on_delete=lambda session_id: on_session_action(session_id, "delete"),
            on_close=on_close
        )
        
        # セッション詳細を表示
        session_detail.render(st.session_state.selected_session_id)

if __name__ == "__main__":
    main()
