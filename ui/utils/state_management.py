"""
状態管理ユーティリティ

Streamlitのセッション状態を安全に管理するためのユーティリティ関数群
"""

import streamlit as st
import json
import logging
import time
from typing import Any, Dict, Optional, TypeVar, Generic, List, Tuple, Union, Set

T = TypeVar('T')

# ロガーの設定
logger = logging.getLogger(__name__)

def get_or_create_state(key: str, default_value: Any = None) -> Any:
    """
    指定されたキーでセッション状態を取得または作成します。
    存在しない場合はデフォルト値を設定します。
    
    Args:
        key: セッション状態のキー
        default_value: キーが存在しない場合に設定するデフォルト値
        
    Returns:
        取得または作成された状態の値
    """
    if key not in st.session_state:
        st.session_state[key] = default_value
        # 状態の作成をログに記録
        logger.debug(f"新しい状態を作成: {key} = {default_value}")
    
    # 存在確認用のチェックサムキーを設定
    checksum_key = f"_checksum_{key}"
    if checksum_key not in st.session_state:
        # JSON化して簡易的なハッシュを作成（厳密なハッシュではなく一致確認用）
        try:
            value_str = json.dumps(st.session_state[key])
            # 長すぎる値はトリム
            if len(value_str) > 100:
                hash_value = hash(value_str)
            else:
                hash_value = value_str
            st.session_state[checksum_key] = hash_value
        except (TypeError, OverflowError):
            # JSON化できない場合はタイムスタンプを使用
            st.session_state[checksum_key] = time.time()
    
    return st.session_state[key]

def save_state(key: str, value: Any) -> None:
    """
    指定されたキーでセッション状態を更新します。
    
    Args:
        key: セッション状態のキー
        value: 保存する値
    """
    # 値を更新
    st.session_state[key] = value
    
    # チェックサムを更新
    checksum_key = f"_checksum_{key}"
    try:
        value_str = json.dumps(value)
        # 長すぎる値はトリム
        if len(value_str) > 100:
            hash_value = hash(value_str)
        else:
            hash_value = value_str
        st.session_state[checksum_key] = hash_value
    except (TypeError, OverflowError):
        # JSON化できない場合はタイムスタンプを使用
        st.session_state[checksum_key] = time.time()
    
    logger.debug(f"状態を更新: {key}")

def confirm_state_intact(key: str) -> bool:
    """
    指定されたキーの状態が完全に保持されているかチェックします。
    
    Args:
        key: チェックする状態のキー
        
    Returns:
        状態が完全に保持されている場合はTrue、そうでない場合はFalse
    """
    if key not in st.session_state:
        logger.warning(f"状態が見つかりません: {key}")
        return False
    
    checksum_key = f"_checksum_{key}"
    if checksum_key not in st.session_state:
        logger.warning(f"チェックサムが見つかりません: {key}")
        return False
    
    # 現在の値とチェックサムを比較
    current_value = st.session_state[key]
    stored_checksum = st.session_state[checksum_key]
    
    try:
        value_str = json.dumps(current_value)
        # 長すぎる値はトリム
        if len(value_str) > 100:
            current_hash = hash(value_str)
        else:
            current_hash = value_str
        
        if isinstance(stored_checksum, (int, float)) and isinstance(current_hash, (int, float)):
            # 数値同士の比較
            is_intact = stored_checksum == current_hash
        elif isinstance(stored_checksum, str) and isinstance(current_hash, str):
            # 文字列同士の比較
            is_intact = stored_checksum == current_hash
        else:
            # 型の不一致
            is_intact = False
        
        if not is_intact:
            logger.warning(f"状態の整合性チェックに失敗: {key}")
        
        return is_intact
    except (TypeError, OverflowError):
        # 比較できない場合はTrueを返す（安全側に倒す）
        return True

def create_session_id() -> str:
    """
    一意のセッションIDを生成します。
    
    Returns:
        str: 生成されたセッションID
    """
    import uuid
    return str(uuid.uuid4())

def get_or_create_session_id() -> str:
    """
    現在のブラウザセッションに関連付けられた一意のIDを取得または生成します。
    
    Returns:
        str: セッションID
    """
    return get_or_create_state("_session_id", create_session_id())

def clear_view_states() -> None:
    """
    すべてのビュー状態を初期化します。
    ページ間のナビゲーション時などに使用します。
    """
    # ビュー状態の保存キー群
    view_state_keys = [
        "view_state", 
        "selected_session_id", 
        "selected_project_id",
        "confirm_delete_session"
    ]
    
    # 各ビュー状態をクリア
    for key in view_state_keys:
        if key in st.session_state:
            del st.session_state[key]
            logger.debug(f"ビュー状態をクリア: {key}")
    
    # チェックサムもクリア
    checksum_keys = [f"_checksum_{key}" for key in view_state_keys]
    for key in checksum_keys:
        if key in st.session_state:
            del st.session_state[key]
