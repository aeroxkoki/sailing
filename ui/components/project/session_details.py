"""
ui.components.project.session_details

セッション詳細表示のUIコンポーネント
"""

import streamlit as st
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
import pandas as pd
import folium
from streamlit_folium import folium_static
import plotly.express as px
import plotly.graph_objects as go

from sailing_data_processor.project.project_manager import ProjectManager, Session
from sailing_data_processor.project.session_manager import SessionManager
from ui.components.common.card import card


def format_datetime(iso_datetime: str) -> str:
    """ISO形式の日時を表示用にフォーマット"""
    try:
        dt = datetime.fromisoformat(iso_datetime)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return iso_datetime


class SessionDetailsView:
    """
    セッション詳細表示コンポーネント
    
    選択されたセッションの詳細情報を表示し、
    編集、削除、タグ付けなどの機能を提供します。
    
    Parameters
    ----------
    project_manager : ProjectManager
        プロジェクト管理クラスのインスタンス
    session_manager : SessionManager
        セッション管理クラスのインスタンス
    on_edit : Optional[Callable[[str], None]], optional
        編集ボタン押下時のコールバック関数, by default None
    on_delete : Optional[Callable[[str], None]], optional
        削除ボタン押下時のコールバック関数, by default None
    on_back : Optional[Callable[[], None]], optional
        戻るボタン押下時のコールバック関数, by default None
    """
    
    def __init__(
        self,
        project_manager: ProjectManager,
        session_manager: SessionManager,
        on_edit: Optional[Callable[[str], None]] = None,
        on_delete: Optional[Callable[[str], None]] = None,
        on_back: Optional[Callable[[], None]] = None,
    ):
        self.project_manager = project_manager
        self.session_manager = session_manager
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_back = on_back
    
    def get_associated_projects(self, session_id: str) -> List[Dict[str, Any]]:
        """
        セッションが関連付けられているプロジェクトのリストを取得
        
        Parameters
        ----------
        session_id : str
            セッションID
            
        Returns
        -------
        List[Dict[str, Any]]
            関連プロジェクト情報のリスト
        """
        projects = self.session_manager.get_projects_containing_session(session_id)
        
        return [
            {
                "id": project.project_id,
                "name": project.name,
                "description": project.description,
                "created_at": format_datetime(project.created_at)
            }
            for project in projects
        ]
    
    def render_map_preview(self, session_id: str):
        """
        セッションのGPSデータをマップでプレビュー表示
        
        Parameters
        ----------
        session_id : str
            セッションID
        """
        # GPSデータの取得
        container = self.project_manager.load_container_from_session(session_id)
        
        if container is None or container.df.empty:
            st.info("このセッションにはGPSデータがありません。")
            return
        
        # 緯度経度データを確認
        df = container.df
        if 'latitude' not in df.columns or 'longitude' not in df.columns:
            st.info("このセッションには座標データがありません。")
            return
        
        # 緯度経度の平均値を計算してマップの中心を決定
        center_lat = df['latitude'].mean()
        center_lon = df['longitude'].mean()
        
        # Foliumマップの作成
        m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
        
        # ルートをポリラインで描画
        route_points = df[['latitude', 'longitude']].values.tolist()
        folium.PolyLine(
            route_points,
            color='blue',
            weight=3,
            opacity=0.7
        ).add_to(m)
        
        # 開始点のマーカー
        folium.Marker(
            location=[df['latitude'].iloc[0], df['longitude'].iloc[0]],
            popup="開始点",
            icon=folium.Icon(color='green', icon='play')
        ).add_to(m)
        
        # 終了点のマーカー
        folium.Marker(
            location=[df['latitude'].iloc[-1], df['longitude'].iloc[-1]],
            popup="終了点",
            icon=folium.Icon(color='red', icon='stop')
        ).add_to(m)
        
        # マップの表示
        folium_static(m)
    
    def render_chart_preview(self, session_id: str):
        """
        セッションのデータをチャートでプレビュー表示
        
        Parameters
        ----------
        session_id : str
            セッションID
        """
        # データの取得
        container = self.project_manager.load_container_from_session(session_id)
        
        if container is None or container.df.empty:
            st.info("このセッションには分析可能なデータがありません。")
            return
        
        df = container.df
        
        # 分析に利用可能なデータ項目を確認
        available_metrics = []
        if 'speed' in df.columns:
            available_metrics.append('speed')
        if 'course' in df.columns:
            available_metrics.append('course')
        if 'heading' in df.columns:
            available_metrics.append('heading')
        if 'wind_speed' in df.columns:
            available_metrics.append('wind_speed')
        if 'wind_direction' in df.columns:
            available_metrics.append('wind_direction')
        
        if not available_metrics:
            st.info("このセッションにはチャート表示可能なデータがありません。")
            return
        
        # タイムスタンプの確認
        has_timestamp = 'timestamp' in df.columns
        
        # タブで表示を切り替える
        chart_tabs = st.tabs(["速度", "方位角", "風情報"])
        
        # 速度タブ
        with chart_tabs[0]:
            if 'speed' in df.columns:
                fig = px.line(
                    df, 
                    x='timestamp' if has_timestamp else df.index, 
                    y='speed',
                    title='速度の推移',
                    labels={'speed': '速度 (kt)', 'timestamp': '時間'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("速度データがありません。")
        
        # 方位角タブ
        with chart_tabs[1]:
            if 'course' in df.columns or 'heading' in df.columns:
                fig = go.Figure()
                
                if 'course' in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df['timestamp'] if has_timestamp else df.index,
                        y=df['course'],
                        mode='lines',
                        name='対地進路'
                    ))
                
                if 'heading' in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df['timestamp'] if has_timestamp else df.index,
                        y=df['heading'],
                        mode='lines',
                        name='船首方位'
                    ))
                
                fig.update_layout(
                    title='方位角の推移',
                    xaxis_title='時間',
                    yaxis_title='方位角 (度)',
                    yaxis=dict(range=[0, 360])
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("方位角データがありません。")
        
        # 風情報タブ
        with chart_tabs[2]:
            if 'wind_speed' in df.columns or 'wind_direction' in df.columns:
                fig = go.Figure()
                
                if 'wind_speed' in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df['timestamp'] if has_timestamp else df.index,
                        y=df['wind_speed'],
                        mode='lines',
                        name='風速'
                    ))
                    
                    fig.update_layout(
                        title='風速の推移',
                        xaxis_title='時間',
                        yaxis_title='風速 (kt)'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                if 'wind_direction' in df.columns:
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(
                        x=df['timestamp'] if has_timestamp else df.index,
                        y=df['wind_direction'],
                        mode='lines',
                        name='風向'
                    ))
                    
                    fig2.update_layout(
                        title='風向の推移',
                        xaxis_title='時間',
                        yaxis_title='風向 (度)',
                        yaxis=dict(range=[0, 360])
                    )
                    st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("風情報データがありません。")
    
    def render_data_summary(self, session_id: str):
        """
        セッションのデータサマリーを表示
        
        Parameters
        ----------
        session_id : str
            セッションID
        """
        # データの取得
        container = self.project_manager.load_container_from_session(session_id)
        
        if container is None or container.df.empty:
            st.info("このセッションにはデータがありません。")
            return
        
        df = container.df
        
        # データポイント数
        num_points = len(df)
        
        # 時間範囲
        time_range = None
        if 'timestamp' in df.columns:
            start_time = df['timestamp'].min()
            end_time = df['timestamp'].max()
            duration = end_time - start_time
            hours = duration.total_seconds() / 3600
            time_range = f"{start_time.strftime('%Y-%m-%d %H:%M')} から {end_time.strftime('%Y-%m-%d %H:%M')} ({hours:.2f}時間)"
        
        # 距離の計算
        total_distance = None
        if 'distance' in df.columns:
            total_distance = df['distance'].sum()
        elif 'latitude' in df.columns and 'longitude' in df.columns:
            # 緯度経度から距離を概算
            from math import sin, cos, sqrt, atan2, radians
            
            # 地球の半径 (km)
            R = 6371.0
            
            total_distance = 0
            for i in range(1, len(df)):
                lat1 = radians(df['latitude'].iloc[i-1])
                lon1 = radians(df['longitude'].iloc[i-1])
                lat2 = radians(df['latitude'].iloc[i])
                lon2 = radians(df['longitude'].iloc[i])
                
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                
                a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                
                distance = R * c
                total_distance += distance
        
        # 平均速度
        avg_speed = None
        if 'speed' in df.columns:
            avg_speed = df['speed'].mean()
        
        # 最大速度
        max_speed = None
        if 'speed' in df.columns:
            max_speed = df['speed'].max()
        
        # 平均風速
        avg_wind = None
        if 'wind_speed' in df.columns:
            avg_wind = df['wind_speed'].mean()
        
        # カード形式でサマリー表示
        col1, col2 = st.columns(2)
        
        with col1:
            with card("基本情報"):
                st.markdown(f"**データポイント数:** {num_points}")
                if time_range:
                    st.markdown(f"**時間範囲:** {time_range}")
                if total_distance:
                    st.markdown(f"**総距離:** {total_distance:.2f} km")
        
        with col2:
            with card("パフォーマンス指標"):
                if avg_speed:
                    st.markdown(f"**平均速度:** {avg_speed:.2f} kt")
                if max_speed:
                    st.markdown(f"**最大速度:** {max_speed:.2f} kt")
                if avg_wind:
                    st.markdown(f"**平均風速:** {avg_wind:.2f} kt")
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        セッションの編集履歴を取得
        
        Parameters
        ----------
        session_id : str
            セッションID
            
        Returns
        -------
        List[Dict[str, Any]]
            編集履歴のリスト
        """
        # 実際の実装では履歴を取得する処理を行う
        # この関数はモックデータを返す
        return [
            {
                "timestamp": "2025-03-28 14:23",
                "user": "user1",
                "action": "メタデータ編集",
                "changes": {
                    "location": {"old": "東京湾", "new": "横浜ベイ"},
                    "boat_type": {"old": "470", "new": "49er"}
                }
            },
            {
                "timestamp": "2025-03-27 09:15",
                "user": "user2",
                "action": "タグ追加",
                "changes": {
                    "tags": {"old": "race", "new": "race, competition, final"}
                }
            },
            {
                "timestamp": "2025-03-26 16:42",
                "user": "user1",
                "action": "セッション作成",
                "changes": {}
            }
        ]
    
    def render(self, session_id: str):
        """
        コンポーネントのレンダリング
        
        Parameters
        ----------
        session_id : str
            表示するセッションのID
        """
        session = self.project_manager.get_session(session_id)
        if not session:
            st.error(f"セッションが見つかりません: {session_id}")
            return
        
        # タイトルとアクションボタン
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title(f"セッション: {session.name}")
            st.caption(f"ID: {session_id}")
        
        with col2:
            cols = st.columns(3)
            with cols[0]:
                if st.button("📝 編集", key="session_details_edit_btn", use_container_width=True):
                    if self.on_edit:
                        self.on_edit(session_id)
            
            with cols[1]:
                if st.button("🗑️ 削除", key="session_details_delete_btn", use_container_width=True):
                    # 削除確認ダイアログ
                    if "confirm_delete_session" not in st.session_state:
                        st.session_state.confirm_delete_session = False
                    
                    st.session_state.confirm_delete_session = True
            
            with cols[2]:
                if st.button("← 戻る", key="session_details_back_btn", use_container_width=True):
                    if self.on_back:
                        self.on_back()
        
        # ステータスバッジの表示
        status_colors = {
            "new": "blue", 
            "validated": "green", 
            "analyzed": "violet", 
            "completed": "orange"
        }
        status_color = status_colors.get(session.status, "gray")
        st.markdown(
            f"<span style='background-color:{status_color};color:white;padding:0.2rem 0.5rem;border-radius:0.5rem;font-size:0.8rem;margin-right:0.5rem'>{session.status or 'なし'}</span>"
            f"<span style='background-color:#555;color:white;padding:0.2rem 0.5rem;border-radius:0.5rem;font-size:0.8rem'>{session.category or 'なし'}</span>",
            unsafe_allow_html=True
        )
        
        # 削除確認ダイアログ
        if st.session_state.get("confirm_delete_session", False):
            with st.container():
                st.warning(f"セッション「{session.name}」を削除しますか？この操作は元に戻せません。")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("削除を確定", key="confirm_delete_yes", use_container_width=True):
                        if self.on_delete:
                            self.on_delete(session_id)
                        st.session_state.confirm_delete_session = False
                with col2:
                    if st.button("キャンセル", key="confirm_delete_no", use_container_width=True):
                        st.session_state.confirm_delete_session = False
                        st.rerun()
        
        # タブの設定
        tabs = st.tabs(["概要", "詳細データ", "関連プロジェクト", "編集履歴"])
        
        # 概要タブ
        with tabs[0]:
            # セッション基本情報
            with st.container():
                st.subheader("基本情報")
                
                # セッション情報カード
                with st.container():
                    st.markdown("##### セッション情報")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**説明:** {session.description}" if session.description else "**説明:** *なし*")
                        st.markdown(f"**作成日:** {format_datetime(session.created_at)}")
                        st.markdown(f"**更新日:** {format_datetime(session.updated_at)}")
                        st.markdown(f"**ステータス:** {session.status or 'なし'}")
                        st.markdown(f"**カテゴリ:** {session.category or 'なし'}")
                        
                        if session.source_file:
                            st.markdown(f"**ソースファイル:** {session.source_file}")
                        if session.source_type:
                            st.markdown(f"**ソースタイプ:** {session.source_type}")
                    
                    with col2:
                        # タグを視覚的に表示
                        if session.tags and len(session.tags) > 0:
                            st.markdown("**タグ:**")
                            tags_html = ""
                            for tag in session.tags:
                                tag_color = f"#{hash(tag) % 0xFFFFFF:06x}"
                                tags_html += f"<span style='background-color:{tag_color};color:white;padding:0.2rem 0.5rem;border-radius:0.5rem;font-size:0.8rem;margin-right:0.5rem;margin-bottom:0.5rem;display:inline-block'>{tag}</span>"
                            st.markdown(tags_html, unsafe_allow_html=True)
                        else:
                            st.markdown("**タグ:** なし")
                        
                        location = session.metadata.get("location", "")
                        if location:
                            st.markdown(f"**位置情報:** {location}")
                        
                        event_date = session.metadata.get("event_date", "")
                        if event_date:
                            st.markdown(f"**イベント日:** {format_datetime(event_date)}")
                        
                        boat_type = session.metadata.get("boat_type", "")
                        if boat_type:
                            st.markdown(f"**艇種:** {boat_type}")
                        
                        crew_info = session.metadata.get("crew_info", "")
                        if crew_info:
                            st.markdown(f"**クルー情報:** {crew_info}")
                
                # 区切り線
                st.markdown("---")
            
            # データサマリー
            with st.container():
                st.subheader("データサマリー")
                self.render_data_summary(session_id)
                
                # 区切り線
                st.markdown("---")
            
            # マッププレビュー
            with st.container():
                st.subheader("コースマッププレビュー")
                self.render_map_preview(session_id)
                
                # 区切り線
                st.markdown("---")
            
            # チャートプレビュー
            with st.container():
                st.subheader("パフォーマンスチャートプレビュー")
                self.render_chart_preview(session_id)
        
        # 詳細データタブ
        with tabs[1]:
            # データ品質指標
            if hasattr(session, 'data_quality') and session.data_quality:
                with st.expander("データ品質", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        quality_score = session.data_quality.get('completeness', 0.0)
                        st.markdown(f"##### 完全性")
                        st.progress(quality_score)
                        st.markdown(f"{quality_score:.2f}/1.0")
                    
                    with col2:
                        consistency_score = session.data_quality.get('consistency', 0.0)
                        st.markdown(f"##### 一貫性")
                        st.progress(consistency_score)
                        st.markdown(f"{consistency_score:.2f}/1.0")
                    
                    with col3:
                        accuracy_score = session.data_quality.get('accuracy', 0.0)
                        st.markdown(f"##### 精度")
                        st.progress(accuracy_score)
                        st.markdown(f"{accuracy_score:.2f}/1.0")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**エラー数:** {session.data_quality.get('error_count', 0)}")
                        st.markdown(f"**警告数:** {session.data_quality.get('warning_count', 0)}")
                    
                    with col2:
                        st.markdown(f"**修正された問題:** {session.data_quality.get('fixed_issues', 0)}")
                        
                        # 検証スコアの総合評価
                        validation_score = session.validation_score if hasattr(session, 'validation_score') else 0.0
                        st.markdown("**総合検証スコア:**")
                        st.progress(float(validation_score))
                        st.markdown(f"{validation_score:.2f}/1.0")
            
            # 生データの表示
            with st.expander("生データ表示", expanded=True):
                container = self.project_manager.load_container_from_session(session_id)
                
                if container is None or container.df.empty:
                    st.info("このセッションにはデータがありません。")
                else:
                    # データ基本情報の表示
                    st.markdown(f"##### データ基本情報")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("データポイント数", f"{len(container.df):,}")
                    with col2:
                        st.metric("列数", f"{len(container.df.columns):,}")
                    with col3:
                        memory_usage = container.df.memory_usage(deep=True).sum() / (1024 * 1024)
                        st.metric("メモリ使用量", f"{memory_usage:.2f} MB")
                    
                    # カラム情報の表示
                    st.markdown("##### データカラム")
                    columns_df = pd.DataFrame({
                        "カラム名": container.df.columns,
                        "データ型": container.df.dtypes.astype(str),
                        "非NULL値": container.df.count().values,
                        "一意値数": [container.df[col].nunique() for col in container.df.columns]
                    })
                    st.dataframe(columns_df, use_container_width=True)
                    
                    # データサンプルの表示
                    st.markdown("##### データサンプル")
                    st.dataframe(container.df.head(100), use_container_width=True)
                    
                    st.info(f"全{len(container.df):,}行中100行を表示しています。")
                    
                    # エクスポートオプション
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("CSVとしてダウンロード", key="download_data_csv", use_container_width=True):
                            csv = container.df.to_csv(index=False)
                            st.download_button(
                                label="ダウンロードを確認",
                                data=csv,
                                file_name=f"{session.name}_data.csv",
                                mime="text/csv",
                                key="confirm_download_data"
                            )
                    
                    with col2:
                        if st.button("Excelとしてダウンロード", key="download_data_excel", use_container_width=True):
                            # Excel出力の準備（仮実装）
                            st.info("Excel出力機能は今後のアップデートで追加される予定です。")
            
            # 分析結果
            with st.expander("分析結果", expanded=True):
                if not hasattr(session, 'analysis_results') or not session.analysis_results:
                    st.info("このセッションにはまだ分析結果がありません。")
                    
                    if st.button("分析を開始", key="start_analysis_btn"):
                        st.info("分析機能は今後のアップデートで追加される予定です。")
                else:
                    # 分析結果の表示（改善版）
                    st.markdown("##### 分析結果一覧")
                    
                    # 分析結果をテーブル形式で表示
                    results_data = []
                    for result_id in session.analysis_results:
                        # 実際は分析結果の詳細情報を取得する
                        results_data.append({
                            "ID": result_id,
                            "タイプ": "風向分析" if "wind" in result_id else "戦略分析",
                            "作成日時": "2025-03-28 10:30",  # 例示用
                            "ステータス": "完了"
                        })
                    
                    if results_data:
                        results_df = pd.DataFrame(results_data)
                        st.dataframe(results_df, use_container_width=True)
                        
                        # 選択して詳細表示
                        selected_result = st.selectbox(
                            "詳細を表示する分析結果を選択:",
                            options=[r["ID"] for r in results_data],
                            format_func=lambda x: f"{x} ({next((r['タイプ'] for r in results_data if r['ID'] == x), '')})"
                        )
                        
                        if st.button("詳細を表示", key="view_selected_result"):
                            st.markdown(f"##### 分析結果「{selected_result}」の詳細")
                            st.info("分析結果の詳細表示機能は今後のアップデートで追加される予定です。")
        
        # 関連プロジェクトタブ
        with tabs[2]:
            # 関連プロジェクト
            associated_projects = self.get_associated_projects(session_id)
            
            if not associated_projects:
                st.info("このセッションはどのプロジェクトにも関連付けられていません。")
                
                # プロジェクト割り当て機能（仮実装）
                if st.button("プロジェクトに割り当て", key="assign_to_project_btn"):
                    st.info("プロジェクト割り当て機能は今後のアップデートで追加される予定です。")
            else:
                # プロジェクト一覧の表示
                st.subheader("関連プロジェクト")
                st.markdown("このセッションは以下のプロジェクトに関連付けられています:")
                
                # プロジェクトカードを表示
                for i, project in enumerate(associated_projects):
                    with st.container():
                        # スタイリングされたカード
                        st.markdown(f"""
                        <div style="border:1px solid #ddd; border-radius:5px; padding:10px; margin-bottom:10px">
                            <h3 style="margin-top:0">{project['name']}</h3>
                            <p>{project['description'][:150]}{"..." if len(project['description']) > 150 else ""}</p>
                            <p style="color:#666; font-size:0.8rem">作成日: {project['created_at']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            if st.button("プロジェクト画面に移動", key=f"goto_project_{i}", use_container_width=True):
                                # プロジェクト画面への遷移処理
                                st.session_state.selected_project_id = project['id']
                                st.rerun()
                        
                        with col2:
                            if st.button("セッションの関連付けを解除", key=f"remove_from_project_{i}", use_container_width=True):
                                # プロジェクトからのセッション削除（仮実装）
                                if self.session_manager.remove_session_from_project(project['id'], session_id):
                                    st.success(f"プロジェクト「{project['name']}」からセッションを削除しました。")
                                    st.rerun()
                                else:
                                    st.error("削除に失敗しました。")
                        
                        with col3:
                            if st.button("詳細", key=f"project_details_{i}", use_container_width=True):
                                # プロジェクト詳細表示（仮実装）
                                st.session_state.view_project_details = project['id']
                
                # 新規プロジェクト割り当て
                with st.expander("新しいプロジェクトに割り当て", expanded=False):
                    # プロジェクト一覧を取得（現在割り当てられていないもの）
                    all_projects = self.project_manager.get_projects()
                    available_projects = [
                        p for p in all_projects 
                        if p.project_id not in [proj['id'] for proj in associated_projects]
                    ]
                    
                    if not available_projects:
                        st.info("割り当て可能な他のプロジェクトはありません。")
                    else:
                        project_options = {p.project_id: p.name for p in available_projects}
                        selected_project = st.selectbox(
                            "プロジェクトを選択:",
                            options=list(project_options.keys()),
                            format_func=lambda x: project_options[x]
                        )
                        
                        if st.button("セッションを割り当て", key="assign_session_btn"):
                            if self.session_manager.add_session_to_project(selected_project, session_id):
                                st.success("プロジェクトにセッションを割り当てました。")
                                st.rerun()
                            else:
                                st.error("割り当てに失敗しました。")
        
        # 編集履歴タブ
        with tabs[3]:
            # 編集履歴の実装
            st.subheader("編集履歴")
            
            # 履歴データの取得
            history = self.get_session_history(session_id)
            
            if not history:
                st.info("このセッションにはまだ編集履歴がありません。")
            else:
                for entry in history:
                    with st.container():
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.markdown(f"**{entry['timestamp']}**")
                            st.markdown(f"ユーザー: {entry['user']}")
                        
                        with col2:
                            st.markdown(f"**{entry['action']}**")
                            if entry.get('changes'):
                                for field, value in entry['changes'].items():
                                    st.markdown(f"{field}: {value['old']} → {value['new']}")
                        
                        st.markdown("---")


def session_editor_view(
    project_manager: ProjectManager,
    session_manager: SessionManager,
    session_id: str,
    on_save: Optional[Callable[[str], None]] = None,
    on_cancel: Optional[Callable[[], None]] = None
) -> bool:
    """
    セッションメタデータの編集フォーム
    
    Parameters
    ----------
    project_manager : ProjectManager
        プロジェクト管理クラスのインスタンス
    session_manager : SessionManager
        セッション管理クラスのインスタンス
    session_id : str
        編集するセッションのID
    on_save : Optional[Callable[[str], None]], optional
        保存時のコールバック関数, by default None
    on_cancel : Optional[Callable[[], None]], optional
        キャンセル時のコールバック関数, by default None
        
    Returns
    -------
    bool
        更新に成功した場合True
    """
    from ui.components.project.session_editor import SessionEditorView
    
    # SessionEditorViewのインスタンスを生成して使用
    editor = SessionEditorView(
        project_manager=project_manager,
        session_manager=session_manager,
        on_save=on_save,
        on_cancel=on_cancel
    )
    
    return editor.render(session_id)
