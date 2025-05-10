#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
シンプルなデバッグスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sailing_data_processor.project.project_storage import ProjectStorage
import tempfile
import shutil


temp_dir = tempfile.mkdtemp()
storage = ProjectStorage(temp_dir)

print("Testing ProjectStorage")
print(f"Base path: {storage.base_path}")
print(f"Projects in cache: {len(storage.projects)}")

# プロジェクトを1つ作成
project1 = storage.create_project(
    name="Tokyo Project",
    description="Project in Tokyo",
    tags=["tokyo"]
)

print(f"Created project: {project1}")
print(f"Projects in cache after creation: {len(storage.projects)}")

# 検索してみる
results = storage.search_projects(query="tokyo")
print(f"Search results for 'tokyo': {len(results)}")

shutil.rmtree(temp_dir)
