# -*- coding: utf-8 -*-
import sys
import os
import importlib
import inspect
import traceback

# カレントディレクトリをパスに追加
sys.path.insert(0, os.getcwd())

print("テスト収集デバッグ開始")

try:
    import pytest
    
    # 利用可能なテストファイルを探す
    test_files = []
    for root, dirs, files in os.walk('tests'):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(os.path.join(root, file))
    
    print(f"見つかったテストファイル数: {len(test_files)}")
    
    # テストファイルのエンコーディングをチェック
    for test_file in test_files[:5]:  # 最初の5つのみ表示
        print(f"テストファイル: {test_file}")
        try:
            # テキストモードで開いてみる
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read(100)  # 最初の100文字だけ読む
                print(f"  読み込み成功: 先頭 '{content[:30]}...'")
        except UnicodeDecodeError as e:
            print(f"  UTF-8デコードエラー: {e}")
            # バイナリモードで開いて問題のバイトを表示
            with open(test_file, 'rb') as f:
                binary_content = f.read(100)
                print(f"  バイナリ内容: {binary_content}")
    
    # モジュールをインポートしてみる
    test_modules = [
        'tests.test_wind_field_fusion_system',
        'tests.test_wind_field_fusion'
    ]
    
    for module_name in test_modules:
        print(f"モジュールインポート試行: {module_name}")
        try:
            module = importlib.import_module(module_name)
            print(f"  インポート成功: {module.__file__}")
            
            # テストクラスの検出
            test_classes = []
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and name.startswith('Test'):
                    test_classes.append(name)
            
            print(f"  テストクラス: {test_classes}")
        except Exception as e:
            print(f"  インポートエラー: {e}")
    
    # pytestによるテスト収集のシミュレーション
    print("\npytestによるテスト収集シミュレーション:")
    try:
        from _pytest.config import Config
        from _pytest.runner import CallInfo
        from _pytest.main import Session
        
        print("pytestのインポート成功")
        
        # テスト収集ドライランの試行
        try:
            # pytestのプログラム的APIを使って収集のみ行う
            print("テスト収集の開始...")
            # 簡略化のためにファイル数を制限
            test_path = 'tests/test_wind_field_fusion_system.py'
            result = pytest.main(['--collect-only', '-vqs', test_path])
            print(f"テスト収集結果: {result}")
        except Exception as e:
            print(f"テスト収集エラー: {e}")
            traceback.print_exc()
    except ImportError:
        print("pytestのインポートに失敗しました")

except Exception as e:
    print(f"全体エラー: {e}")
    traceback.print_exc()

print("テスト収集デバッグ終了")
