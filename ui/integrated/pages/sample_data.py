# -*- coding: utf-8 -*-
"""
ui.integrated.pages.sample_data

サンプルデータページ - テスト/学習用のサンプルデータをインポートする機能
"""

import streamlit as st
import pandas as pd
import os
import io
import tempfile
from typing import Dict, List, Any, Optional, Tuple
import json
from pathlib import Path

# セッション状態キー
SESSION_STATE_KEY = "sample_data_state"

# サンプルデータの定義
SAMPLE_DATASETS = [
    {
        "id": "sample_1",
        "name": "標準シミュレーション - 短距離コース",
        "description": "短距離コースでの標準的なセーリングデータのシミュレーション。アップウィンド・ダウンウィンドのレグが含まれる。",
        "file_path": "/simulation_data/standard_simulation_20250327_151233.csv",
        "metadata_path": "/simulation_data/standard_metadata_20250327_151233.json",
        "thumbnail": "📊",
        "tags": ["シミュレーション", "短距離", "スタンダード"]
    },
    {
        "id": "sample_2",
        "name": "標準シミュレーション - 長距離コース",
        "description": "長距離コースでの標準的なセーリングデータのシミュレーション。複数のレグと戦略的な判断ポイントが含まれる。",
        "file_path": "/simulation_data/standard_simulation_20250327_152131.csv",
        "metadata_path": "/simulation_data/standard_metadata_20250327_152131.json",
        "thumbnail": "📈",
        "tags": ["シミュレーション", "長距離", "複雑", "戦略"]
    }
]

def initialize_session_state():
    """セッション状態を初期化"""
    if SESSION_STATE_KEY not in st.session_state:
        st.session_state[SESSION_STATE_KEY] = {
            "selected_sample": None,
            "import_completed": False,
            "imported_container": None
        }

def render_page():
    """サンプルデータページをレンダリング"""
    st.title("サンプルデータ")
    
    # セッション状態を初期化
    initialize_session_state()
    
    # コンテナを取得
    state = st.session_state[SESSION_STATE_KEY]
    
    st.write("""
    テスト・学習用のサンプルデータを選択してインポートします。
    サンプルデータを使用すると、システムの機能をすぐに試すことができます。
    """)
    
    # 戻るボタン
    if st.button("データインポートページに戻る", key="back_to_import"):
        st.session_state.current_page = "data_import"
        st.rerun()
    
    # サンプルデータの一覧表示
    st.header("利用可能なサンプルデータ")
    
    # サンプルデータセット選択
    render_sample_selection()
    
    # 選択されたサンプルデータの詳細表示
    if state.get("selected_sample"):
        render_sample_details()
        
        # インポート済みの場合、セッション作成フォームを表示
        if state.get("import_completed") and state.get("imported_container"):
            render_session_creation_form()

def render_sample_selection():
    """サンプルデータセットの選択UI"""
    state = st.session_state[SESSION_STATE_KEY]
    
    # 2列のグリッドでサンプルを表示
    col1, col2 = st.columns(2)
    
    for i, sample in enumerate(SAMPLE_DATASETS):
        col = col1 if i % 2 == 0 else col2
        
        with col:
            container = st.container(border=True)
            with container:
                st.markdown(f"### {sample['thumbnail']} {sample['name']}")
                st.markdown(sample["description"])
                st.markdown(f"**タグ**: {', '.join(sample['tags'])}")
                
                # 選択ボタン
                is_selected = state.get("selected_sample") == sample["id"]
                if st.button(
                    "選択中" if is_selected else "選択する", 
                    key=f"select_{sample['id']}",
                    type="primary" if is_selected else "secondary",
                    use_container_width=True
                ):
                    # 選択状態を更新
                    state["selected_sample"] = sample["id"]
                    state["import_completed"] = False
                    state["imported_container"] = None
                    st.rerun()

def render_sample_details():
    """選択されたサンプルデータの詳細表示"""
    state = st.session_state[SESSION_STATE_KEY]
    
    # 選択されたサンプルを取得
    selected_id = state.get("selected_sample")
    selected_sample = next((s for s in SAMPLE_DATASETS if s["id"] == selected_id), None)
    
    if not selected_sample:
        st.error("選択されたサンプルデータが見つかりません。")
        return
    
    # サンプルデータの詳細表示
    st.header(f"{selected_sample['name']} の詳細")
    
    # メタデータの読み込み
    metadata = load_sample_metadata(selected_sample["metadata_path"])
    
    if metadata:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("メタデータ")
            for key, value in metadata.items():
                if isinstance(value, list):
                    st.write(f"**{key}**: {', '.join(value)}")
                else:
                    st.write(f"**{key}**: {value}")
        
        with col2:
            st.subheader("サンプルデータ情報")
            # CSVファイルのプレビュー
            df = load_sample_csv(selected_sample["file_path"])
            if df is not None:
                st.write(f"**データポイント数**: {len(df)}")
                
                # タイムスタンプの範囲を表示
                if "timestamp" in df.columns:
                    try:
                        df["timestamp"] = pd.to_datetime(df["timestamp"])
                        min_time = df["timestamp"].min()
                        max_time = df["timestamp"].max()
                        duration = (max_time - min_time).total_seconds() / 60  # 分に変換
                        st.write(f"**時間範囲**: {min_time} ～ {max_time}")
                        st.write(f"**期間**: {duration:.1f}分")
                    except:
                        pass
                
                # プレビュー表示
                st.write("**データプレビュー**:")
                st.dataframe(df.head(5), use_container_width=True)
    
    # インポートボタン
    if st.button("このデータセットをインポート", type="primary", key="import_sample_btn"):
        # インポートを実行
        container = import_sample_data(selected_sample)
        if container:
            # インポート成功
            state["import_completed"] = True
            state["imported_container"] = container
            
            # インポートコントローラーにコンテナを設定
            from ui.integrated.controllers.import_controller import ImportController
            controller = ImportController()
            controller.set_imported_container(container)
            
            st.success("サンプルデータのインポートが完了しました！")
            
            # データのプレビューを表示
            with st.expander("インポート結果のプレビュー", expanded=True):
                # データフレームの基本情報を表示
                df = container.data if container else None
                if df is not None:
                    st.write(f"**データポイント数**: {len(df)}")
                    
                    # マップでの表示
                    if "latitude" in df.columns and "longitude" in df.columns:
                        st.subheader("トラック表示")
                        map_data = df[["latitude", "longitude"]].copy()
                        st.map(map_data)

def render_session_creation_form():
    """セッション作成フォームの表示"""
    st.header("セッション作成")
    
    state = st.session_state[SESSION_STATE_KEY]
    container = state.get("imported_container")
    
    if not container:
        return
    
    # インポートコントローラーを取得
    from ui.integrated.controllers.import_controller import ImportController
    controller = ImportController()
    
    # プロジェクト選択
    projects = get_available_projects()
    
    if projects:
        project_options = {p["id"]: p["name"] for p in projects}
        project_id = st.selectbox(
            "プロジェクト",
            options=list(project_options.keys()),
            format_func=lambda x: project_options.get(x, "不明なプロジェクト"),
            key="sample_project_id"
        )
        
        # セッション情報入力
        # 選択されたサンプルの名前をデフォルトにする
        selected_id = state.get("selected_sample")
        selected_sample = next((s for s in SAMPLE_DATASETS if s["id"] == selected_id), None)
        default_name = selected_sample["name"] if selected_sample else "サンプルセッション"
        
        session_name = st.text_input("セッション名", value=default_name, key="sample_session_name")
        session_desc = st.text_area("説明", key="sample_session_description")
        
        # サンプルデータのタグをデフォルトに設定
        default_tags = ", ".join(selected_sample["tags"]) if selected_sample else "サンプル"
        session_tags = st.text_input("タグ（カンマ区切り）", value=default_tags, key="sample_session_tags")
        
        tags_list = [tag.strip() for tag in session_tags.split(",")] if session_tags else []
        
        # セッション作成ボタン
        if st.button("セッションを作成", key="sample_create_session_btn"):
            if not session_name:
                st.error("セッション名を入力してください。")
            else:
                success = controller.create_session_from_container(
                    project_id=project_id,
                    name=session_name,
                    description=session_desc,
                    tags=tags_list
                )
                
                if success:
                    st.success("セッションが作成されました。")
                    
                    # ナビゲーションオプション
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("プロジェクト詳細を表示", key="goto_project_detail", use_container_width=True):
                            st.session_state.current_page = "project_detail"
                            st.session_state.selected_project_id = project_id
                            st.rerun()
                    with col2:
                        if st.button("データ検証を実行", key="goto_data_validation", use_container_width=True):
                            st.session_state.current_page = "data_validation"
                            st.rerun()
                else:
                    st.error("セッション作成に失敗しました。")
                    for error in controller.get_errors():
                        st.error(error)
    else:
        st.warning("利用可能なプロジェクトがありません。先にプロジェクトを作成してください。")
        if st.button("新規プロジェクト作成", key="sample_create_project_btn"):
            st.session_state.current_page = "project_create"
            st.rerun()

def import_sample_data(sample: Dict[str, Any]):
    """
    サンプルデータをインポート
    
    Parameters
    ----------
    sample : Dict[str, Any]
        サンプルデータの情報
        
    Returns
    -------
    GPSDataContainer or None
        インポートされたデータコンテナ
    """
    # CSVファイルとメタデータを読み込む
    df = load_sample_csv(sample["file_path"])
    metadata = load_sample_metadata(sample["metadata_path"])
    
    if df is None:
        st.error(f"サンプルCSVファイルの読み込みに失敗しました: {sample['file_path']}")
        return None
    
    if metadata is None:
        # メタデータがない場合はデフォルト値を使用
        metadata = {
            "name": sample["name"],
            "description": sample["description"],
            "tags": sample["tags"]
        }
    
    try:
        # 一時ファイルにCSVを書き込み
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            df.to_csv(tmp.name, index=False)
            tmp_path = tmp.name
        
        try:
            # インポーターを取得
            from sailing_data_processor.importers.csv_importer import CSVImporter
            
            # カラムマッピングを設定
            column_mapping = {
                "timestamp": "timestamp",
                "latitude": "latitude",
                "longitude": "longitude"
            }
            
            # オプションフィールドがあれば追加
            optional_fields = ["speed", "course", "elevation", "heart_rate", "power", "distance", "temperature", "wind_speed", "wind_direction"]
            for field in optional_fields:
                if field in df.columns:
                    column_mapping[field] = field
            
            # インポート設定
            import_settings = {
                "delimiter": ",",
                "encoding": "utf-8",
                "skiprows": 0,
                "column_mapping": column_mapping
            }
            
            # インポーターの初期化とインポート実行
            importer = CSVImporter(import_settings)
            container = importer.import_data(tmp_path, metadata)
            
            return container
        
        finally:
            # 一時ファイルを削除
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    except Exception as e:
        st.error(f"サンプルデータのインポート中にエラーが発生しました: {str(e)}")
        return None

def load_sample_csv(file_path: str) -> Optional[pd.DataFrame]:
    """
    サンプルCSVファイルを読み込む
    
    Parameters
    ----------
    file_path : str
        CSVファイルのパス
        
    Returns
    -------
    Optional[pd.DataFrame]
        読み込まれたデータフレーム
    """
    try:
        # 相対パスをプロジェクトルートからの絶対パスに変換
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        abs_path = os.path.join(project_root, file_path.lstrip("/"))
        
        # ファイルが存在するか確認
        if not os.path.exists(abs_path):
            st.error(f"ファイルが見つかりません: {abs_path}")
            return None
        
        # CSVの読み込み
        df = pd.read_csv(abs_path)
        return df
    
    except Exception as e:
        st.error(f"CSVファイルの読み込みエラー: {str(e)}")
        return None

def load_sample_metadata(file_path: str) -> Optional[Dict[str, Any]]:
    """
    サンプルメタデータファイルを読み込む
    
    Parameters
    ----------
    file_path : str
        メタデータファイルのパス
        
    Returns
    -------
    Optional[Dict[str, Any]]
        読み込まれたメタデータ
    """
    try:
        # 相対パスをプロジェクトルートからの絶対パスに変換
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        abs_path = os.path.join(project_root, file_path.lstrip("/"))
        
        # ファイルが存在するか確認
        if not os.path.exists(abs_path):
            st.warning(f"メタデータファイルが見つかりません: {abs_path}")
            return None
        
        # JSONの読み込み
        with open(abs_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        return metadata
    
    except Exception as e:
        st.warning(f"メタデータファイルの読み込みエラー: {str(e)}")
        return None

def get_available_projects() -> List[Dict[str, Any]]:
    """
    利用可能なプロジェクトのリストを取得
    
    Returns
    -------
    List[Dict[str, Any]]
        プロジェクトの辞書のリスト
    """
    from ui.components.project.project_manager import initialize_project_manager
    
    project_manager = initialize_project_manager()
    if not project_manager:
        return []
    
    # ルートプロジェクトを取得
    root_projects = project_manager.get_root_projects()
    
    # プロジェクト情報を整形
    projects = []
    for project in root_projects:
        projects.append({
            "id": project.project_id,
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at,
            "updated_at": project.updated_at
        })
        
        # サブプロジェクトも取得
        sub_projects = project_manager.get_sub_projects(project.project_id)
        for sub in sub_projects:
            projects.append({
                "id": sub.project_id,
                "name": f"{project.name} > {sub.name}",
                "description": sub.description,
                "created_at": sub.created_at,
                "updated_at": sub.updated_at
            })
    
    return projects

if __name__ == "__main__":
    render_page()
