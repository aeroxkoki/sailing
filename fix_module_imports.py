#!/usr/bin/env python3
"""
Pythonモジュールのインポート問題を診断するスクリプト
"""

import sys
import os
import importlib
import traceback
from pathlib import Path

def test_import(module_path):
    """
    モジュールをインポートし、結果を報告します
    """
    print(f"インポートテスト: {module_path}")
    
    try:
        # モジュールをインポート
        module = importlib.import_module(module_path)
        print(f"✅ インポート成功: {module_path}")
        
        # モジュールのソースファイルパスを表示
        if hasattr(module, "__file__"):
            print(f"  モジュールファイル: {module.__file__}")
        
        return True, module
    except Exception as e:
        print(f"❌ インポートエラー: {module_path}")
        print(f"  エラー: {str(e)}")
        print("  詳細なエラー情報:")
        traceback.print_exc()
        return False, None

def check_syntax(file_path):
    """
    Pythonファイルの構文をチェックします
    """
    print(f"構文チェック: {file_path}")
    
    try:
        # ファイルを開いて構文チェック
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # 構文チェック (コンパイルのみ)
        compiled = compile(source, file_path, 'exec')
        print(f"✅ 構文チェック成功: {file_path}")
        return True
    except SyntaxError as e:
        print(f"❌ 構文エラー: {file_path}")
        print(f"  行 {e.lineno}, 列 {e.offset}: {e.text}")
        print(f"  エラー: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ ファイル読み込みエラー: {file_path}")
        print(f"  エラー: {str(e)}")
        return False

def test_problematic_modules():
    """
    問題のあるモジュールのリストをテスト
    """
    # 問題のあるモジュールのリスト
    modules = [
        "sailing_data_processor.reporting.elements.map.layers.data_connector",
        "sailing_data_processor.reporting.elements.timeline.event_timeline",
        "sailing_data_processor.reporting.elements.timeline.parameter_timeline",
        "sailing_data_processor.reporting.elements.timeline.playback_control",
        "sailing_data_processor.reporting.elements.visualizations.basic_charts",
        "sailing_data_processor.reporting.elements.visualizations.sailing_charts",
        "sailing_data_processor.validation.visualization_improvements"
    ]
    
    results = {}
    
    for module_path in modules:
        # 相対パスに変換
        file_parts = module_path.split('.')
        file_path = os.path.join(*file_parts) + '.py'
        
        # 構文チェック
        syntax_ok = check_syntax(file_path)
        
        if syntax_ok:
            # インポートテスト
            import_ok, _ = test_import(module_path)
        else:
            import_ok = False
        
        results[module_path] = {
            "syntax_ok": syntax_ok,
            "import_ok": import_ok
        }
        
        print("-" * 60)
    
    # 結果の要約
    print("\n結果の要約:")
    for module_path, result in results.items():
        status = "✅" if result["import_ok"] else "❌"
        print(f"{status} {module_path}")
    
    return results

def main():
    """
    メイン関数
    """
    # プロジェクトルートのパスを設定
    project_root = os.path.abspath(os.path.curdir)
    print(f"プロジェクトルート: {project_root}")
    
    # Pythonパスにプロジェクトルートを追加
    sys.path.insert(0, project_root)
    print(f"Python パス: {sys.path}")
    
    # 問題のあるモジュールをテスト
    test_problematic_modules()

if __name__ == "__main__":
    main()
