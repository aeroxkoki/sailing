#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
セッションマネージャーのバグ修正スクリプト

テストで見つかったエラー：
- test_update_session_status - Expected: mockは呼び出されない。Actual: not called.
- test_update_session_category - Expected: mockは呼び出されない。Actual: not called.
- test_update_session_tags - Expected: mock('6205ae47-4ac6-4a26-a5b8-5c8b7280a1d7', ['test', 'practice'], ['advanced', 'windy', 'test'])。 Actual: not called.
"""

import sys
import os
import re

def fix_session_manager(file_path):
    """session_manager.py ファイルを修正します"""
    
    # ファイルの存在確認
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
    
    print(f"Fixing {file_path}")
    
    # ファイルを読み込む
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # バックアップファイルの作成
    backup_path = f"{file_path}.bak"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Backup created: {backup_path}")
    
    # update_session_status メソッドの修正
    status_pattern = r'def update_session_status\(self, session_id: str, status: str\)(.*?)try:(.*?)# ステータスを更新\n\s+session\.status = status(.*?)except Exception as e:'
    status_replacement = r'def update_session_status(self, session_id: str, status: str)\1try:\2# Sessionオブジェクトにupdate_statusメソッドがあればそれを使用\n        if hasattr(session, \'update_status\') and callable(getattr(session, \'update_status\')):\n            session.update_status(status)\n        else:\n            # 直接属性として設定\n            session.status = status\3except Exception as e:'
    content = re.sub(status_pattern, status_replacement, content, flags=re.DOTALL)
    
    # update_session_category メソッドの修正
    category_pattern = r'def update_session_category\(self, session_id: str, category: str\)(.*?)try:(.*?)# カテゴリを更新\n\s+session\.category = category(.*?)except Exception as e:'
    category_replacement = r'def update_session_category(self, session_id: str, category: str)\1try:\2# Sessionオブジェクトにupdate_categoryメソッドがあればそれを使用\n        if hasattr(session, \'update_category\') and callable(getattr(session, \'update_category\')):\n            session.update_category(category)\n        else:\n            # 直接属性として設定\n            session.category = category\3except Exception as e:'
    content = re.sub(category_pattern, category_replacement, content, flags=re.DOTALL)
    
    # 修正したファイルを保存
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Session manager fixed successfully")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # デフォルトパス
        file_path = "sailing_data_processor/project/session_manager.py"
    
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    abs_file_path = os.path.join(root_dir, file_path)
    
    if fix_session_manager(abs_file_path):
        print("Success\!")
    else:
        print("Failed to fix session manager.")
        sys.exit(1)
