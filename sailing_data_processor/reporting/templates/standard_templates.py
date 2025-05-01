# -*- coding: utf-8 -*-
"""
Standard templates for reports

This module provides standard templates for sailing data reports
"""

from typing import Dict, List, Any, Optional

def create_basic_template():
    """
    基本レポートテンプレートを作成
    
    セッションの基本情報と主要指標を表示する標準テンプレート
    
    Returns
    -------
    Template
        基本レポートテンプレート
    """
    # スタブ実装 - 実際のTemplate実装はここに追加
    return {"name": "基本レポート", "type": "basic"}

def create_detailed_template():
    """
    詳細分析レポートテンプレートを作成
    
    詳細な分析結果とグラフを含む高度なレポートテンプレート
    
    Returns
    -------
    Template
        詳細分析レポートテンプレート
    """
    # スタブ実装
    return {"name": "詳細分析レポート", "type": "detailed"}

def create_presentation_template():
    """
    プレゼンテーション用テンプレートを作成
    
    視覚的な要素を重視したプレゼンテーション用テンプレート
    
    Returns
    -------
    Template
        プレゼンテーション用テンプレート
    """
    # スタブ実装
    return {"name": "プレゼンテーションレポート", "type": "presentation"}

def create_coaching_template():
    """
    コーチング用テンプレートを作成
    
    改善点と次のステップにフォーカスしたコーチング用テンプレート
    
    Returns
    -------
    Template
        コーチング用テンプレート
    """
    # スタブ実装
    return {"name": "コーチング用レポート", "type": "coaching"}

def get_all_standard_templates() -> Dict[str, Any]:
    """
    すべての標準テンプレートを取得
    
    Returns
    -------
    Dict[str, Template]
        テンプレート名をキーとした標準テンプレートの辞書
    """
    return {
        "basic": create_basic_template(),
        "detailed": create_detailed_template(),
        "presentation": create_presentation_template(),
        "coaching": create_coaching_template()
    }
