# -*- coding: utf-8 -*-
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
        # テスト前にカウンタをリセット
        self.project_manager.get_all_sessions.reset_mock()
        
        sessions = self.session_manager.get_all_sessions()
        
        # get_all_sessions が1回だけ呼ばれたことを確認
        self.project_manager.get_all_sessions.assert_called_once()
        
        # 返されたセッションを検証
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


class TestSessionManager(unittest.TestCase):
    """セッションマネージャーの拡張機能テスト"""

    def setUp(self):
        """テスト環境の準備"""
        # モックオブジェクトを作成
        self.project_manager = MagicMock()
        
        # テスト用のモックプロジェクトを作成
        self.mock_project1 = MagicMock()
        self.mock_project1.project_id = "project1"
        self.mock_project1.add_session = MagicMock()
        self.mock_project1.remove_session = MagicMock()
        
        self.mock_project2 = MagicMock()
        self.mock_project2.project_id = "project2"
        self.mock_project2.add_session = MagicMock()
        self.mock_project2.remove_session = MagicMock()
        
        # モックセッションを作成
        self.mock_session = MagicMock()
        self.mock_session.session_id = "test_session"
        self.mock_session.metadata = {}
        self.mock_session.tags = ["test", "セーリング"]
        
        # get_project メソッドのモック
        def get_project_mock(project_id):
            if project_id == "project1":
                return self.mock_project1
            elif project_id == "project2":
                return self.mock_project2
            return None
        
        self.project_manager.get_project = MagicMock(side_effect=get_project_mock)
        
        # get_session メソッドのモック
        self.project_manager.get_session = MagicMock(return_value=self.mock_session)
        
        # get_all_sessions メソッドのモック
        self.project_manager.get_all_sessions = MagicMock(return_value=[self.mock_session])
        
        # save_project と save_session メソッドのモック
        self.project_manager.save_project = MagicMock()
        self.project_manager.save_session = MagicMock()

        # インスタンス作成
        with patch('pathlib.Path.mkdir'):
            self.session_manager = SessionManager(self.project_manager)
    
    def test_init(self):
        """初期化のテスト"""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            session_manager = SessionManager(self.project_manager)
            # mkdir が呼ばれたことを確認
            mock_mkdir.assert_called()
    
    def test_add_session_to_project(self):
        """セッションをプロジェクトに追加するテスト"""
        result = self.session_manager.add_session_to_project("project1", "test_session")
        
        # 結果を検証
        self.assertTrue(result)
        # add_session メソッドが正しく呼ばれたことを確認
        self.mock_project1.add_session.assert_called_with("test_session")
        # save_project メソッドが呼ばれたことを確認
        self.project_manager.save_project.assert_called_with(self.mock_project1)
    
    def test_add_session_to_nonexistent_project(self):
        """存在しないプロジェクトへの追加テスト"""
        result = self.session_manager.add_session_to_project("nonexistent", "test_session")
        
        # 結果を検証
        self.assertFalse(result)
        # save_project が呼ばれないことを確認
        self.project_manager.save_project.assert_not_called()
    
    def test_remove_session_from_project(self):
        """プロジェクトからセッションを削除するテスト"""
        result = self.session_manager.remove_session_from_project("project1", "test_session")
        
        # 結果を検証
        self.assertTrue(result)
        # remove_session メソッドが正しく呼ばれたことを確認
        self.mock_project1.remove_session.assert_called_with("test_session")
        # save_project メソッドが呼ばれたことを確認
        self.project_manager.save_project.assert_called_with(self.mock_project1)
    
    def test_move_session(self):
        """セッションを移動するテスト"""
        result = self.session_manager.move_session("test_session", "project1", "project2")
        
        # 結果を検証
        self.assertTrue(result)
        # 適切なメソッドが呼ばれたことを確認
        self.mock_project1.remove_session.assert_called_with("test_session")
        self.mock_project2.add_session.assert_called_with("test_session")
        # プロジェクトの保存が行われたことを確認
        self.assertEqual(self.project_manager.save_project.call_count, 2)
    
    def test_update_session_metadata(self):
        """セッションメタデータを更新するテスト"""
        # 更新するメタデータ
        metadata = {"location": "Tokyo Bay", "weather": "Sunny"}
        
        # パッチを適用してメソッド呼び出しを監視
        with patch.object(self.session_manager, '_update_search_index') as mock_update_index:
            result = self.session_manager.update_session_metadata("test_session", metadata)
            
            # 結果を検証
            self.assertTrue(result)
            # メタデータが正しく更新されたか確認
            self.assertEqual(self.mock_session.metadata["location"], "Tokyo Bay")
            self.assertEqual(self.mock_session.metadata["weather"], "Sunny")
            # 検索インデックスが更新されたか確認
            mock_update_index.assert_called_with(self.mock_session)
            # セッションが保存されたか確認
            self.project_manager.save_session.assert_called_with(self.mock_session)
    
    def test_update_session_status(self):
        """セッションステータスを更新するテスト"""
        # ステータス更新メソッドを持つセッションを作成
        self.mock_session.update_status = MagicMock()
        
        # パッチを適用してメソッド呼び出しを監視
        with patch.object(self.session_manager, '_update_search_index') as mock_update_index:
            result = self.session_manager.update_session_status("test_session", "completed")
            
            # 結果を検証
            self.assertTrue(result)
            # ステータスが正しく更新されたか確認
            self.mock_session.update_status.assert_called_with("completed")
            # 検索インデックスが更新されたか確認
            mock_update_index.assert_called_with(self.mock_session)
            # セッションが保存されたか確認
            self.project_manager.save_session.assert_called_with(self.mock_session)
    
    def test_update_session_category(self):
        """セッションカテゴリを更新するテスト"""
        # カテゴリ更新メソッドを持つセッションを作成
        self.mock_session.update_category = MagicMock()
        
        # パッチを適用してメソッド呼び出しを監視
        with patch.object(self.session_manager, '_update_search_index') as mock_update_index:
            result = self.session_manager.update_session_category("test_session", "race")
            
            # 結果を検証
            self.assertTrue(result)
            # カテゴリが正しく更新されたか確認
            self.mock_session.update_category.assert_called_with("race")
            # 検索インデックスが更新されたか確認
            mock_update_index.assert_called_with(self.mock_session)
            # セッションが保存されたか確認
            self.project_manager.save_session.assert_called_with(self.mock_session)
    
    def test_update_session_tags(self):
        """セッションタグを更新するテスト"""
        # 新しいタグのリスト
        new_tags = ["competition", "offshore"]
        
        # 更新前のタグをコピー
        old_tags = self.mock_session.tags.copy()
        
        # パッチを適用してメソッド呼び出しを監視
        with patch.object(self.session_manager, '_update_session_tags') as mock_update_tags, \
             patch.object(self.session_manager, '_update_search_index') as mock_update_index:
            
            result = self.session_manager.update_session_tags("test_session", new_tags)
            
            # 結果を検証
            self.assertTrue(result)
            # タグが正しく更新されたか確認
            self.assertEqual(self.mock_session.tags, new_tags)
            # タグキャッシュが更新されたか確認
            mock_update_tags.assert_called_with("test_session", old_tags, new_tags)
            # 検索インデックスが更新されたか確認
            mock_update_index.assert_called_with(self.mock_session)
            # セッションが保存されたか確認
            self.project_manager.save_session.assert_called_with(self.mock_session)


if __name__ == "__main__":
    unittest.main()
