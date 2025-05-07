# -*- coding: utf-8 -*-
"""
プロジェクト検索機能の修正が正しく適用されたかをテストするスクリプト
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# プロジェクトストレージをインポート
from sailing_data_processor.project.project_storage import ProjectStorage
from sailing_data_processor.project.project_model import Project

def test_search_projects():
    """プロジェクト検索機能をテスト"""
    # 一時ディレクトリを作成
    temp_dir = tempfile.mkdtemp()
    
    try:
        # プロジェクトストレージを初期化
        storage = ProjectStorage(temp_dir)
        
        # テスト用プロジェクトを作成
        project1 = storage.create_project(
            name="Sailing Competition",
            description="Race in Tokyo Bay",
            tags=["race", "tokyo"]
        )
        
        project2 = storage.create_project(
            name="Practice Session",
            description="Practice in Yokohama",
            tags=["practice", "yokohama"]
        )
        
        project3 = storage.create_project(
            name="Analysis Project",
            description="Wind direction analysis",
            tags=["analysis", "wind", "tokyo"]
        )
        
        # 名前・説明による検索
        print("\nテスト1: テキスト検索 (tokyo)")
        results = storage.search_projects(query="tokyo")
        print(f"結果: {len(results)}件")
        for p in results:
            print(f" - {p.name}: {p.description}")
        
        # タグによる検索
        print("\nテスト2: タグ検索 (tokyo)")
        results = storage.search_projects(tags=["tokyo"])
        print(f"結果: {len(results)}件")
        for p in results:
            print(f" - {p.name}: タグ = {p.tags}")
        
        # 複合検索（日本語）
        print("\nテスト3: 複合検索 (分析 + wind)")
        results = storage.search_projects(query="分析", tags=["wind"])
        print(f"結果: {len(results)}件")
        for p in results:
            print(f" - {p.name}: {p.description}, タグ = {p.tags}")
            
        # 日本語のテスト用に新しいプロジェクトを追加
        project4 = storage.create_project(
            name="東京湾トレーニング",
            description="東京湾でのセーリング技術分析",
            tags=["分析", "トレーニング"]
        )
        
        # 日本語検索
        print("\nテスト4: 日本語検索 (東京)")
        results = storage.search_projects(query="東京")
        print(f"結果: {len(results)}件")
        for p in results:
            print(f" - {p.name}: {p.description}")
        
        # 日本語タグ検索
        print("\nテスト5: 日本語タグ検索 (分析)")
        results = storage.search_projects(tags=["分析"])
        print(f"結果: {len(results)}件")
        for p in results:
            print(f" - {p.name}: タグ = {p.tags}")
        
    finally:
        # 一時ディレクトリを削除
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    print("プロジェクト検索機能修正テスト開始...\n")
    test_search_projects()
    print("\nテスト完了")
