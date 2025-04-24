# -*- coding: utf-8 -*-
"""
session_manager.py の基本機能のテスト

セッションマネージャーの基本的な機能をテストする単純な例
"""

import unittest
from unittest.mock import MagicMock
import tempfile
import shutil
from pathlib import Path

from sailing_data_processor.project.session_manager import SessionManager
from sailing_data_processor.project.session_model import SessionModel


class TestSessionManagerSimple(unittest.TestCase):
    """セッションマネージャーの基本機能テスト"""

    def setUp(self):
        """各テスト前の準備"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        
        # プロジェクトマネージャーのモックを作成
        self.project_manager = MagicMock()
        self.project_manager.base_path = self.temp_dir
        
        # テスト用セッションを作成
        self.session1 = SessionModel(name="Session 1", project_id="project1")
        self.session2 = SessionModel(name="Session 2", project_id="project1")
        
        # モックの設定
        self.project_manager.get_all_sessions.return_value = [self.session1, self.session2]
        
        # セッションマネージャーを作成
        self.session_manager = SessionManager(self.project_manager)

    def tearDown(self):
        """各テスト後のクリーンアップ"""
        shutil.rmtree(self.temp_dir)

    def test_get_all_sessions(self):
        """すべてのセッション取得機能のテスト"""
        sessions = self.session_manager.get_all_sessions()
        self.assertEqual(len(sessions), 2)
        self.assertEqual(sessions[0].name, "Session 1")
        self.assertEqual(sessions[1].name, "Session 2")


if __name__ == "__main__":
    unittest.main()
