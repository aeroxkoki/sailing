#!/usr/bin/env python3
"""テスト収集エラーをチェックするスクリプト"""

import sys
import os
import pytest
import traceback

def main():
    # プロジェクトのルートディレクトリをPythonパスに追加
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    
    # プロジェクトディレクトリに移動
    os.chdir(project_root)
    
    try:
        # テストの収集のみを実行し、エラーを確認
        exit_code = pytest.main([
            '--collect-only',
            '--ignore=tests/project/',
            '--tb=short',
            'tests/'
        ])
        
        if exit_code != 0:
            print(f"テスト収集中にエラーが発生しました: exit_code={exit_code}")
            
            # エラーの詳細を取得
            print("\n詳細なエラー情報を収集します...")
            exit_code = pytest.main([
                '--collect-only',
                '--ignore=tests/project/',
                '--tb=long',
                '-v',
                'tests/'
            ])
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
