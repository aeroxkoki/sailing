#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
複合検索のテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sailing_data_processor.project.project_storage import ProjectStorage
import tempfile
import shutil


temp_dir = tempfile.mkdtemp()
storage = ProjectStorage(temp_dir)

print("Testing Complex Search")

# プロジェクトを作成
project3 = storage.create_project(
    name="Analysis Project",
    description="Wind direction analysis",
    tags=["analysis", "wind", "tokyo"]
)

print(f"Created project: {project3}")
print(f"Name: {project3.name}")
print(f"Description: {project3.description}")
print(f"Tags: {project3.tags}")

# 複合検索: query="分析", tags=["wind"]
print("\n=== Complex search: query='分析', tags=['wind'] ===")
results = storage.search_projects(query="分析", tags=["wind"])
print(f"Found {len(results)} results")

# デバッグのため、検索の詳細を表示
query = "分析"
tags = ["wind"]

print(f"\nDebug info:")
print(f"Query: '{query}'")
print(f"Tags: {tags}")

for project in storage.projects.values():
    print(f"\nChecking project: {project.name}")
    print(f"  Description: {project.description}")
    print(f"  Description lower: {project.description.lower()}")
    print(f"  '{query}' in description: {query in project.description}")
    print(f"  '{query}' in description.lower(): {query in project.description.lower()}")
    print(f"  Project tags: {project.tags}")
    print(f"  Any tag match: {any(tag in project.tags for tag in tags)}")

shutil.rmtree(temp_dir)
