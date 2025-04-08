"""
ui.components.forms.import_wizard.components.enhanced_column_mapper

強化された列マッピング用のUIコンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
import json
import os
from pathlib import Path
import difflib


def enhanced_column_mapper(
    columns: List[str],
    required_fields: List[str],
    optional_fields: List[Dict[str, str]],
    current_mapping: Dict[str, str] = None,
    sample_data: Optional[pd.DataFrame] = None,
    key_prefix: str = "enhanced_column_mapper"
) -> Dict[str, str]:
    """
    強化されたCSVの列マッピングUIを提供
    
    Parameters
    ----------
    columns : List[str]
        CSVファイルの列名リスト
    required_fields : List[str]
        必須フィールドのリスト
    optional_fields : List[Dict[str, str]]
        オプションフィールドのリスト（各辞書はkeyとlabelを含む）
    current_mapping : Dict[str, str], optional
        現在のマッピング（key: 変換後のフィールド名, value: 元の列名）
    sample_data : Optional[pd.DataFrame], optional
        サンプルデータ（プレビュー表示用）
    key_prefix : str, optional
        Streamlitコンポーネントのキープレフィックス
        
    Returns
    -------
    Dict[str, str]
        更新された列マッピング
    """
    mapping = current_mapping.copy() if current_mapping else {}
    
    st.write("### 列マッピング")
    
    # ヘルプ情報
    with st.expander("列マッピングのヘルプ", expanded=False):
        st.markdown("""
        **列マッピングとは？**
        
        CSVファイルの列名とシステムが必要とするフィールド名が一致しない場合、このマッピングで対応関係を指定します。
        
        例えば、CSVファイルに「GPS_Time」という列がある場合、それを「timestamp」（タイムスタンプ）フィールドとして使うことをここで指定します。
        
        **必須フィールド**は全て指定する必要があります。**オプションフィールド**は、対応する列がある場合のみ指定してください。
        """)
    
    # カラム情報の表示
    if sample_data is not None and len(sample_data) > 0:
        with st.expander("CSVファイルの列情報", expanded=False):
            # カラム情報テーブルの作成
            column_info = []
            for col in columns:
                col_data = sample_data[col]
                data_type = str(col_data.dtype)
                
                # サンプル値（最初の数値）
                sample_values = col_data.dropna().head(3).tolist()
                sample_str = ", ".join([str(val) for val in sample_values])
                
                # 空でない値の数
                non_null_count = col_data.count()
                non_null_percent = (non_null_count / len(col_data)) * 100 if len(col_data) > 0 else 0
                
                column_info.append({
                    "列名": col,
                    "データ型": data_type,
                    "サンプル値": sample_str,
                    "空でない値": f"{non_null_count} ({non_null_percent:.1f}%)"
                })
            
            # 情報テーブルの表示
            st.dataframe(pd.DataFrame(column_info), use_container_width=True)
    
    # マッピング設定の保存/読み込み
    mapping_profiles = _load_mapping_profiles()
    if mapping_profiles:
        st.write("#### 保存されたマッピング設定")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_profile = st.selectbox(
                "保存済みのマッピング設定",
                options=["選択してください"] + list(mapping_profiles.keys()),
                key=f"{key_prefix}_profile_select"
            )
        
        with col2:
            if selected_profile != "選択してください":
                if st.button("適用", key=f"{key_prefix}_apply_profile"):
                    # 存在する列のみをマッピングに使用
                    profile_mapping = mapping_profiles[selected_profile]
                    mapping = {k: v for k, v in profile_mapping.items() if v in columns}
                    st.success(f"マッピング設定 '{selected_profile}' を適用しました")
    
    # 自動マッピング機能
    if not mapping or st.button("自動マッピングを実行", key=f"{key_prefix}_auto_map"):
        auto_mapping = _auto_detect_mapping(columns, required_fields, optional_fields, sample_data)
        # 既存のマッピングと自動検出したマッピングをマージ
        for field, column in auto_mapping.items():
            if field not in mapping or mapping[field] == "---":
                mapping[field] = column
        
        if auto_mapping:
            st.success(f"{len(auto_mapping)}個の列を自動マッピングしました")
    
    # 必須フィールドのマッピング
    st.write("#### 必須フィールド")
    
    # 必須フィールドのマッピング状態を視覚的に表示
    required_status = []
    for field in required_fields:
        if field in mapping and mapping[field] != "---":
            status = "✅ マッピング済み"
            color = "green"
        else:
            status = "❌ 未マッピング"
            color = "red"
        
        required_status.append(f"<span style='color: {color}'>{_get_field_label(field)}: {status}</span>")
    
    status_html = " &nbsp;&nbsp; ".join(required_status)
    st.markdown(f"<div style='margin-bottom: 10px;'>{status_html}</div>", unsafe_allow_html=True)
    
    for field in required_fields:
        # 列のオプションを作成（"---"は選択なしを表す）
        options = ["---"] + columns
        
        # 自動推奨ソート（類似度でソート）
        sorted_options = _sort_options_by_field_similarity(field, options)
        
        # 現在のマッピングを検索、なければ最初のオプションを使用
        current_value = mapping.get(field, "---")
        current_index = sorted_options.index(current_value) if current_value in sorted_options else 0
        
        # フィールド説明（フィールド名によって変更）
        field_label = _get_field_label(field)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 選択ボックス
            selected = st.selectbox(
                field_label,
                options=sorted_options,
                index=current_index,
                key=f"{key_prefix}_{field}"
            )
        
        with col2:
            # ヒント表示
            if field == "timestamp":
                st.info("日時情報を含む列")
            elif field == "latitude":
                st.info("緯度情報（-90〜90度）")
            elif field == "longitude":
                st.info("経度情報（-180〜180度）")
        
        # 選択内容をマッピングに反映
        if selected != "---":
            mapping[field] = selected
        elif field in mapping:
            # '---'が選択された場合は、マッピングから削除
            del mapping[field]
        
        # サンプルデータがあれば、選択された列のサンプル値を表示
        if sample_data is not None and selected in sample_data.columns:
            col_data = sample_data[selected]
            data_type = col_data.dtype
            
            # サンプル値と適合性チェック
            sample_values = col_data.dropna().head(3).tolist()
            sample_str = ", ".join([str(val) for val in sample_values])
            
            # フィールド固有の検証
            validation_message = ""
            validation_color = "blue"
            
            if field == "timestamp":
                # タイムスタンプの検証
                try:
                    pd.to_datetime(col_data.head())
                    validation_message = "✓ 日時形式として認識できます"
                    validation_color = "green"
                except:
                    validation_message = "⚠ 日時形式として認識できない可能性があります"
                    validation_color = "orange"
            
            elif field == "latitude":
                # 緯度の検証（-90〜90の範囲内か）
                numeric_data = pd.to_numeric(col_data, errors='coerce')
                if numeric_data.min() >= -90 and numeric_data.max() <= 90:
                    validation_message = "✓ 緯度として妥当な範囲です"
                    validation_color = "green"
                else:
                    validation_message = "⚠ 緯度の範囲外の値があります"
                    validation_color = "orange"
            
            elif field == "longitude":
                # 経度の検証（-180〜180の範囲内か）
                numeric_data = pd.to_numeric(col_data, errors='coerce')
                if numeric_data.min() >= -180 and numeric_data.max() <= 180:
                    validation_message = "✓ 経度として妥当な範囲です"
                    validation_color = "green"
                else:
                    validation_message = "⚠ 経度の範囲外の値があります"
                    validation_color = "orange"
            
            # サンプル値と検証結果の表示
            st.caption(f"サンプル値: {sample_str}")
            if validation_message:
                st.markdown(f"<span style='color: {validation_color}'>{validation_message}</span>", unsafe_allow_html=True)
    
    # オプションフィールドのマッピング
    st.write("#### オプションフィールド")
    st.write("データに含まれる場合は選択してください。")
    
    # オプションフィールドを2つのカテゴリに分ける
    navigation_fields = ["speed", "course", "elevation", "distance"]
    biometric_fields = ["heart_rate", "cadence", "power", "temperature"]
    weather_fields = ["wind_speed", "wind_direction"]
    
    # フィールドをグループ化
    field_groups = {
        "航法データ": [field for field in optional_fields if field["key"] in navigation_fields],
        "生体・センサーデータ": [field for field in optional_fields if field["key"] in biometric_fields],
        "気象データ": [field for field in optional_fields if field["key"] in weather_fields],
        "その他": [field for field in optional_fields if field["key"] not in navigation_fields + biometric_fields + weather_fields]
    }
    
    # グループごとに表示
    for group_name, fields in field_groups.items():
        if fields:  # フィールドがある場合のみ表示
            st.write(f"**{group_name}:**")
            
            # 2列レイアウト
            cols = st.columns(2)
            
            for i, field_info in enumerate(fields):
                field = field_info["key"]
                field_label = field_info["label"]
                
                # 列のオプションを作成
                options = ["（なし）"] + columns
                
                # 自動推奨ソート
                sorted_options = ["（なし）"] + _sort_options_by_field_similarity(field, [opt for opt in options if opt != "（なし）"])
                
                current_value = mapping.get(field, "（なし）")
                current_index = sorted_options.index(current_value) if current_value in sorted_options else 0
                
                with cols[i % 2]:
                    # オプションフィールドの選択UI
                    col_select, col_hint = st.columns([3, 1])
                    
                    with col_select:
                        selected = st.selectbox(
                            f"{field_label} ({field})",
                            options=sorted_options,
                            index=current_index,
                            key=f"{key_prefix}_opt_{field}"
                        )
                    
                    with col_hint:
                        # フィールド固有のヒント
                        if field == "speed":
                            st.info("速度（ノット）")
                        elif field == "course":
                            st.info("進行方向（度）")
                        elif field == "elevation":
                            st.info("高度（m）")
                        elif field == "heart_rate":
                            st.info("心拍数（bpm）")
                    
                    # 選択内容をマッピングに反映
                    if selected != "（なし）":
                        mapping[field] = selected
                    elif field in mapping:
                        del mapping[field]
                    
                    # サンプルデータがあれば、選択された列のサンプル値を表示
                    if sample_data is not None and selected in sample_data.columns:
                        sample_values = sample_data[selected].dropna().head(2).tolist()
                        sample_str = ", ".join([str(val) for val in sample_values])
                        st.caption(f"サンプル値: {sample_str}")
    
    # マッピング設定の保存
    st.write("#### マッピング設定の保存")
    col_save1, col_save2 = st.columns([3, 1])
    
    with col_save1:
        new_profile_name = st.text_input(
            "マッピング設定名",
            key=f"{key_prefix}_new_profile_name",
            placeholder="設定名を入力（例：MyGPSデバイス）"
        )
    
    with col_save2:
        if st.button("保存", key=f"{key_prefix}_save_profile"):
            if new_profile_name:
                # 保存処理
                _save_mapping_profile(new_profile_name, mapping)
                st.success(f"マッピング設定 '{new_profile_name}' を保存しました")
            else:
                st.warning("設定名を入力してください")
    
    # マッピングのプレビュー
    if mapping and sample_data is not None:
        st.write("#### マッピングプレビュー")
        preview_df = pd.DataFrame()
        
        # マッピングされた列だけを表示
        for target, source in mapping.items():
            if source in sample_data.columns:
                preview_df[target] = sample_data[source]
        
        if not preview_df.empty:
            st.dataframe(preview_df.head())
            
            # 必須フィールドの検証
            missing_required = [field for field in required_fields if field not in preview_df.columns]
            if missing_required:
                st.warning(f"必須フィールドがマッピングされていません: {', '.join(missing_required)}")
            else:
                st.success("必須フィールドはすべてマッピングされています")
        else:
            st.info("プレビューデータがありません")
    
    return mapping


def _auto_detect_mapping(columns: List[str], required_fields: List[str], 
                         optional_fields: List[Dict[str, str]], 
                         sample_data: Optional[pd.DataFrame] = None) -> Dict[str, str]:
    """
    列名から自動的にマッピングを検出する
    
    Parameters
    ----------
    columns : List[str]
        CSVファイルの列名リスト
    required_fields : List[str]
        必須フィールドのリスト
    optional_fields : List[Dict[str, str]]
        オプションフィールドのリスト
    sample_data : Optional[pd.DataFrame], optional
        サンプルデータ
        
    Returns
    -------
    Dict[str, str]
        検出されたマッピング
    """
    mapping = {}
    
    # すべてのフィールドリストを作成
    all_fields = required_fields + [field["key"] for field in optional_fields]
    
    # 列名を小文字に変換してリストを作成（処理用）
    lowercase_columns = [col.lower() for col in columns]
    
    # 各フィールドについて、最も類似した列名を検出
    for field in all_fields:
        # そのフィールドの一般的な同義語パターンを定義
        patterns = _get_field_patterns(field)
        
        # 完全一致のチェック
        exact_match = None
        for i, col_lower in enumerate(lowercase_columns):
            if col_lower in patterns:
                exact_match = columns[i]
                break
        
        if exact_match:
            mapping[field] = exact_match
            continue
        
        # 部分一致のチェック
        partial_match = None
        best_score = 0
        
        for i, col_lower in enumerate(lowercase_columns):
            for pattern in patterns:
                if pattern in col_lower:
                    # 単語全体が含まれているかをスコア化
                    if pattern == col_lower or f"_{pattern}" in col_lower or pattern == col_lower.split('_')[-1]:
                        score = len(pattern) / len(col_lower)
                        if score > best_score:
                            best_score = score
                            partial_match = columns[i]
        
        if partial_match and best_score > 0.3:  # 30%以上の一致度
            mapping[field] = partial_match
            continue
        
        # 類似度によるマッチング
        if not exact_match and not partial_match:
            closest_match = None
            best_similarity = 0
            
            for i, col in enumerate(columns):
                # 各パターンとの最大類似度を計算
                max_pattern_similarity = 0
                for pattern in patterns:
                    similarity = difflib.SequenceMatcher(None, pattern, col.lower()).ratio()
                    max_pattern_similarity = max(max_pattern_similarity, similarity)
                
                if max_pattern_similarity > best_similarity and max_pattern_similarity > 0.6:  # 60%以上の類似度
                    best_similarity = max_pattern_similarity
                    closest_match = col
            
            if closest_match:
                mapping[field] = closest_match
    
    # サンプルデータがある場合は、データの内容に基づく追加検証
    if sample_data is not None:
        # 各フィールドについて、データ内容に基づく検証
        
        # タイムスタンプの検出（日付/時刻形式のカラム）
        if "timestamp" not in mapping:
            for col in columns:
                if col in sample_data:
                    try:
                        # 日付/時刻として解析できるか試みる
                        pd.to_datetime(sample_data[col].head())
                        mapping["timestamp"] = col
                        break
                    except:
                        pass
        
        # 緯度/経度の検出（値の範囲に基づく）
        lat_lon_candidates = {}
        
        for col in columns:
            if col in sample_data and pd.api.types.is_numeric_dtype(sample_data[col]):
                values = sample_data[col].dropna()
                if len(values) > 0:
                    min_val = values.min()
                    max_val = values.max()
                    
                    # 緯度の範囲 (-90 ~ 90)
                    if "latitude" not in mapping and min_val >= -90 and max_val <= 90:
                        lat_lon_candidates[col] = {"field": "latitude", "range": max_val - min_val}
                    
                    # 経度の範囲 (-180 ~ 180)
                    if "longitude" not in mapping and min_val >= -180 and max_val <= 180:
                        lat_lon_candidates[col] = {"field": "longitude", "range": max_val - min_val}
        
        # 最も変動の大きい列を経度、次を緯度に（通常、経度の方が緯度より変動が大きい）
        sorted_candidates = sorted(lat_lon_candidates.items(), key=lambda x: x[1]["range"], reverse=True)
        
        if len(sorted_candidates) >= 2:
            # 最も変動が大きい列を経度に
            if "longitude" not in mapping:
                mapping["longitude"] = sorted_candidates[0][0]
            
            # 次に変動が大きい列を緯度に
            if "latitude" not in mapping:
                mapping["latitude"] = sorted_candidates[1][0]
        
        # speedの検出（値の範囲に基づく）
        if "speed" not in mapping:
            for col in columns:
                if col in sample_data and pd.api.types.is_numeric_dtype(sample_data[col]):
                    values = sample_data[col].dropna()
                    if len(values) > 0:
                        mean_val = values.mean()
                        # 速度は通常0〜50ノット程度
                        if 0 <= mean_val <= 50:
                            mapping["speed"] = col
                            break
    
    return mapping


def _get_field_patterns(field: str) -> List[str]:
    """
    フィールド名の一般的なパターンを取得
    
    Parameters
    ----------
    field : str
        フィールド名
        
    Returns
    -------
    List[str]
        一般的なパターンのリスト
    """
    patterns = {
        "timestamp": ["time", "date", "timestamp", "datetime", "recorded", "created", "時間", "日時"],
        "latitude": ["lat", "latitude", "緯度", "緯度（度）", "y", "ylat"],
        "longitude": ["lon", "lng", "longitude", "経度", "経度（度）", "x", "xlon"],
        "speed": ["speed", "velocity", "spd", "速度", "speed_kph", "speed_knots", "船速"],
        "course": ["course", "bearing", "heading", "direction", "cog", "進行方向", "方位"],
        "elevation": ["ele", "elev", "elevation", "altitude", "高度", "高さ"],
        "heart_rate": ["hr", "heart", "心拍", "心拍数", "pulse", "bpm"],
        "cadence": ["cad", "cadence", "ケイデンス", "回転数"],
        "power": ["power", "pwr", "pow", "パワー", "出力", "ワット"],
        "distance": ["dist", "distance", "距離", "cumulative_distance", "total_distance"],
        "temperature": ["temp", "temperature", "気温", "温度"],
        "wind_speed": ["wind_speed", "windspeed", "wind_velocity", "風速"],
        "wind_direction": ["wind_direction", "wind_dir", "wind_heading", "風向"]
    }
    
    return patterns.get(field, [field])


def _sort_options_by_field_similarity(field: str, options: List[str]) -> List[str]:
    """
    フィールド名との類似度でオプションをソート
    
    Parameters
    ----------
    field : str
        フィールド名
    options : List[str]
        ソートするオプションのリスト
        
    Returns
    -------
    List[str]
        ソート済みオプションリスト
    """
    # フィールドのパターンを取得
    patterns = _get_field_patterns(field)
    
    # 各オプションのスコアを計算
    option_scores = []
    for option in options:
        option_lower = option.lower()
        
        # スコア計算
        score = 0
        
        # 完全一致の場合は最高スコア
        if option_lower in patterns:
            score = 1.0
        else:
            # パターンとの最大類似度を計算
            max_pattern_score = 0
            for pattern in patterns:
                # 部分一致（含まれている場合）
                if pattern in option_lower:
                    pattern_score = len(pattern) / len(option_lower)
                    max_pattern_score = max(max_pattern_score, pattern_score)
                
                # 類似度スコア
                similarity = difflib.SequenceMatcher(None, pattern, option_lower).ratio()
                max_pattern_score = max(max_pattern_score, similarity * 0.8)  # 類似度は80%のウェイト
            
            score = max_pattern_score
        
        option_scores.append((option, score))
    
    # スコア降順でソート
    sorted_options = [opt for opt, _ in sorted(option_scores, key=lambda x: x[1], reverse=True)]
    
    # 最初のオプションは特別なケース（"---"など）なら元の位置を維持
    if options and (options[0] == "---" or options[0] == "（なし）"):
        sorted_options.remove(options[0])
        sorted_options.insert(0, options[0])
    
    return sorted_options


def _get_field_label(field_name: str) -> str:
    """
    フィールド名から表示用ラベルを取得
    
    Parameters
    ----------
    field_name : str
        フィールド名
        
    Returns
    -------
    str
        表示用ラベル
    """
    labels = {
        "timestamp": "タイムスタンプ (timestamp)",
        "latitude": "緯度 (latitude)",
        "longitude": "経度 (longitude)",
        "speed": "速度 (speed)",
        "course": "方位 (course)",
        "elevation": "高度 (elevation)",
        "heart_rate": "心拍数 (heart_rate)",
        "cadence": "ケイデンス (cadence)",
        "power": "パワー (power)",
        "distance": "距離 (distance)",
        "temperature": "温度 (temperature)",
        "wind_speed": "風速 (wind_speed)",
        "wind_direction": "風向 (wind_direction)"
    }
    
    return labels.get(field_name, field_name)


def _load_mapping_profiles() -> Dict[str, Dict[str, str]]:
    """
    保存されたマッピングプロファイルを読み込む
    
    Returns
    -------
    Dict[str, Dict[str, str]]
        プロファイル名とマッピングの辞書
    """
    try:
        # 設定ディレクトリのパス
        config_dir = Path.home() / ".sailing_analyzer"
        mapping_file = config_dir / "column_mappings.json"
        
        # ディレクトリがなければ作成
        config_dir.mkdir(exist_ok=True)
        
        # ファイルが存在しない場合は空の辞書を返す
        if not mapping_file.exists():
            return {}
        
        # ファイルから読み込み
        with open(mapping_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    except Exception as e:
        st.warning(f"マッピング設定の読み込みに失敗しました: {e}")
        return {}


def _save_mapping_profile(profile_name: str, mapping: Dict[str, str]) -> bool:
    """
    マッピングプロファイルを保存
    
    Parameters
    ----------
    profile_name : str
        プロファイル名
    mapping : Dict[str, str]
        保存するマッピング
        
    Returns
    -------
    bool
        保存成功かどうか
    """
    try:
        # 現在のプロファイルを読み込み
        profiles = _load_mapping_profiles()
        
        # 新しいプロファイルを追加
        profiles[profile_name] = mapping
        
        # 設定ディレクトリのパス
        config_dir = Path.home() / ".sailing_analyzer"
        mapping_file = config_dir / "column_mappings.json"
        
        # ディレクトリがなければ作成
        config_dir.mkdir(exist_ok=True)
        
        # ファイルに保存
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
        
        return True
    
    except Exception as e:
        st.warning(f"マッピング設定の保存に失敗しました: {e}")
        return False
