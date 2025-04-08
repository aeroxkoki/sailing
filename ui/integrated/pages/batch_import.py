"""
ui.integrated.pages.batch_import

バッチインポートページ - 複数ファイルを一括インポートする機能
"""

import streamlit as st
import pandas as pd
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import time

# セッション状態キー
SESSION_STATE_KEY = "batch_import_state"

def initialize_session_state():
    """セッション状態を初期化"""
    if SESSION_STATE_KEY not in st.session_state:
        st.session_state[SESSION_STATE_KEY] = {
            "uploaded_files": [],
            "selected_format": None,
            "import_settings": {},
            "metadata": {},
            "import_results": [],
            "current_file_index": 0,
            "import_completed": False,
            "import_started": False,
            "import_progress": 0.0,
            "success_count": 0,
            "failed_count": 0
        }

def render_page():
    """バッチインポートページをレンダリング"""
    st.title("バッチインポート")
    
    # セッション状態を初期化
    initialize_session_state()
    
    # コンテナを取得
    state = st.session_state[SESSION_STATE_KEY]
    
    st.write("""
    複数のGPSデータファイルを一括インポートします。
    同一形式のファイルを効率的に処理できます。
    """)
    
    # 戻るボタン
    if st.button("データインポートページに戻る", key="back_to_import"):
        st.session_state.current_page = "data_import"
        st.rerun()
    
    # ファイルアップロード
    with st.expander("1. ファイルアップロード", expanded=not state.get("uploaded_files")):
        render_file_upload_section()
    
    # ファイル形式選択
    if state.get("uploaded_files"):
        with st.expander("2. ファイル形式と設定", expanded=not state.get("selected_format")):
            render_format_selection()
    
    # メタデータ設定
    if state.get("selected_format"):
        with st.expander("3. 共通メタデータ", expanded=not state.get("metadata")):
            render_metadata_section()
    
    # インポート実行
    if state.get("metadata"):
        with st.expander("4. インポート実行", expanded=True):
            render_import_execution()
    
    # インポート結果
    if state.get("import_completed"):
        with st.expander("5. インポート結果", expanded=True):
            render_import_results()
            
            # インポート完了後のナビゲーション
            st.subheader("次のステップ")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("データ検証へ進む", key="goto_validation", use_container_width=True):
                    st.session_state.current_page = "data_validation"
                    st.rerun()
            
            with col2:
                if st.button("プロジェクト一覧へ", key="goto_projects", use_container_width=True):
                    st.session_state.current_page = "projects"
                    st.rerun()
            
            with col3:
                if st.button("新しいインポートを開始", key="restart_import", use_container_width=True):
                    # 状態をリセット
                    st.session_state[SESSION_STATE_KEY] = {
                        "uploaded_files": [],
                        "selected_format": None,
                        "import_settings": {},
                        "metadata": {},
                        "import_results": [],
                        "current_file_index": 0,
                        "import_completed": False,
                        "import_started": False,
                        "import_progress": 0.0,
                        "success_count": 0,
                        "failed_count": 0
                    }
                    st.rerun()

def render_file_upload_section():
    """ファイルアップロードセクションをレンダリング"""
    state = st.session_state[SESSION_STATE_KEY]
    
    st.write("インポートするファイルを選択してください。対応形式: CSV, GPX, TCX, FIT")
    
    # 複数ファイルアップロード
    uploaded_files = st.file_uploader(
        "GPS/セーリングデータファイル（複数選択可）",
        type=["csv", "gpx", "tcx", "fit"],
        accept_multiple_files=True,
        key="batch_file_uploader"
    )
    
    if uploaded_files:
        # アップロードされたファイル情報をセッションに保存
        file_info = []
        for file in uploaded_files:
            file_info.append({
                "name": file.name,
                "size": file.size,
                "type": file.type or "不明",
                "file_obj": file
            })
        
        # セッション状態を更新
        state["uploaded_files"] = file_info
        
        # ファイル一覧を表示
        st.write(f"**アップロードされたファイル:** {len(file_info)}個")
        
        # データフレームでファイル情報を表示
        file_df = pd.DataFrame([
            {
                "ファイル名": info["name"],
                "サイズ": format_file_size(info["size"]),
                "タイプ": info["type"]
            }
            for info in file_info
        ])
        
        st.dataframe(file_df, use_container_width=True, hide_index=True)
    else:
        state["uploaded_files"] = []

def render_format_selection():
    """ファイル形式選択セクションをレンダリング"""
    state = st.session_state[SESSION_STATE_KEY]
    
    # アップロードされたファイルの拡張子を分析
    file_extensions = [Path(file["name"]).suffix.lower().lstrip(".") for file in state["uploaded_files"]]
    extension_counts = {}
    for ext in file_extensions:
        extension_counts[ext] = extension_counts.get(ext, 0) + 1
    
    # 最も多い拡張子を推定
    most_common_ext = max(extension_counts.items(), key=lambda x: x[1])[0] if extension_counts else None
    
    # 拡張子からファイル形式を推定
    format_map = {
        "csv": "CSV",
        "gpx": "GPX",
        "tcx": "TCX",
        "fit": "FIT"
    }
    
    recommended_format = format_map.get(most_common_ext, None)
    
    # 推定された形式を表示
    if recommended_format:
        st.info(f"推奨ファイル形式: {recommended_format} (最も多い拡張子: .{most_common_ext})")
    
    # ファイル形式選択
    format_options = ["CSV", "GPX", "TCX", "FIT"]
    selected_format = st.selectbox(
        "インポート形式を選択",
        options=format_options,
        index=format_options.index(recommended_format) if recommended_format in format_options else 0,
        key="batch_format_selector"
    )
    
    # 選択された形式に応じた設定オプションを表示
    st.subheader("インポート設定")
    
    import_settings = {}
    
    if selected_format == "CSV":
        col1, col2 = st.columns(2)
        with col1:
            delimiter = st.text_input("区切り文字", value=",", key="batch_csv_delimiter")
            import_settings["delimiter"] = delimiter
            
            encoding = st.selectbox(
                "エンコーディング",
                options=["utf-8", "shift-jis", "euc-jp", "iso-2022-jp"],
                key="batch_csv_encoding"
            )
            import_settings["encoding"] = encoding
        
        with col2:
            skip_rows = st.number_input(
                "スキップする行数",
                min_value=0,
                value=0,
                step=1,
                key="batch_csv_skiprows"
            )
            import_settings["skiprows"] = int(skip_rows)
            
            date_format = st.text_input(
                "日付フォーマット (オプション)",
                value="",
                help="例: %Y-%m-%d %H:%M:%S",
                key="batch_csv_dateformat"
            )
            if date_format:
                import_settings["date_format"] = date_format
        
        # CSVカラムマッピング
        st.subheader("カラムマッピング")
        st.write("CSVファイルの列と内部データモデルのマッピングを設定します。")
        
        # サンプルCSVを読み込む（最初のファイルをサンプルとして使用）
        sample_file = next((f["file_obj"] for f in state["uploaded_files"] if f["name"].lower().endswith(".csv")), None)
        
        if sample_file:
            try:
                # サンプルとして先頭5行を読み込む
                sample_df = pd.read_csv(
                    sample_file,
                    delimiter=delimiter,
                    encoding=encoding,
                    skiprows=int(skip_rows),
                    nrows=5
                )
                
                # ファイルポインタをリセット
                sample_file.seek(0)
                
                # サンプルデータを表示
                st.write("**サンプルデータ (先頭5行):**")
                st.dataframe(sample_df, use_container_width=True)
                
                # カラムマッピングの設定
                column_mapping = {}
                
                # 必須フィールド
                st.write("**必須フィールドのマッピング:**")
                required_fields = ["timestamp", "latitude", "longitude"]
                
                for field in required_fields:
                    field_labels = {
                        "timestamp": "タイムスタンプ",
                        "latitude": "緯度",
                        "longitude": "経度"
                    }
                    
                    field_hints = {
                        "timestamp": "日時を含む列",
                        "latitude": "緯度を含む列",
                        "longitude": "経度を含む列"
                    }
                    
                    column_mapping[field] = st.selectbox(
                        f"{field_labels.get(field, field)}",
                        options=[""] + list(sample_df.columns),
                        index=0,
                        help=field_hints.get(field, ""),
                        key=f"batch_csv_map_{field}"
                    )
                
                # オプションフィールド
                st.write("**オプションフィールドのマッピング:**")
                
                col1, col2 = st.columns(2)
                
                optional_fields = [
                    ("speed", "速度"),
                    ("course", "方位"),
                    ("elevation", "高度"),
                    ("heart_rate", "心拍数"),
                    ("power", "パワー"),
                    ("distance", "距離"),
                    ("temperature", "温度"),
                    ("wind_speed", "風速"),
                    ("wind_direction", "風向")
                ]
                
                for i, (field, label) in enumerate(optional_fields):
                    with col1 if i % 2 == 0 else col2:
                        column_mapping[field] = st.selectbox(
                            f"{label}",
                            options=[""] + list(sample_df.columns),
                            index=0,
                            key=f"batch_csv_map_opt_{field}"
                        )
                
                # 空の値を削除
                column_mapping = {k: v for k, v in column_mapping.items() if v}
                
                # マッピングをインポート設定に追加
                if column_mapping:
                    import_settings["column_mapping"] = column_mapping
                
                # 必須フィールドがすべてマッピングされているかチェック
                missing_required = [field for field in required_fields if field not in column_mapping]
                if missing_required:
                    st.warning(f"以下の必須フィールドがマッピングされていません: {', '.join(missing_required)}")
            
            except Exception as e:
                st.error(f"サンプルCSVの読み込みエラー: {str(e)}")
        else:
            st.warning("CSVファイルのサンプルがないため、カラムマッピングをスキップします。実際のインポート時に手動でマッピングする必要があります。")
    
    elif selected_format in ["GPX", "TCX", "FIT"]:
        st.info(f"{selected_format}ファイルはGPSデータを自動的に解析します。特別な設定は必要ありません。")
    
    # セッション状態を更新
    state["selected_format"] = selected_format
    state["import_settings"] = import_settings

def render_metadata_section():
    """メタデータ設定セクションをレンダリング"""
    state = st.session_state[SESSION_STATE_KEY]
    
    st.write("すべてのインポートファイルに共通のメタデータを設定します。")
    
    # メタデータ入力フォーム
    metadata = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        metadata["name"] = st.text_input("名前（セッション名のプレフィックスとして使用）", key="batch_meta_name")
        metadata["location"] = st.text_input("場所", key="batch_meta_location")
        metadata["boat_type"] = st.text_input("ボートタイプ", key="batch_meta_boat_type")
    
    with col2:
        metadata["sailor"] = st.text_input("セーラー名", key="batch_meta_sailor")
        metadata["coach"] = st.text_input("コーチ名", key="batch_meta_coach")
        metadata["weather_conditions"] = st.text_input("気象条件", key="batch_meta_weather")
    
    # タグ
    metadata["tags"] = st.text_input(
        "タグ（カンマ区切り）",
        help="タグを使用してデータを整理します。カンマで区切って複数指定できます。",
        key="batch_meta_tags"
    )
    
    # タグをリストに変換
    if metadata["tags"]:
        metadata["tags"] = [tag.strip() for tag in metadata["tags"].split(",")]
    else:
        metadata["tags"] = []
    
    # メモ/説明
    metadata["description"] = st.text_area("説明", key="batch_meta_description")
    
    # プロジェクト選択
    st.subheader("インポート先プロジェクト")
    st.write("インポートしたファイルはセッションとして保存されます。")
    
    projects = get_available_projects()
    
    if projects:
        project_options = {p["id"]: p["name"] for p in projects}
        selected_project_id = st.selectbox(
            "プロジェクト",
            options=list(project_options.keys()),
            format_func=lambda x: project_options.get(x, "不明なプロジェクト"),
            key="batch_project_selector"
        )
        
        metadata["project_id"] = selected_project_id
    else:
        st.warning("利用可能なプロジェクトがありません。先にプロジェクトを作成してください。")
        if st.button("新規プロジェクト作成", key="batch_create_project_btn"):
            st.session_state.current_page = "project_create"
            st.rerun()
    
    # セッション状態を更新
    state["metadata"] = metadata

def render_import_execution():
    """インポート実行セクションをレンダリング"""
    state = st.session_state[SESSION_STATE_KEY]
    
    st.subheader("インポート実行")
    
    # インポート前の概要を表示
    file_count = len(state["uploaded_files"])
    selected_format = state["selected_format"]
    
    st.write(f"**インポートするファイル数:** {file_count}")
    st.write(f"**選択された形式:** {selected_format}")
    
    # 設定の概要
    with st.expander("インポート設定の概要", expanded=False):
        if state["import_settings"]:
            for key, value in state["import_settings"].items():
                if key != "column_mapping":
                    st.write(f"**{key}:** {value}")
                else:
                    st.write("**カラムマッピング:**")
                    for field, column in value.items():
                        st.write(f"- {field}: {column}")
        else:
            st.write("特別な設定はありません。")
    
    # メタデータの概要
    with st.expander("メタデータの概要", expanded=False):
        for key, value in state["metadata"].items():
            if key != "tags":
                st.write(f"**{key}:** {value}")
            else:
                st.write(f"**{key}:** {', '.join(value)}")
    
    # インポート開始ボタン
    start_import = st.button(
        "インポートを開始",
        key="batch_start_import",
        type="primary",
        disabled=state.get("import_started", False)
    )
    
    if start_import:
        state["import_started"] = True
        state["import_results"] = []
        state["current_file_index"] = 0
        state["import_progress"] = 0.0
        state["success_count"] = 0
        state["failed_count"] = 0
    
    # インポートの実行
    if state.get("import_started", False) and not state.get("import_completed", False):
        perform_batch_import()

def perform_batch_import():
    """バッチインポートを実行"""
    state = st.session_state[SESSION_STATE_KEY]
    
    # プログレスバーを表示
    progress_bar = st.progress(0)
    
    # ステータステキスト
    status_text = st.empty()
    
    # 現在処理中のファイルとインデックス
    current_index = state["current_file_index"]
    total_files = len(state["uploaded_files"])
    
    if current_index >= total_files:
        # すべてのファイルのインポートが完了
        state["import_completed"] = True
        progress_bar.progress(1.0)
        status_text.success(f"インポート完了: {state['success_count']}成功 / {state['failed_count']}失敗")
        return
    
    # 現在のファイル
    current_file = state["uploaded_files"][current_index]
    status_text.info(f"インポート中 ({current_index + 1}/{total_files}): {current_file['name']}")
    
    # インポート実行
    try:
        # インポートコントローラーを取得
        from ui.integrated.controllers.import_controller import ImportController
        controller = ImportController(key_prefix=f"batch_import_{current_index}")
        
        # ファイル形式
        file_format = state["selected_format"]
        
        # インポート設定
        import_settings = state["import_settings"].copy()
        
        # メタデータの準備
        metadata = state["metadata"].copy()
        
        # ファイル固有のメタデータを追加（ファイル名をセッション名に使用）
        file_name = Path(current_file["name"]).stem
        metadata["name"] = metadata.get("name", "") + " " + file_name if metadata.get("name") else file_name
        
        # インポート実行
        container = controller.import_data(
            file_obj=current_file["file_obj"],
            file_format=file_format,
            import_settings=import_settings,
            metadata=metadata,
            run_validation=True
        )
        
        # インポート結果を保存
        result = {
            "file_name": current_file["name"],
            "success": container is not None,
            "errors": controller.get_errors(),
            "warnings": controller.get_warnings(),
            "container_id": container.container_id if container else None
        }
        
        state["import_results"].append(result)
        
        # 成功・失敗のカウント
        if result["success"]:
            state["success_count"] += 1
            
            # プロジェクトが指定されている場合はセッションを作成
            if "project_id" in metadata and metadata["project_id"]:
                try:
                    # セッションを作成
                    session_created = controller.create_session_from_container(
                        project_id=metadata["project_id"],
                        name=metadata["name"],
                        description=metadata.get("description", ""),
                        tags=metadata.get("tags", [])
                    )
                    
                    result["session_created"] = session_created
                except Exception as e:
                    result["session_created"] = False
                    result["session_error"] = str(e)
            
        else:
            state["failed_count"] += 1
    
    except Exception as e:
        # 予期しないエラーが発生した場合
        state["import_results"].append({
            "file_name": current_file["name"],
            "success": False,
            "errors": [f"インポート中にエラーが発生しました: {str(e)}"],
            "warnings": [],
            "container_id": None
        })
        state["failed_count"] += 1
    
    # 次のファイルへ
    state["current_file_index"] += 1
    state["import_progress"] = state["current_file_index"] / total_files
    
    # プログレスバーを更新
    progress_bar.progress(state["import_progress"])
    
    # 更新を表示するためにページをリロード
    st.rerun()

def render_import_results():
    """インポート結果セクションをレンダリング"""
    state = st.session_state[SESSION_STATE_KEY]
    
    st.subheader("インポート結果")
    
    # 結果の概要
    success_count = state["success_count"]
    failed_count = state["failed_count"]
    total_count = success_count + failed_count
    
    # メトリクス表示
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("総ファイル数", total_count)
    with col2:
        st.metric("成功", success_count)
    with col3:
        st.metric("失敗", failed_count)
    
    # 詳細結果
    results = state["import_results"]
    
    if results:
        # 結果のデータフレーム
        result_df = pd.DataFrame([
            {
                "ファイル名": r["file_name"],
                "結果": "成功" if r["success"] else "失敗",
                "エラー": ", ".join(r["errors"]) if r["errors"] else "なし",
                "警告": len(r["warnings"]),
                "セッション作成": "成功" if r.get("session_created", False) else ("失敗" if "session_created" in r else "未実行")
            }
            for r in results
        ])
        
        st.dataframe(result_df, use_container_width=True, hide_index=True)
        
        # 詳細情報
        with st.expander("詳細なエラーと警告を表示", expanded=False):
            for i, result in enumerate(results):
                if not result["success"] or result["warnings"]:
                    st.markdown(f"#### {result['file_name']}")
                    
                    if result["errors"]:
                        st.error("エラー:")
                        for error in result["errors"]:
                            st.write(f"- {error}")
                    
                    if result["warnings"]:
                        st.warning("警告:")
                        for warning in result["warnings"]:
                            st.write(f"- {warning}")
                    
                    st.divider()
    else:
        st.info("インポート結果はまだありません。")

def format_file_size(size_bytes: int) -> str:
    """
    ファイルサイズを読みやすい形式に変換
    
    Parameters
    ----------
    size_bytes : int
        バイト単位のサイズ
        
    Returns
    -------
    str
        読みやすい形式のサイズ（例: 1.23 MB）
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

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
