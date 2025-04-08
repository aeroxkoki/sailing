"""
テストモジュール: sailing_data_processor.project.project_model
テスト対象: Projectクラス, Sessionクラス, AnalysisResultクラス
"""

import os
import json
import pytest
from datetime import datetime
from pathlib import Path
import uuid

from sailing_data_processor.project.project_model import Project, Session, AnalysisResult


class TestProject:
    """
    Projectクラスのテスト
    """
    
    def test_project_initialization(self):
        """プロジェクトの初期化をテスト"""
        # 基本的な初期化
        project = Project(name="テストプロジェクト")
        
        assert project.name == "テストプロジェクト"
        assert project.description == ""
        assert isinstance(project.project_id, str)
        assert project.parent_id is None
        assert project.category == "general"
        assert project.color == "#4A90E2"
        assert project.icon == "folder"
        assert isinstance(project.created_at, str)
        assert project.updated_at == project.created_at
        assert project.sessions == []
        assert project.sub_projects == []
        assert project.favorites is False
        assert "default_view" in project.view_settings
        
        # パラメータを指定した初期化
        project = Project(
            name="カスタムプロジェクト",
            description="説明文",
            tags=["tag1", "tag2"],
            metadata={"key": "value"},
            project_id="custom-id",
            parent_id="parent-id",
            category="racing",
            color="#FF0000",
            icon="star"
        )
        
        assert project.name == "カスタムプロジェクト"
        assert project.description == "説明文"
        assert project.tags == ["tag1", "tag2"]
        assert project.metadata["key"] == "value"
        assert project.project_id == "custom-id"
        assert project.parent_id == "parent-id"
        assert project.category == "racing"
        assert project.color == "#FF0000"
        assert project.icon == "star"
    
    def test_project_methods(self):
        """プロジェクトのメソッドをテスト"""
        project = Project(name="テストプロジェクト")
        
        # セッション追加・削除
        project.add_session("session-1")
        assert "session-1" in project.sessions
        
        project.add_session("session-2")
        assert len(project.sessions) == 2
        
        # 重複を追加しない
        project.add_session("session-1")
        assert len(project.sessions) == 2
        
        result = project.remove_session("session-1")
        assert result is True
        assert "session-1" not in project.sessions
        
        # 存在しないセッション削除
        result = project.remove_session("non-existent")
        assert result is False
        
        # サブプロジェクト追加・削除
        project.add_sub_project("sub-1")
        assert "sub-1" in project.sub_projects
        
        result = project.remove_sub_project("sub-1")
        assert result is True
        assert "sub-1" not in project.sub_projects
        
        # メタデータ更新
        project.update_metadata("test_key", "test_value")
        assert project.metadata["test_key"] == "test_value"
        
        # タグ追加・削除
        project.add_tag("tag1")
        assert "tag1" in project.tags
        
        result = project.remove_tag("tag1")
        assert result is True
        assert "tag1" not in project.tags
        
        # お気に入り設定
        project.set_favorites(True)
        assert project.favorites is True
        
        # 表示設定更新
        project.update_view_settings({"sort_by": "date"})
        assert project.view_settings["sort_by"] == "date"
        
        # カラー設定
        project.set_color("#00FF00")
        assert project.color == "#00FF00"
        
        # アイコン設定
        project.set_icon("folder-open")
        assert project.icon == "folder-open"
        
        # カテゴリ設定
        project.set_category("practice")
        assert project.category == "practice"
    
    def test_project_to_dict(self):
        """プロジェクトのシリアライズをテスト"""
        project = Project(
            name="テストプロジェクト",
            description="説明文",
            tags=["tag1", "tag2"],
            metadata={"key": "value"}
        )
        
        project.add_session("session-1")
        project.add_sub_project("sub-1")
        
        data = project.to_dict()
        
        assert data["name"] == "テストプロジェクト"
        assert data["description"] == "説明文"
        assert data["tags"] == ["tag1", "tag2"]
        assert data["metadata"]["key"] == "value"
        assert "project_id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "sessions" in data
        assert "sub_projects" in data
        assert "favorites" in data
        assert "view_settings" in data
    
    def test_project_from_dict(self):
        """プロジェクトのデシリアライズをテスト"""
        data = {
            "name": "復元プロジェクト",
            "description": "説明文",
            "tags": ["tag1", "tag2"],
            "metadata": {"key": "value"},
            "project_id": "test-id",
            "parent_id": "parent-id",
            "category": "racing",
            "color": "#FF0000",
            "icon": "star",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-02T00:00:00",
            "sessions": ["session-1", "session-2"],
            "sub_projects": ["sub-1"],
            "favorites": True,
            "view_settings": {
                "default_view": "grid",
                "sort_by": "date",
                "sort_order": "desc",
                "view_mode": "detailed"
            }
        }
        
        project = Project.from_dict(data)
        
        assert project.name == "復元プロジェクト"
        assert project.description == "説明文"
        assert project.tags == ["tag1", "tag2"]
        assert project.metadata["key"] == "value"
        assert project.project_id == "test-id"
        assert project.parent_id == "parent-id"
        assert project.category == "racing"
        assert project.color == "#FF0000"
        assert project.icon == "star"
        assert project.created_at == "2025-01-01T00:00:00"
        assert project.updated_at == "2025-01-02T00:00:00"
        assert project.sessions == ["session-1", "session-2"]
        assert project.sub_projects == ["sub-1"]
        assert project.favorites is True
        assert project.view_settings["default_view"] == "grid"
        assert project.view_settings["view_mode"] == "detailed"


class TestSession:
    """
    Sessionクラスのテスト
    """
    
    def test_session_initialization(self):
        """セッションの初期化をテスト"""
        # 基本的な初期化
        session = Session(name="テストセッション")
        
        assert session.name == "テストセッション"
        assert session.description == ""
        assert isinstance(session.session_id, str)
        assert session.category == "general"
        assert session.color == "#32A852"
        assert session.icon == "map"
        assert session.source_file is None
        assert session.source_type is None
        assert session.status == "new"
        assert isinstance(session.created_at, str)
        assert session.updated_at == session.created_at
        assert session.data_file is None
        assert session.state_file is None
        assert session.analysis_results == []
        assert session.favorites is False
        assert session.validation_score == 0.0
        assert "completeness" in session.data_quality
        
        # パラメータを指定した初期化
        session = Session(
            name="カスタムセッション",
            description="説明文",
            tags=["tag1", "tag2"],
            metadata={"key": "value"},
            session_id="custom-id",
            category="race",
            color="#FF0000",
            icon="flag",
            source_file="/path/to/file.csv",
            source_type="csv",
            status="validated"
        )
        
        assert session.name == "カスタムセッション"
        assert session.description == "説明文"
        assert session.tags == ["tag1", "tag2"]
        assert session.metadata["key"] == "value"
        assert session.session_id == "custom-id"
        assert session.category == "race"
        assert session.color == "#FF0000"
        assert session.icon == "flag"
        assert session.source_file == "/path/to/file.csv"
        assert session.source_type == "csv"
        assert session.status == "validated"
    
    def test_session_methods(self):
        """セッションのメソッドをテスト"""
        session = Session(name="テストセッション")
        
        # データファイル設定
        session.set_data("/path/to/data.json")
        assert session.data_file == "/path/to/data.json"
        
        # 状態ファイル設定
        session.set_state("/path/to/state.json")
        assert session.state_file == "/path/to/state.json"
        
        # 分析結果追加・削除
        session.add_analysis_result("result-1")
        assert "result-1" in session.analysis_results
        
        session.add_analysis_result("result-2")
        assert len(session.analysis_results) == 2
        
        # 重複を追加しない
        session.add_analysis_result("result-1")
        assert len(session.analysis_results) == 2
        
        result = session.remove_analysis_result("result-1")
        assert result is True
        assert "result-1" not in session.analysis_results
        
        # 存在しない結果の削除
        result = session.remove_analysis_result("non-existent")
        assert result is False
        
        # メタデータ更新
        session.update_metadata("test_key", "test_value")
        assert session.metadata["test_key"] == "test_value"
        
        # タグ追加・削除
        session.add_tag("tag1")
        assert "tag1" in session.tags
        
        result = session.remove_tag("tag1")
        assert result is True
        assert "tag1" not in session.tags
        
        # カラー設定
        session.set_color("#00FF00")
        assert session.color == "#00FF00"
        
        # アイコン設定
        session.set_icon("compass")
        assert session.icon == "compass"
        
        # ステータス設定
        session.set_status("analyzed")
        assert session.status == "analyzed"
        
        # お気に入り設定
        session.set_favorites(True)
        assert session.favorites is True
        
        # 検証スコア更新
        session.update_validation_score(0.85)
        assert session.validation_score == 0.85
        
        # 範囲外の値は制限される
        session.update_validation_score(1.5)
        assert session.validation_score == 1.0
        
        session.update_validation_score(-0.5)
        assert session.validation_score == 0.0
        
        # データ品質更新
        session.update_data_quality({
            "completeness": 0.95,
            "error_count": 5
        })
        assert session.data_quality["completeness"] == 0.95
        assert session.data_quality["error_count"] == 5
    
    def test_session_to_dict(self):
        """セッションのシリアライズをテスト"""
        session = Session(
            name="テストセッション",
            description="説明文",
            tags=["tag1", "tag2"],
            metadata={"key": "value"},
            category="race",
            status="validated"
        )
        
        session.add_analysis_result("result-1")
        
        data = session.to_dict()
        
        assert data["name"] == "テストセッション"
        assert data["description"] == "説明文"
        assert data["tags"] == ["tag1", "tag2"]
        assert data["metadata"]["key"] == "value"
        assert data["category"] == "race"
        assert data["status"] == "validated"
        assert "session_id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "analysis_results" in data
        assert "validation_score" in data
        assert "data_quality" in data
    
    def test_session_from_dict(self):
        """セッションのデシリアライズをテスト"""
        data = {
            "name": "復元セッション",
            "description": "説明文",
            "tags": ["tag1", "tag2"],
            "metadata": {"key": "value"},
            "session_id": "test-id",
            "category": "race",
            "color": "#FF0000",
            "icon": "flag",
            "source_file": "/path/to/file.csv",
            "source_type": "csv",
            "status": "analyzed",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-02T00:00:00",
            "data_file": "/path/to/data.json",
            "state_file": "/path/to/state.json",
            "analysis_results": ["result-1", "result-2"],
            "favorites": True,
            "validation_score": 0.95,
            "data_quality": {
                "completeness": 0.95,
                "consistency": 0.90,
                "accuracy": 0.88,
                "error_count": 5,
                "warning_count": 3,
                "fixed_issues": 2
            }
        }
        
        session = Session.from_dict(data)
        
        assert session.name == "復元セッション"
        assert session.description == "説明文"
        assert session.tags == ["tag1", "tag2"]
        assert session.metadata["key"] == "value"
        assert session.session_id == "test-id"
        assert session.category == "race"
        assert session.color == "#FF0000"
        assert session.icon == "flag"
        assert session.source_file == "/path/to/file.csv"
        assert session.source_type == "csv"
        assert session.status == "analyzed"
        assert session.created_at == "2025-01-01T00:00:00"
        assert session.updated_at == "2025-01-02T00:00:00"
        assert session.data_file == "/path/to/data.json"
        assert session.state_file == "/path/to/state.json"
        assert session.analysis_results == ["result-1", "result-2"]
        assert session.favorites is True
        assert session.validation_score == 0.95
        assert session.data_quality["completeness"] == 0.95
        assert session.data_quality["fixed_issues"] == 2


class TestAnalysisResult:
    """
    AnalysisResultクラスのテスト
    """
    
    def test_analysis_result_initialization(self):
        """分析結果の初期化をテスト"""
        # 基本的な初期化
        data = {"values": [1, 2, 3], "average": 2.0}
        result = AnalysisResult(
            name="テスト結果",
            result_type="test_analysis",
            data=data
        )
        
        assert result.name == "テスト結果"
        assert result.description == ""
        assert result.result_type == "test_analysis"
        assert result.data == data
        assert isinstance(result.result_id, str)
        assert result.tags == []
        assert result.version == 1
        assert result.quality_score == 0.0
        assert "chart_type" in result.visualization_settings
        assert isinstance(result.created_at, str)
        assert result.updated_at == result.created_at
        assert result.summary == ""
        assert result.highlights == []
        
        # パラメータを指定した初期化
        result = AnalysisResult(
            name="カスタム結果",
            result_type="custom_analysis",
            data=data,
            description="説明文",
            metadata={"key": "value"},
            result_id="custom-id",
            tags=["tag1", "tag2"],
            version=2,
            quality_score=0.85,
            visualization_settings={"chart_type": "bar"}
        )
        
        assert result.name == "カスタム結果"
        assert result.description == "説明文"
        assert result.result_type == "custom_analysis"
        assert result.data == data
        assert result.metadata["key"] == "value"
        assert result.result_id == "custom-id"
        assert result.tags == ["tag1", "tag2"]
        assert result.version == 2
        assert result.quality_score == 0.85
        assert result.visualization_settings["chart_type"] == "bar"
    
    def test_analysis_result_methods(self):
        """分析結果のメソッドをテスト"""
        data = {"values": [1, 2, 3], "average": 2.0}
        result = AnalysisResult(
            name="テスト結果",
            result_type="test_analysis",
            data=data
        )
        
        # データ更新
        new_data = {"values": [1, 2, 3, 4], "average": 2.5}
        result.update_data(new_data)
        assert result.data == new_data
        assert result.version == 2  # バージョンが上がる
        
        # メタデータ更新
        result.update_metadata("test_key", "test_value")
        assert result.metadata["test_key"] == "test_value"
        
        # タグ追加・削除
        result.add_tag("tag1")
        assert "tag1" in result.tags
        
        result.add_tag("tag2")
        assert len(result.tags) == 2
        
        # 重複を追加しない
        result.add_tag("tag1")
        assert len(result.tags) == 2
        
        res = result.remove_tag("tag1")
        assert res is True
        assert "tag1" not in result.tags
        
        # 存在しないタグの削除
        res = result.remove_tag("non-existent")
        assert res is False
        
        # 可視化設定更新
        result.update_visualization_settings({
            "chart_type": "line",
            "color_scheme": "reds"
        })
        assert result.visualization_settings["chart_type"] == "line"
        assert result.visualization_settings["color_scheme"] == "reds"
        
        # 要約設定
        result.set_summary("これはテスト結果の要約です")
        assert result.summary == "これはテスト結果の要約です"
        
        # ハイライト追加
        result.add_highlight("重要なポイント1")
        assert "重要なポイント1" in result.highlights
        
        result.add_highlight("重要なポイント2")
        assert len(result.highlights) == 2
        
        # 品質スコア更新
        result.update_quality_score(0.75)
        assert result.quality_score == 0.75
        
        # 範囲外の値は制限される
        result.update_quality_score(1.5)
        assert result.quality_score == 1.0
        
        result.update_quality_score(-0.5)
        assert result.quality_score == 0.0
    
    def test_analysis_result_to_dict(self):
        """分析結果のシリアライズをテスト"""
        data = {"values": [1, 2, 3], "average": 2.0}
        result = AnalysisResult(
            name="テスト結果",
            result_type="test_analysis",
            data=data,
            description="説明文",
            tags=["tag1", "tag2"]
        )
        
        result.set_summary("要約")
        result.add_highlight("ハイライト1")
        
        data_dict = result.to_dict()
        
        assert data_dict["name"] == "テスト結果"
        assert data_dict["description"] == "説明文"
        assert data_dict["result_type"] == "test_analysis"
        assert data_dict["data"] == data
        assert data_dict["tags"] == ["tag1", "tag2"]
        assert data_dict["version"] == 1
        assert "visualization_settings" in data_dict
        assert data_dict["summary"] == "要約"
        assert data_dict["highlights"] == ["ハイライト1"]
        assert "result_id" in data_dict
        assert "created_at" in data_dict
        assert "updated_at" in data_dict
    
    def test_analysis_result_from_dict(self):
        """分析結果のデシリアライズをテスト"""
        data = {
            "name": "復元結果",
            "description": "説明文",
            "result_type": "custom_analysis",
            "data": {"values": [1, 2, 3], "average": 2.0},
            "metadata": {"key": "value"},
            "result_id": "test-id",
            "tags": ["tag1", "tag2"],
            "version": 3,
            "quality_score": 0.85,
            "visualization_settings": {
                "chart_type": "bar",
                "color_scheme": "greens",
                "show_grid": False
            },
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-02T00:00:00",
            "summary": "要約テキスト",
            "highlights": ["ハイライト1", "ハイライト2"]
        }
        
        result = AnalysisResult.from_dict(data)
        
        assert result.name == "復元結果"
        assert result.description == "説明文"
        assert result.result_type == "custom_analysis"
        assert result.data["average"] == 2.0
        assert result.metadata["key"] == "value"
        assert result.result_id == "test-id"
        assert result.tags == ["tag1", "tag2"]
        assert result.version == 3
        assert result.quality_score == 0.85
        assert result.visualization_settings["chart_type"] == "bar"
        assert result.visualization_settings["show_grid"] is False
        assert result.created_at == "2025-01-01T00:00:00"
        assert result.updated_at == "2025-01-02T00:00:00"
        assert result.summary == "要約テキスト"
        assert result.highlights == ["ハイライト1", "ハイライト2"]
