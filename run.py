#!/usr/bin/env python3
"""
セーリング戦略分析システム起動スクリプト
"""

import os
import sys
import subprocess
import argparse

def main():
    """
    アプリケーションを起動する
    """
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='セーリング戦略分析システムの起動')
    parser.add_argument('--env', default='prod', choices=['dev', 'prod'], 
                        help='実行環境 (dev: 開発, prod: 本番)')
    args = parser.parse_args()
    
    # スクリプトのディレクトリを取得
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # メインアプリケーションのパス
    app_path = os.path.join(script_dir, 'ui', 'app_v5.py')
    print(f"アプリケーションパス: {app_path}")
    
    # 環境変数の設定
    env = os.environ.copy()
    
    # 開発モードの場合
    if args.env == 'dev':
        print("開発モードで起動します...")
        env['STREAMLIT_DEBUG'] = 'true'
        cmd = ['streamlit', 'run', app_path, '--server.runOnSave=true']
    else:
        print("本番モードで起動します...")
        cmd = ['streamlit', 'run', app_path]
    
    # アプリケーションの実行
    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\nアプリケーションを終了します...")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
