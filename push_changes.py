#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
セーリング戦略分析システムの修正をGitHubにプッシュするスクリプト

このスクリプトは、修正したセッションマネージャをテストし、成功した場合にGitHubにプッシュします。
"""

import os
import sys
import subprocess
from pathlib import Path
import datetime

def run_command(command, cwd=None, capture_output=True):
    """
    コマンドを実行し、結果を返す関数
    
    Parameters
    ----------
    command : str
        実行するコマンド
    cwd : str, optional
        コマンドを実行するディレクトリ
    capture_output : bool, optional
        出力をキャプチャするかどうか
        
    Returns
    -------
    tuple
        (戻り値, 標準出力, 標準エラー出力)
    """
    print(f"実行コマンド: {command}")
    
    if capture_output:
        result = subprocess.run(command, shell=True, text=True, capture_output=True, cwd=cwd)
        return result.returncode, result.stdout, result.stderr
    else:
        result = subprocess.run(command, shell=True, text=True, cwd=cwd)
        return result.returncode, None, None

def main():
    # プロジェクトのルートディレクトリを取得
    script_path = Path(__file__).resolve()
    project_root = script_path.parent
    print(f"プロジェクトルート: {project_root}")
    
    # PYTHONPATHを設定
    os.environ["PYTHONPATH"] = str(project_root)
    
    # テストを実行
    print("テストを実行中...")
    test_cmd = "python3 -m pytest tests/test_project/test_session_manager.py -v"
    test_status, test_stdout, test_stderr = run_command(test_cmd, cwd=project_root)
    
    # テスト結果を表示
    print("\nテスト結果:")
    if test_stdout:
        print(test_stdout)
    
    if test_stderr:
        print("\nエラー:")
        print(test_stderr)
    
    # テストが失敗した場合は終了
    if test_status != 0:
        print(f"テストに失敗しました。ステータスコード: {test_status}")
        print("修正を再確認してください。")
        return 1
    
    # テストが成功した場合はGitにコミットしてプッシュ
    print("\n変更をコミット中...")
    
    # Gitのステータスを確認
    _, git_status, _ = run_command("git status", cwd=project_root)
    print(git_status)
    
    # 変更をステージング
    stage_cmd = "git add sailing_data_processor/project/session_manager.py"
    run_command(stage_cmd, cwd=project_root)
    
    # コミットメッセージを作成
    commit_msg = f"Fix session_manager.py to pass all tests - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    commit_cmd = f'git commit -m "{commit_msg}"'
    commit_status, commit_stdout, commit_stderr = run_command(commit_cmd, cwd=project_root)
    
    if commit_status != 0:
        print(f"コミットに失敗しました: {commit_stderr}")
        return 1
    
    print(commit_stdout)
    
    # GitHubにプッシュ
    print("\n変更をプッシュ中...")
    push_cmd = "git push"
    push_status, push_stdout, push_stderr = run_command(push_cmd, cwd=project_root)
    
    if push_status != 0:
        print(f"プッシュに失敗しました: {push_stderr}")
        return 1
    
    print(push_stdout)
    print("\n完了！変更がGitHubにプッシュされました。")
    return 0

if __name__ == "__main__":
    sys.exit(main())
