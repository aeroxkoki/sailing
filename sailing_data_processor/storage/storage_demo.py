"""
ストレージソリューションのデモアプリケーション

このモジュールは実装したストレージソリューションの機能を確認するための
デモアプリケーションを提供します。
"""

import json
import base64
import time
import datetime
import random
from typing import Dict, Any, List

import streamlit as st
import pandas as pd
import numpy as np

from .storage_interface import StorageInterface, StorageError
from .browser_storage import BrowserStorage
from .export_import import ExportImportManager, convert_df_to_csv_download
from .storage_components import StorageManagerComponent, ImportExportComponent


class StorageDemoApp:
    """
    ストレージソリューションのデモアプリケーション
    """
    
    def __init__(self):
        """初期化"""
        # ブラウザストレージの初期化
        if "browser_storage" not in st.session_state:
            try:
                # 初回アクセス時にストレージを初期化
                st.session_state.browser_storage = BrowserStorage(namespace="demo")
            except Exception as e:
                st.error(f"ストレージの初期化に失敗しました: {str(e)}")
                st.session_state.browser_storage = None
        
        self.storage = st.session_state.browser_storage
        
        # エクスポート/インポートマネージャーの初期化
        self.export_manager = ExportImportManager()
        
        # UIコンポーネントの初期化
        self.storage_manager = StorageManagerComponent(self.storage) if self.storage else None
        self.import_export = ImportExportComponent(self.export_manager)
        
        # アクティブなセッションデータ
        if "active_session" not in st.session_state:
            st.session_state.active_session = None
    
    def _generate_sample_data(self, num_points: int = 100) -> pd.DataFrame:
        """
        サンプルのセーリングデータを生成
        
        Args:
            num_points: データポイント数
            
        Returns:
            pd.DataFrame: 生成されたサンプルデータ
        """
        # 時間軸
        times = pd.date_range(start=datetime.datetime.now(), periods=num_points, freq='10S')
        
        # GPSデータ生成（円形の航跡をシミュレート）
        center_lat, center_lon = 35.65, 139.8  # 東京湾付近
        radius = 0.02  # 約2km
        
        # 円周に沿った動き
        angles = np.linspace(0, 2 * np.pi, num_points)
        latitudes = center_lat + radius * np.cos(angles)
        longitudes = center_lon + radius * np.sin(angles)
        
        # 速度と風向風速を生成
        speeds = 5 + np.sin(angles) * 2  # 3-7ノットの間で変動
        wind_directions = (angles * 180 / np.pi + 180) % 360  # 0-360度
        wind_speeds = 10 + np.sin(angles * 2) * 3  # 7-13ノットの間で変動
        
        # データフレーム作成
        data = pd.DataFrame({
            'timestamp': times,
            'latitude': latitudes,
            'longitude': longitudes,
            'speed': speeds,
            'wind_direction': wind_directions,
            'wind_speed': wind_speeds,
        })
        
        return data
    
    def _create_sample_session(self, name: str = "サンプルセッション") -> Dict[str, Any]:
        """
        サンプルセッションデータを作成
        
        Args:
            name: セッション名
            
        Returns:
            Dict[str, Any]: セッションデータ
        """
        data = self._generate_sample_data()
        
        session = {
            "id": f"session_{int(time.time())}",
            "name": name,
            "created_at": datetime.datetime.now().isoformat(),
            "modified_at": datetime.datetime.now().isoformat(),
            "data": data.to_dict(orient="records"),
            "metadata": {
                "boat_type": "470",
                "location": "東京湾",
                "weather": "晴れ",
                "notes": "サンプルデータです"
            }
        }
        
        return session
    
    def _create_multiple_sample_sessions(self, count: int = 5) -> Dict[str, Dict[str, Any]]:
        """
        複数のサンプルセッションを作成
        
        Args:
            count: 作成するセッション数
            
        Returns:
            Dict[str, Dict[str, Any]]: セッションのディクショナリ
        """
        locations = ["東京湾", "大阪湾", "琵琶湖", "瀬戸内海", "浜名湖"]
        boat_types = ["470", "レーザー", "49er", "国体ウインドサーフィン", "シーホッパー"]
        weathers = ["晴れ", "曇り", "小雨", "強風", "微風"]
        
        sessions = {}
        for i in range(count):
            name = f"セッション {i+1}"
            session = self._create_sample_session(name)
            
            # バリエーションを付ける
            session["metadata"]["location"] = random.choice(locations)
            session["metadata"]["boat_type"] = random.choice(boat_types)
            session["metadata"]["weather"] = random.choice(weathers)
            
            # データポイント数を変える
            points = random.randint(50, 200)
            session["data"] = self._generate_sample_data(points).to_dict(orient="records")
            
            sessions[session["id"]] = session
        
        return sessions
    
    def render_basic_storage_demo(self):
        """基本的なストレージ操作のデモを表示"""
        st.header("基本的なストレージ操作")
        
        if not self.storage:
            st.error("ブラウザストレージが利用できません。ブラウザの設定を確認してください。")
            return
        
        # データ保存セクション
        st.subheader("データの保存")
        
        # シンプルなキーバリューの保存
        with st.form("save_simple_data"):
            key = st.text_input("キー", "test_key")
            value = st.text_area("値", "{\"name\": \"テストデータ\", \"value\": 123}")
            
            submit = st.form_submit_button("保存")
            if submit:
                try:
                    # JSON文字列をオブジェクトに変換
                    data = json.loads(value)
                    
                    # 保存
                    if self.storage.save(key, data):
                        st.success(f"データを保存しました（キー: {key}）")
                    else:
                        st.error("データの保存に失敗しました")
                except json.JSONDecodeError:
                    st.error("無効なJSON形式です")
                except Exception as e:
                    st.error(f"エラー: {str(e)}")
        
        # 大きなデータの保存（自動チャンク分割テスト）
        st.subheader("大きなデータの保存（チャンク分割テスト）")
        
        with st.form("save_large_data"):
            chunk_key = st.text_input("キー", "large_data")
            data_size = st.slider("データサイズ（項目数）", 100, 5000, 1000)
            
            submit = st.form_submit_button("大きなデータを生成して保存")
            if submit:
                try:
                    # 大きなデータを生成
                    large_data = {
                        "name": "大きなテストデータ",
                        "created_at": datetime.datetime.now().isoformat(),
                        "items": [{"id": i, "value": f"テストデータ {i}" * 10} for i in range(data_size)]
                    }
                    
                    # JSONサイズを表示
                    json_data = json.dumps(large_data)
                    size_kb = len(json_data) / 1024
                    st.info(f"生成されたデータサイズ: {size_kb:.2f} KB")
                    
                    # 保存（進捗表示）
                    with st.spinner("データを保存中..."):
                        if self.storage.save(chunk_key, large_data):
                            st.success(f"大きなデータを保存しました（キー: {chunk_key}）")
                        else:
                            st.error("データの保存に失敗しました")
                    
                except Exception as e:
                    st.error(f"エラー: {str(e)}")
        
        # データ読み込みセクション
        st.subheader("データの読み込み")
        
        with st.form("load_data"):
            load_key = st.text_input("読み込むキー", "test_key")
            submit = st.form_submit_button("読み込み")
            
            if submit:
                try:
                    data = self.storage.load(load_key)
                    if data is not None:
                        st.json(data)
                    else:
                        st.warning(f"キー '{load_key}' に対応するデータが見つかりませんでした")
                except Exception as e:
                    st.error(f"読み込みエラー: {str(e)}")
    
    def render_session_management_demo(self):
        """セッション管理のデモを表示"""
        st.header("セッション管理デモ")
        
        if not self.storage:
            st.error("ブラウザストレージが利用できません。ブラウザの設定を確認してください。")
            return
        
        # 現在のセッション表示
        if st.session_state.active_session:
            st.subheader("現在のセッション")
            
            session = st.session_state.active_session
            st.write(f"名前: {session['name']}")
            st.write(f"作成日時: {session['created_at']}")
            
            metadata = session.get("metadata", {})
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("艇種:", metadata.get("boat_type", "未設定"))
            with col2:
                st.write("場所:", metadata.get("location", "未設定"))
            with col3:
                st.write("天候:", metadata.get("weather", "未設定"))
            
            data = pd.DataFrame(session.get("data", []))
            if not data.empty:
                st.write(f"データポイント数: {len(data)}")
                st.dataframe(data.head(10))
                
                # データのプレビュー
                if st.button("データをプレビュー", key="preview_session_data"):
                    # シンプルなグラフ表示
                    st.line_chart(data[['speed', 'wind_speed']])
                    
                    # マップ表示（簡易版）
                    st.subheader("航跡")
                    st.map(data[['latitude', 'longitude']])
                
                # CSVダウンロード
                csv_data, csv_filename = convert_df_to_csv_download(data, f"{session['name']}.csv")
                st.download_button(
                    label="CSVとしてダウンロード",
                    data=csv_data,
                    file_name=csv_filename,
                    mime="text/csv",
                    key="download_csv"
                )
                
            # セッション保存ボタン
            if st.button("セッションを保存", key="save_current_session"):
                try:
                    session_id = session.get("id")
                    if self.storage.save(f"session_{session_id}", session):
                        st.success(f"セッション '{session['name']}' を保存しました")
                    else:
                        st.error("セッションの保存に失敗しました")
                except Exception as e:
                    st.error(f"保存エラー: {str(e)}")
            
            # エクスポートボタン
            st.subheader("セッションのエクスポート")
            self.import_export.render_export_button(
                {"type": "session", "session": session},
                name=f"session_{session['id']}",
                label="このセッションをエクスポート"
            )
        
        # 新しいサンプルセッションの作成
        st.subheader("サンプルセッションの作成")
        
        with st.form("create_sample_session"):
            session_name = st.text_input("セッション名", "テストセッション")
            data_points = st.slider("データポイント数", 50, 500, 100)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                boat_type = st.selectbox("艇種", ["470", "レーザー", "49er", "国体ウインドサーフィン", "シーホッパー"])
            with col2:
                location = st.selectbox("場所", ["東京湾", "大阪湾", "琵琶湖", "瀬戸内海", "浜名湖"])
            with col3:
                weather = st.selectbox("天候", ["晴れ", "曇り", "小雨", "強風", "微風"])
            
            if st.form_submit_button("サンプルセッションを作成"):
                # サンプルセッション作成
                session = self._create_sample_session(session_name)
                
                # メタデータとデータを設定
                session["metadata"]["boat_type"] = boat_type
                session["metadata"]["location"] = location
                session["metadata"]["weather"] = weather
                session["data"] = self._generate_sample_data(data_points).to_dict(orient="records")
                
                # セッションをアクティブにする
                st.session_state.active_session = session
                st.success(f"サンプルセッション '{session_name}' を作成しました")
                st.experimental_rerun()
    
    def render_import_export_demo(self):
        """インポート/エクスポートのデモを表示"""
        st.header("インポート/エクスポートデモ")
        
        if not self.storage:
            st.error("ブラウザストレージが利用できません。ブラウザの設定を確認してください。")
            return
        
        # バッチエクスポートデモ
        st.subheader("バッチエクスポートデモ")
        
        if st.button("サンプルセッションを複数生成", key="create_multiple_sessions"):
            sample_sessions = self._create_multiple_sample_sessions(5)
            st.session_state.sample_sessions = sample_sessions
            st.success(f"{len(sample_sessions)}個のサンプルセッションを生成しました")
        
        # 生成されたサンプルセッションをエクスポート
        if hasattr(st.session_state, 'sample_sessions') and st.session_state.sample_sessions:
            sessions = st.session_state.sample_sessions
            self.import_export.render_export_multiple_items(
                sessions,
                "sessions",
                "サンプルセッションをエクスポート"
            )
        
        # インポートデモ
        st.subheader("ファイルからインポート")
        
        def handle_import(import_data):
            content_type = import_data.get("type")
            
            if content_type == "session":
                # セッションインポート
                session_data = import_data.get("session", {})
                st.session_state.active_session = session_data
                st.success(f"セッション '{session_data.get('name', 'unknown')}' をインポートしました")
            
            elif content_type == "sessions":
                # 複数セッションインポート
                sessions = import_data.get("items", {})
                st.session_state.sample_sessions = sessions
                st.success(f"{len(sessions)}個のセッションをインポートしました")
            
            else:
                st.warning(f"未サポートのコンテンツタイプです: {content_type}")
        
        self.import_export.render_import_uploader(
            on_import=handle_import,
            label="セーリングデータファイルをインポート",
            help_text="エクスポートしたセッションデータをアップロードします"
        )
    
    def render_storage_management_demo(self):
        """ストレージ管理のデモを表示"""
        st.header("ストレージ管理")
        
        if not self.storage:
            st.error("ブラウザストレージが利用できません。ブラウザの設定を確認してください。")
            return
        
        def on_session_select(key):
            try:
                session_data = self.storage.load(key)
                if session_data:
                    st.session_state.active_session = session_data
                    st.success(f"セッション '{session_data.get('name', key)}' を読み込みました")
                    st.experimental_rerun()
            except Exception as e:
                st.error(f"セッションの読み込みエラー: {str(e)}")
        
        # ストレージ管理UIの表示
        self.storage_manager.render_storage_manager(
            prefix="session_",
            on_select=on_session_select
        )
    
    def run(self):
        """アプリケーションを実行"""
        st.title("セーリング戦略分析システム - ストレージデモ")
        
        if not self.storage:
            st.error("ブラウザストレージが利用できません。このデモには最新のブラウザが必要です。")
            return
        
        # サイドバーのナビゲーション
        st.sidebar.title("デモナビゲーション")
        demo_page = st.sidebar.radio(
            "表示するデモを選択:",
            ["セッション管理", "ストレージ管理", "インポート/エクスポート", "基本的なストレージ操作"]
        )
        
        # ストレージ情報を常に表示
        with st.sidebar:
            storage_info = self.storage.get_storage_info()
            used_mb = storage_info.get("namespace_used", 0) / (1024 * 1024)
            total_mb = storage_info.get("estimated_max", 0) / (1024 * 1024)
            usage_percent = min(100, (used_mb / total_mb * 100) if total_mb > 0 else 0)
            
            st.progress(usage_percent / 100)
            st.write(f"ストレージ使用量: {used_mb:.2f} MB / {total_mb:.2f} MB ({usage_percent:.1f}%)")
        
        # 選択されたデモページを表示
        if demo_page == "セッション管理":
            self.render_session_management_demo()
        elif demo_page == "ストレージ管理":
            self.render_storage_management_demo()
        elif demo_page == "インポート/エクスポート":
            self.render_import_export_demo()
        elif demo_page == "基本的なストレージ操作":
            self.render_basic_storage_demo()


def main():
    """デモアプリケーションのメインエントリーポイント"""
    demo_app = StorageDemoApp()
    demo_app.run()


if __name__ == "__main__":
    main()
