# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - エンコーディングユーティリティ

日本語テキストの処理とエンコーディング問題に対応するためのユーティリティ関数
"""

import unicodedata
import re
from typing import Dict, Any, Union, List


def normalize_japanese_text(text: str) -> str:
    """
    日本語テキストの正規化を行う。
    全角/半角の統一、異体字の正規化などを実施。
    
    Args:
        text: 正規化する日本語テキスト
        
    Returns:
        正規化された日本語テキスト
    """
    if not text:
        return text
        
    # Unicode正規化（NFCフォーム）
    normalized = unicodedata.normalize('NFC', text)
    return normalized


def sanitize_json_strings(data: Union[Dict[str, Any], List[Any], str]) -> Union[Dict[str, Any], List[Any], str]:
    """
    JSONデータ内のすべての文字列に対して日本語正規化を実施。
    辞書、リスト、または文字列を再帰的に処理。
    
    Args:
        data: 処理するデータ（辞書、リスト、または文字列）
        
    Returns:
        処理済みのデータ
    """
    if isinstance(data, dict):
        return {k: sanitize_json_strings(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_json_strings(item) for item in data]
    elif isinstance(data, str):
        return normalize_japanese_text(data)
    else:
        return data


def detect_encoding_issues(text: str) -> bool:
    """
    テキスト内のエンコーディング問題を検出。
    文字化けの可能性がある特殊なパターンをチェック。
    
    Args:
        text: チェックするテキスト
        
    Returns:
        問題がある場合はTrue、それ以外はFalse
    """
    if not text:
        return False
        
    # エンコーディング問題の可能性があるパターン
    problematic_patterns = [
        r'[\uFFFD]',  # 置換文字
        r'[\u0000-\u001F\u007F-\u009F]',  # 制御文字
    ]
    
    for pattern in problematic_patterns:
        if re.search(pattern, text):
            return True
            
    return False


def fix_common_encoding_issues(text: str) -> str:
    """
    一般的なエンコーディング問題の修正を試みる。
    
    Args:
        text: 修正するテキスト
        
    Returns:
        修正されたテキスト
    """
    if not text:
        return text
    
    # 制御文字の削除
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
    
    # 置換文字を空白に置き換え
    text = text.replace('\uFFFD', ' ')
    
    return text.strip()
