# -*- coding: utf-8 -*-
"""
sailing_data_processor.project.session_model のテスト

セッションモデルと結果モデルの機能をテストする
"""

import unittest
from datetime import datetime, timedelta
import json
import os
import uuid
from pathlib import Path

from sailing_data_processor.project.session_model import SessionModel, SessionResult


class TestSessionModel(unittest.TestCase):
    """セッションモデルのテストケース"""

    def test_session_model_creation(self):
        """セッションモデルの基本的な作成をテスト"""
        session = SessionModel(
            name="テストセッション",
            project_id="project123",
            description="テスト用のセッション",
            category="analysis",
            tags=["風向分析", "テスト"],
            status="active",
            rating=3
        )
        
        # 基本属性の検証
        self.assertEqual(session.name, "テストセッション")
        self.assertEqual(session.project_id, "project123")
        self.assertEqual(session.description, "テスト用のセッション")
        self.assertEqual(session.category, "analysis")
        self.assertEqual(session.tags, ["風向分析", "テスト"])
        self.assertEqual(session.status, "active")
        self.assertEqual(session.rating, 3)
        
        # 自動生成された属性の検証
        self.assertIsNotNone(session.session_id)
        self.assertIsNotNone(session.created_at)
        self.assertEqual(session.created_at, session.updated_at)
        self.assertEqual(session.results, [])

    def test_tag_management(self):
        """タグ管理機能のテスト"""
        session = SessionModel(
            name="タグテストセッション",
            project_id="project123",
            tags=["初期タグ"]
        )
        
        # 初期状態の確認
        self.assertEqual(session.tags, ["初期タグ"])
        
        # タグの追加
        session.add_tag("新しいタグ")
        self.assertEqual(session.tags, ["初期タグ", "新しいタグ"])
        
        # 重複するタグの追加（無視されるはず）
        session.add_tag("新しいタグ")
        self.assertEqual(session.tags, ["初期タグ", "新しいタグ"])
        
        # タグの削除
        session.remove_tag("初期タグ")
        self.assertEqual(session.tags, ["新しいタグ"])
        
        # 存在しないタグの削除（エラーにならないことを確認）
        session.remove_tag("存在しないタグ")
        self.assertEqual(session.tags, ["新しいタグ"])
        
        # 更新日時の変更を確認
        self.assertNotEqual(session.created_at, session.updated_at)

    def test_related_sessions_management(self):
        """関連セッション管理機能のテスト"""
        session = SessionModel(
            name="関連セッションテスト",
            project_id="project123"
        )
        
        # 初期状態の確認
        self.assertEqual(session.related_sessions, {
            "parent": [], "child": [], "previous": [], "next": [], "related": []
        })
        
        # 関連セッションの追加
        session.add_related_session("session1", "parent")
        self.assertEqual(session.related_sessions["parent"], ["session1"])
        
        # 別のタイプの関連セッションの追加
        session.add_related_session("session2", "child")
        self.assertEqual(session.related_sessions["child"], ["session2"])
        
        # デフォルトのタイプ（related）を使用した追加
        session.add_related_session("session3")
        self.assertEqual(session.related_sessions["related"], ["session3"])
        
        # 重複する関連セッションの追加（無視されるはず）
        session.add_related_session("session1", "parent")
        self.assertEqual(session.related_sessions["parent"], ["session1"])
        
        # 関連セッションの削除
        session.remove_related_session("session1", "parent")
        self.assertEqual(session.related_sessions["parent"], [])
        
        # 存在しない関連セッションの削除（エラーにならないことを確認）
        session.remove_related_session("session99", "parent")
        self.assertEqual(session.related_sessions["parent"], [])
        
        # 存在しない関連タイプの削除（エラーにならないことを確認）
        session.remove_related_session("session3", "unknown_type")
        self.assertEqual(session.related_sessions["related"], ["session3"])

    def test_serialization(self):
        """シリアル化と逆シリアル化のテスト"""
        original_session = SessionModel(
            name="シリアル化テスト",
            project_id="project123",
            description="シリアル化のテスト用セッション",
            category="analysis",
            tags=["シリアル化", "テスト"],
            status="active",
            rating=4,
            related_sessions={"parent": ["parent1"], "child": ["child1", "child2"]},
            event_date=datetime.now(),
            location="テスト位置",
            importance="high",
            completion_percentage=75
        )
        
        # 結果の追加
        original_session.add_result("result1")
        original_session.add_result("result2")
        
        # 辞書に変換
        session_dict = original_session.to_dict()
        
        # 辞書からインスタンスを再作成
        recreated_session = SessionModel.from_dict(session_dict)
        
        # 基本属性の検証
        self.assertEqual(recreated_session.name, original_session.name)
        self.assertEqual(recreated_session.project_id, original_session.project_id)
        self.assertEqual(recreated_session.description, original_session.description)
        self.assertEqual(recreated_session.category, original_session.category)
        self.assertEqual(recreated_session.tags, original_session.tags)
        self.assertEqual(recreated_session.status, original_session.status)
        self.assertEqual(recreated_session.rating, original_session.rating)
        self.assertEqual(recreated_session.session_id, original_session.session_id)
        self.assertEqual(recreated_session.created_at, original_session.created_at)
        self.assertEqual(recreated_session.updated_at, original_session.updated_at)
        self.assertEqual(recreated_session.results, original_session.results)
        self.assertEqual(recreated_session.location, original_session.location)
        self.assertEqual(recreated_session.importance, original_session.importance)
        self.assertEqual(recreated_session.completion_percentage, original_session.completion_percentage)
        
        # 関連セッションの検証
        for relation_type in original_session.related_sessions:
            self.assertEqual(
                recreated_session.related_sessions[relation_type], 
                original_session.related_sessions[relation_type]
            )

    def test_session_copy(self):
        """セッションコピー機能のテスト"""
        original_session = SessionModel(
            name="コピー元セッション",
            project_id="project123",
            description="コピーのテスト用セッション",
            tags=["コピー", "テスト"],
            status="active",
            rating=5
        )
        
        # セッションのコピーを作成
        copied_session = original_session.create_copy()
        
        # 名前の検証（「Copy of 」が付加されるはず）
        self.assertEqual(copied_session.name, "Copy of コピー元セッション")
        
        # その他の属性の検証
        self.assertEqual(copied_session.project_id, original_session.project_id)
        self.assertEqual(copied_session.description, original_session.description)
        self.assertEqual(copied_session.category, original_session.category)
        self.assertEqual(copied_session.tags, original_session.tags)
        self.assertEqual(copied_session.status, original_session.status)
        self.assertEqual(copied_session.rating, original_session.rating)
        
        # IDは異なるはず
        self.assertNotEqual(copied_session.session_id, original_session.session_id)
        
        # カスタム名でコピーを作成
        custom_copied_session = original_session.create_copy("カスタム名のコピー")
        self.assertEqual(custom_copied_session.name, "カスタム名のコピー")

    def test_update_methods(self):
        """更新メソッドのテスト"""
        session = SessionModel(
            name="更新テストセッション",
            project_id="project123"
        )
        original_updated_at = session.updated_at
        
        # 少し待って更新が確実に時刻の違いを生み出すようにする
        import time
        time.sleep(0.01)
        
        # 各種更新メソッドのテスト
        session.update_rating(4)
        session.update_status("completed")
        session.update_metadata("key1", "value1")
        session.update_event_date(datetime.now())
        session.update_location("新しい位置")
        session.update_purpose("新しい目的")
        session.update_importance("critical")
        session.update_completion_percentage(80)
        
        # 更新後の値を検証
        self.assertEqual(session.rating, 4)
        self.assertEqual(session.status, "completed")
        self.assertEqual(session.metadata["key1"], "value1")
        self.assertIsNotNone(session.event_date)
        self.assertEqual(session.location, "新しい位置")
        self.assertEqual(session.purpose, "新しい目的")
        self.assertEqual(session.importance, "critical")
        self.assertEqual(session.completion_percentage, 80)
        
        # 更新日時が変更されたことを確認
        self.assertNotEqual(session.updated_at, original_updated_at)


class TestSessionResult(unittest.TestCase):
    """セッション結果モデルのテストケース"""

    def test_result_creation(self):
        """結果モデルの基本的な作成をテスト"""
        result = SessionResult(
            result_id="result123",
            session_id="session123",
            result_type="wind_estimation",
            data={"wind_direction": 270, "wind_speed": 12},
            result_category="analysis",
            importance="normal",
            version=1,
            is_current=True
        )
        
        # 基本属性の検証
        self.assertEqual(result.result_id, "result123")
        self.assertEqual(result.session_id, "session123")
        self.assertEqual(result.result_type, "wind_estimation")
        self.assertEqual(result.data, {"wind_direction": 270, "wind_speed": 12})
        self.assertEqual(result.result_category, "analysis")
        self.assertEqual(result.importance, "normal")
        self.assertEqual(result.version, 1)
        self.assertEqual(result.is_current, True)
        
        # 自動生成された属性の検証
        self.assertIsNotNone(result.created_at)
        self.assertEqual(result.tags, [])
        self.assertIsNone(result.parent_version)

    def test_result_serialization(self):
        """結果のシリアル化と逆シリアル化のテスト"""
        original_result = SessionResult(
            result_id="result123",
            session_id="session123",
            result_type="wind_estimation",
            data={"wind_direction": 270, "wind_speed": 12},
            result_category="analysis",
            importance="high",
            metadata={"accuracy": "high", "confidence": 0.85},
            version=2,
            is_current=True,
            tags=["風向", "推定"],
            parent_version=1
        )
        
        # 辞書に変換
        result_dict = original_result.to_dict()
        
        # 辞書からインスタンスを再作成
        recreated_result = SessionResult.from_dict(result_dict)
        
        # 基本属性の検証
        self.assertEqual(recreated_result.result_id, original_result.result_id)
        self.assertEqual(recreated_result.session_id, original_result.session_id)
        self.assertEqual(recreated_result.result_type, original_result.result_type)
        self.assertEqual(recreated_result.data, original_result.data)
        self.assertEqual(recreated_result.result_category, original_result.result_category)
        self.assertEqual(recreated_result.importance, original_result.importance)
        self.assertEqual(recreated_result.metadata, original_result.metadata)
        self.assertEqual(recreated_result.version, original_result.version)
        self.assertEqual(recreated_result.is_current, original_result.is_current)
        self.assertEqual(recreated_result.tags, original_result.tags)
        self.assertEqual(recreated_result.parent_version, original_result.parent_version)

    def test_versioning(self):
        """バージョン管理機能のテスト"""
        # 初期バージョンの作成
        original_result = SessionResult(
            result_id="result123",
            session_id="session123",
            result_type="wind_estimation",
            data={"wind_direction": 270, "wind_speed": 12},
            version=1,
            is_current=True
        )
        
        # 新しいバージョンの作成
        new_data = {"wind_direction": 280, "wind_speed": 14}
        new_version = original_result.create_new_version(new_data)
        
        # 新しいバージョンの検証
        self.assertEqual(new_version.result_id, original_result.result_id)
        self.assertEqual(new_version.session_id, original_result.session_id)
        self.assertEqual(new_version.result_type, original_result.result_type)
        self.assertEqual(new_version.data, new_data)
        self.assertEqual(new_version.version, 2)
        self.assertEqual(new_version.is_current, True)
        self.assertEqual(new_version.parent_version, 1)
        
        # 元のバージョンが現在のバージョンではなくなったことを確認
        self.assertEqual(original_result.is_current, False)
        
        # バージョン履歴がメタデータに記録されていることを確認
        self.assertIn("version_history", new_version.metadata)
        self.assertEqual(len(new_version.metadata["version_history"]), 1)
        self.assertEqual(new_version.metadata["version_history"][0]["version"], 1)

    def test_tag_management(self):
        """結果のタグ管理機能のテスト"""
        result = SessionResult(
            result_id="result123",
            session_id="session123",
            result_type="wind_estimation",
            data={"wind_direction": 270, "wind_speed": 12},
            tags=["初期タグ"]
        )
        
        # 初期状態の確認
        self.assertEqual(result.tags, ["初期タグ"])
        
        # タグの追加
        result.add_tag("新しいタグ")
        self.assertEqual(result.tags, ["初期タグ", "新しいタグ"])
        
        # 重複するタグの追加（無視されるはず）
        result.add_tag("新しいタグ")
        self.assertEqual(result.tags, ["初期タグ", "新しいタグ"])
        
        # タグの削除
        result.remove_tag("初期タグ")
        self.assertEqual(result.tags, ["新しいタグ"])
        
        # 存在しないタグの削除（エラーにならないことを確認）
        result.remove_tag("存在しないタグ")
        self.assertEqual(result.tags, ["新しいタグ"])

    def test_update_methods(self):
        """結果の更新メソッドのテスト"""
        result = SessionResult(
            result_id="result123",
            session_id="session123",
            result_type="wind_estimation",
            data={"wind_direction": 270, "wind_speed": 12}
        )
        
        # 各種更新メソッドのテスト
        result.update_metadata({"quality": "high", "analyst": "user1"})
        result.mark_as_current(False)
        result.update_importance("high")
        result.update_category("validation")
        
        # 更新後の値を検証
        self.assertEqual(result.metadata["quality"], "high")
        self.assertEqual(result.metadata["analyst"], "user1")
        self.assertEqual(result.is_current, False)
        self.assertEqual(result.importance, "high")
        self.assertEqual(result.result_category, "validation")


if __name__ == "__main__":
    unittest.main()
