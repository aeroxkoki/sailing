# -*- coding: utf-8 -*-
"""
sailing_data_processor.strategy.dependency_utils モジュール

戦略検出モジュールの依存関係を管理するユーティリティ
"""

import sys
import os
import importlib
import warnings
from typing import Optional, Any

def load_module(module_name: str) -> Optional[Any]:
    """
    モジュールを動的にロードする
    
    Parameters:
    -----------
    module_name : str
        ロードするモジュールの名前
        
    Returns:
    --------
    Module or None
        ロードされたモジュール、失敗時はNone
    """
    try:
        module = importlib.import_module(module_name)
        return module
    except ImportError as e:
        warnings.warn(f"モジュール {module_name} のロードに失敗しました: {e}")
        return None

def get_class_from_module(module_name: str, class_name: str) -> Optional[Any]:
    """
    指定されたモジュールからクラスを取得する
    
    Parameters:
    -----------
    module_name : str
        モジュール名
    class_name : str
        クラス名
        
    Returns:
    --------
    class or None
        取得されたクラス、失敗時はNone
    """
    module = load_module(module_name)
    if module:
        try:
            return getattr(module, class_name)
        except AttributeError as e:
            warnings.warn(f"クラス {class_name} がモジュール {module_name} に見つかりません: {e}")
    return None

def safe_import(module_path: str, fallback=None):
    """
    安全なインポートを行い、失敗時はフォールバックを返す
    
    Parameters:
    -----------
    module_path : str
        インポートするモジュールパス
    fallback : Any, optional
        インポート失敗時に返す値
        
    Returns:
    --------
    Any
        インポートされたモジュール、または失敗時のフォールバック値
    """
    try:
        components = module_path.split('.')
        module_name = '.'.join(components[:-1])
        class_name = components[-1]
        
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        warnings.warn(f"{module_path} のインポートに失敗しました: {e}")
        return fallback

def add_project_root_to_path():
    """
    プロジェクトルートディレクトリをPYTHONPATHに追加する
    """
    # 現在のファイルが存在するディレクトリ
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # sailing_data_processorディレクトリ
    module_dir = os.path.dirname(current_dir)
    
    # プロジェクトルート
    project_root = os.path.dirname(module_dir)
    
    # PYTHONPATHに追加
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # モジュールディレクトリも追加
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)