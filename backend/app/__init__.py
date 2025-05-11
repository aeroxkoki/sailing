# -*- coding: utf-8 -*-
"""初期化ファイル"""

# プロジェクトルートディレクトリをPython pathに追加
import os
import sys

# プロジェクトルートディレクトリをPython pathに追加
# これにより sailing_data_processor モジュールがインポート可能になる
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)
