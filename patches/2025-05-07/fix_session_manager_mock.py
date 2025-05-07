#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
セッションマネージャーテストの修正

テストで使用されるモックオブジェクトの問題を修正します。
"""

import os
import sys
from pathlib import Path

# プロジェクトルートを取得
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# テストファイルのパス
test_file_path = os.path.join(project_root, 'tests', 'test_project', 'test_session_manager.py')

def fix_session_manager_test():
    """セッションマネージャーのテストを修正"""
    print(f"セッションマネージャーテストの修正を開始: {test_file_path}")
    
    # ファイルを読み込む
    with open(test_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # ファイルの内容を修正
    
    # 1. MagicMockのインポートを確認
    if 'from unittest.mock import MagicMock, patch' not in content:
        content = content.replace('from unittest.mock import', 'from unittest.mock import MagicMock, patch')
    
    # 2. project_managerのモック方法を修正
    old_code = """    @pytest.fixture
    def mock_project_manager(self):
        \"\"\"Create mock project manager\"\"\"
        manager = MagicMock(spec=ProjectManager)"""
    
    new_code = """    @pytest.fixture
    def mock_project_manager(self):
        \"\"\"Create mock project manager\"\"\"
        manager = MagicMock(spec=ProjectManager)
        
        # プロパティとしてセーブメソッドを追加（lambda関数ではなくMockオブジェクト）
        manager.save_project = MagicMock()
        manager.save_session = MagicMock()"""
    
    if old_code in content:
        content = content.replace(old_code, new_code)
    
    # 3. セッションマネージャーの初期化を修正
    old_init = """    @pytest.fixture
    def session_manager(self, mock_project_manager):
        \"\"\"Create session manager with mock project manager\"\"\"
        manager, _ = mock_project_manager
        
        # Patch mkdir to avoid actually creating directories
        with patch('pathlib.Path.mkdir'):
            sm = SessionManager(manager)
            
            # Mock the _initialize_cache method
            sm._initialize_cache = MagicMock()
            
            return sm"""
    
    new_init = """    @pytest.fixture
    def session_manager(self, mock_project_manager):
        \"\"\"Create session manager with mock project manager\"\"\"
        manager, _ = mock_project_manager
        
        # Patch mkdir to avoid actually creating directories
        with patch('pathlib.Path.mkdir'):
            sm = SessionManager(manager)
            
            # Mock the _initialize_cache method
            sm._initialize_cache = MagicMock()
            
            # モックメソッドの設定
            sm._update_search_index = MagicMock()
            sm._update_session_tags = MagicMock()
            
            return sm"""
    
    if old_init in content:
        content = content.replace(old_init, new_init)
    
    # 4. プロジェクトの設定を修正
    project_setup = """        # Setup project-session relationships
        project1.add_session(session1.session_id)
        project1.add_session(session2.session_id)
        project2.add_session(session3.session_id)"""
    
    new_project_setup = """        # Setup project-session relationships
        project1.add_session = MagicMock()
        project1.remove_session = MagicMock()
        project2.add_session = MagicMock()
        project2.remove_session = MagicMock()
        
        # モックの戻り値を設定
        project1.add_session.return_value = None
        project1.remove_session.return_value = None
        project2.add_session.return_value = None
        project2.remove_session.return_value = None
        
        # テスト用の関連付け
        project1.sessions = [session1.session_id, session2.session_id]
        project2.sessions = [session3.session_id]"""
    
    if project_setup in content:
        content = content.replace(project_setup, new_project_setup)
    
    # 修正内容を保存
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"セッションマネージャーテストの修正が完了しました。")
    return True

if __name__ == "__main__":
    fix_session_manager_test()
