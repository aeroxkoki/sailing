"""
ui.components.forms.import_wizard.components.metadata_editor

メタデータ編集用のUIコンポーネント
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import json
from pathlib import Path
from datetime import datetime


def metadata_editor(
    current_metadata: Dict[str, Any] = None,
    key_prefix: str = "metadata_editor"
) -> Dict[str, Any]:
    """
    メタデータ編集UIを提供
    
    Parameters
    ----------
    current_metadata : Dict[str, Any], optional
        現在のメタデータ
    key_prefix : str, optional
        Streamlitのキープレフィックス
        
    Returns
    -------
    Dict[str, Any]
        更新されたメタデータ
    """
    st.write("### データメタデータ")
    st.write("インポートするデータに関する追加情報を入力してください。")
    
    metadata = current_metadata.copy() if current_metadata else {}
    
    # メタデータテンプレートの読み込み
    templates = _load_metadata_templates()
    if templates:
        st.write("#### 保存されたテンプレート")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_template = st.selectbox(
                "メタデータテンプレート",
                options=["選択してください"] + list(templates.keys()),
                key=f"{key_prefix}_template_select"
            )
        
        with col2:
            if selected_template != "選択してください":
                if st.button("適用", key=f"{key_prefix}_apply_template"):
                    # テンプレートを適用（現在のメタデータと統合）
                    metadata.update(templates[selected_template])
                    st.success(f"テンプレート '{selected_template}' を適用しました")
    
    # メタデータ入力フォーム
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            # 基本情報
            st.write("#### 基本情報")
            
            # 艇・セーラー情報
            boat_name = st.text_input(
                "ボート名",
                value=metadata.get("boat_name", ""),
                key=f"{key_prefix}_boat_name",
                help="ボートの名前または識別子"
            )
            if boat_name:
                metadata["boat_name"] = boat_name
            
            sailor_name = st.text_input(
                "セーラー名",
                value=metadata.get("sailor_name", ""),
                key=f"{key_prefix}_sailor_name",
                help="セーラーまたはスキッパーの名前"
            )
            if sailor_name:
                metadata["sailor_name"] = sailor_name
            
            boat_class = st.text_input(
                "艇種",
                value=metadata.get("boat_class", ""),
                key=f"{key_prefix}_boat_class",
                help="470、レーザー、49erなどの艇種"
            )
            if boat_class:
                metadata["boat_class"] = boat_class
            
            team_name = st.text_input(
                "チーム名",
                value=metadata.get("team_name", ""),
                key=f"{key_prefix}_team_name",
                help="所属チームやクラブ名"
            )
            if team_name:
                metadata["team_name"] = team_name
        
        with col2:
            # セッション情報
            st.write("#### セッション情報")
            
            session_type = st.selectbox(
                "セッションタイプ",
                options=["", "レース", "練習", "トレーニング", "テスト", "その他"],
                index=["", "レース", "練習", "トレーニング", "テスト", "その他"].index(metadata.get("session_type", "")),
                key=f"{key_prefix}_session_type"
            )
            if session_type:
                metadata["session_type"] = session_type
            
            session_date = st.date_input(
                "セッション日付",
                value=None,
                key=f"{key_prefix}_session_date"
            )
            if session_date:
                metadata["session_date"] = session_date.isoformat()
            
            location = st.text_input(
                "場所",
                value=metadata.get("location", ""),
                key=f"{key_prefix}_location",
                help="レースや練習の場所"
            )
            if location:
                metadata["location"] = location
            
            weather_conditions = st.text_input(
                "気象条件",
                value=metadata.get("weather_conditions", ""),
                key=f"{key_prefix}_weather_conditions",
                help="風速、風向、波の状態など"
            )
            if weather_conditions:
                metadata["weather_conditions"] = weather_conditions
    
    # 追加情報
    with st.expander("追加情報", expanded=False):
        # 追加情報の入力
        notes = st.text_area(
            "備考",
            value=metadata.get("notes", ""),
            key=f"{key_prefix}_notes",
            help="セッションに関する補足情報や観察事項"
        )
        if notes:
            metadata["notes"] = notes
        
        # タグ
        tags_str = st.text_input(
            "タグ（カンマ区切り）",
            value=",".join(metadata.get("tags", [])) if "tags" in metadata else "",
            key=f"{key_prefix}_tags",
            help="カンマ区切りでタグを入力"
        )
        if tags_str:
            metadata["tags"] = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        
        # カスタムフィールド
        st.write("#### カスタムフィールド")
        st.write("任意のカスタムフィールドを追加できます。")
        
        # 既存のカスタムフィールド
        custom_fields = {k: v for k, v in metadata.items() 
                         if k not in ["boat_name", "sailor_name", "boat_class", "team_name", 
                                      "session_type", "session_date", "location", "weather_conditions",
                                      "notes", "tags", "created_at", "updated_at"]}
        
        # 既存フィールドの表示と編集
        if custom_fields:
            st.write("既存のカスタムフィールド:")
            for field_name, field_value in list(custom_fields.items()):
                col1, col2, col3 = st.columns([3, 6, 1])
                with col1:
                    st.text(field_name)
                with col2:
                    new_value = st.text_input(
                        f"値_{field_name}",
                        value=str(field_value),
                        key=f"{key_prefix}_custom_{field_name}",
                        label_visibility="collapsed"
                    )
                    metadata[field_name] = new_value
                with col3:
                    if st.button("削除", key=f"{key_prefix}_delete_{field_name}"):
                        del metadata[field_name]
                        st.experimental_rerun()
        
        # 新規フィールドの追加
        st.write("新規フィールド追加:")
        new_field_col1, new_field_col2, new_field_col3 = st.columns([3, 6, 1])
        with new_field_col1:
            new_field_name = st.text_input(
                "新規フィールド名",
                key=f"{key_prefix}_new_field_name",
                placeholder="フィールド名"
            )
        with new_field_col2:
            new_field_value = st.text_input(
                "新規フィールド値",
                key=f"{key_prefix}_new_field_value",
                placeholder="値"
            )
        with new_field_col3:
            if st.button("追加", key=f"{key_prefix}_add_field"):
                if new_field_name and new_field_name not in metadata:
                    metadata[new_field_name] = new_field_value
                    st.success(f"フィールド '{new_field_name}' を追加しました")
    
    # メタデータテンプレートの保存
    with st.expander("テンプレートとして保存", expanded=False):
        st.write("現在のメタデータをテンプレートとして保存します。")
        
        col_save1, col_save2 = st.columns([3, 1])
        
        with col_save1:
            template_name = st.text_input(
                "テンプレート名",
                key=f"{key_prefix}_template_name",
                placeholder="マイメタデータテンプレート"
            )
        
        with col_save2:
            if st.button("保存", key=f"{key_prefix}_save_template"):
                if template_name:
                    # 保存処理
                    success = _save_metadata_template(template_name, metadata)
                    if success:
                        st.success(f"テンプレート '{template_name}' を保存しました")
                else:
                    st.warning("テンプレート名を入力してください")
    
    # 自動的にタイムスタンプを追加
    metadata["updated_at"] = datetime.now().isoformat()
    if "created_at" not in metadata:
        metadata["created_at"] = datetime.now().isoformat()
    
    return metadata


def _load_metadata_templates() -> Dict[str, Dict[str, Any]]:
    """
    メタデータテンプレートを読み込む
    
    Returns
    -------
    Dict[str, Dict[str, Any]]
        テンプレート名とメタデータの辞書
    """
    try:
        # 設定ディレクトリのパス
        config_dir = Path.home() / ".sailing_analyzer"
        template_file = config_dir / "metadata_templates.json"
        
        # ディレクトリがなければ作成
        config_dir.mkdir(exist_ok=True)
        
        # ファイルが存在しない場合は空の辞書を返す
        if not template_file.exists():
            return {}
        
        # ファイルから読み込み
        with open(template_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    except Exception as e:
        st.warning(f"メタデータテンプレートの読み込みに失敗しました: {e}")
        return {}


def _save_metadata_template(template_name: str, metadata: Dict[str, Any]) -> bool:
    """
    メタデータテンプレートを保存
    
    Parameters
    ----------
    template_name : str
        テンプレート名
    metadata : Dict[str, Any]
        保存するメタデータ
        
    Returns
    -------
    bool
        保存成功かどうか
    """
    try:
        # タイムスタンプなどの一時的な値は除外
        save_metadata = metadata.copy()
        for key in ["created_at", "updated_at"]:
            if key in save_metadata:
                del save_metadata[key]
        
        # 現在のテンプレートを読み込み
        templates = _load_metadata_templates()
        
        # 新しいテンプレートを追加
        templates[template_name] = save_metadata
        
        # 設定ディレクトリのパス
        config_dir = Path.home() / ".sailing_analyzer"
        template_file = config_dir / "metadata_templates.json"
        
        # ディレクトリがなければ作成
        config_dir.mkdir(exist_ok=True)
        
        # ファイルに保存
        with open(template_file, "w", encoding="utf-8") as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        
        return True
    
    except Exception as e:
        st.warning(f"メタデータテンプレートの保存に失敗しました: {e}")
        return False
