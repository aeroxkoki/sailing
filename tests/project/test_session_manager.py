"""
sailing_data_processor.project.session_manager のテスト

セッションマネージャークラスの基本機能をテストする
"""

import unittest
from unittest.mock import MagicMock, patch
import os
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

from sailing_data_processor.project.session_manager import SessionManager
from sailing_data_processor.project.session_model import SessionModel, SessionResult


class TestSessionManagerBasic(unittest.TestCase):
    """セッションマネージャーの基本機能テスト"""

    def setUp(self):
        """各テスト前の準備"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        
        # プロジェクトマネージャーのモックを作成
        self.project_manager = MagicMock()
        self.project_manager.base_path = self.temp_dir
        
        # テスト用セッションを作成
        self.session1 = SessionModel(name="Session 1", project_id="project1", tags=["風向", "テスト"])
        self.session2 = SessionModel(name="Session 2", project_id="project1", tags=["戦略", "テスト"])
        self.session3 = SessionModel(name="Session 3", project_id="project2", tags=["風向", "戦略"])
        
        # 関連セッションを設定
        self.session1.add_related_session(self.session2.session_id, "related")
        self.session2.add_related_session(self.session1.session_id, "related")
        self.session3.add_related_session(self.session1.session_id, "parent")
        
        # モックの設定
        self.project_manager.get_all_sessions.return_value = [self.session1, self.session2, self.session3]
        
        # get_sessionメソッドのモック設定
        def get_session_mock(session_id):
            for session in [self.session1, self.session2, self.session3]:
                if session.session_id == session_id:
                    return session
            return None
            
        self.project_manager.get_session = get_session_mock
        
        # セッションマネージャーを作成
        self.session_manager = SessionManager(self.project_manager)

    def tearDown(self):
        """各テスト後のクリーンアップ"""
        shutil.rmtree(self.temp_dir)

    def test_get_all_sessions(self):
        """すべてのセッション取得をテスト"""
        sessions = self.session_manager.get_all_sessions()
        self.assertEqual(len(sessions), 3)
        self.assertEqual(sessions[0].name, "Session 1")
        self.assertEqual(sessions[1].name, "Session 2")
        self.assertEqual(sessions[2].name, "Session 3")
        
    def test_get_sessions_by_tag(self):
        """タグによるセッション検索をテスト"""
        # タグインデックスが正しく構築されているか確認
        self.assertIn("風向", self.session_manager._session_tags_cache)
        self.assertIn("テスト", self.session_manager._session_tags_cache)
        self.assertIn("戦略", self.session_manager._session_tags_cache)
        
        # 「風向」タグを持つセッションを検索
        sessions_ids = self.session_manager.get_sessions_by_tag("風向")
        self.assertEqual(len(sessions_ids), 2)
        self.assertIn(self.session1.session_id, sessions_ids)
        self.assertIn(self.session3.session_id, sessions_ids)
        
        # 「テスト」タグを持つセッションを検索
        sessions_ids = self.session_manager.get_sessions_by_tag("テスト")
        self.assertEqual(len(sessions_ids), 2)
        self.assertIn(self.session1.session_id, sessions_ids)
        self.assertIn(self.session2.session_id, sessions_ids)
        
        # 存在しないタグを検索
        sessions_ids = self.session_manager.get_sessions_by_tag("存在しないタグ")
        self.assertEqual(len(sessions_ids), 0)


if __name__ == "__main__":
    unittest.main()
