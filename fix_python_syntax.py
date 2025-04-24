#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python構文エラーを修正するスクリプト
"""

import os
import re
import sys
import shutil

def fix_data_connector_lambda():
    """
    data_connector.pyのラムダ式構文エラーを修正
    """
    file_path = "sailing_data_processor/reporting/elements/map/layers/data_connector.py"
    print(f"修正中: {file_path}")
    
    # バックアップ作成
    backup_path = f"{file_path}.syntax.bak"
    shutil.copy2(file_path, backup_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # ラムダ式を修正 (行を分割)
    pattern = r'(self\._transformers\["min_max_normalize"\] = lambda x, min_val=0\.0, max_val=1\.0:) *\n'
    replacement = r'\1\n            '
    
    fixed_content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"✅ 修正完了: {file_path}")

def fix_triple_quotes():
    """
    閉じられていない三重引用符を修正
    """
    files = [
        "sailing_data_processor/reporting/elements/timeline/event_timeline.py",
        "sailing_data_processor/reporting/elements/timeline/parameter_timeline.py"
    ]
    
    for file_path in files:
        print(f"修正中: {file_path}")
        
        # バックアップ作成
        backup_path = f"{file_path}.syntax.bak"
        shutil.copy2(file_path, backup_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # ファイル末尾に閉じ三重引用符を追加
        if not content.endswith('"""'):
            if content.endswith('\n'):
                fixed_content = content + '"""'
            else:
                fixed_content = content + '\n"""'
        else:
            fixed_content = content
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"✅ 修正完了: {file_path}")

def fix_javascript_comments():
    """
    JavaScriptコメントを修正
    """
    file_path = "sailing_data_processor/reporting/elements/timeline/playback_control.py"
    print(f"修正中: {file_path}")
    
    # バックアップ作成
    backup_path = f"{file_path}.syntax.bak"
    shutil.copy2(file_path, backup_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    in_js_string = False
    
    for line in lines:
        # JavaScriptのコメント(//)をPythonのコメント(#)に置換 or 文字列として処理
        if "// " in line and not in_js_string:
            # f-string内かどうかを確認
            if "f'''" in line or "f\"\"\"" in line:
                in_js_string = True
                fixed_lines.append(line)
            else:
                fixed_line = line.replace("// ", "# ")
                fixed_lines.append(fixed_line)
        elif in_js_string and ("'''" in line or "\"\"\"" in line):
            in_js_string = False
            fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"✅ 修正完了: {file_path}")

def fix_unmatched_braces():
    """
    余分な閉じ括弧を修正
    """
    files = [
        "sailing_data_processor/reporting/elements/visualizations/basic_charts.py",
        "sailing_data_processor/reporting/elements/visualizations/sailing_charts.py"
    ]
    
    for file_path in files:
        print(f"修正中: {file_path}")
        
        # バックアップ作成
        backup_path = f"{file_path}.syntax.bak"
        shutil.copy2(file_path, backup_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 余分な閉じ括弧を削除 (簡易的な修正)
        if file_path.endswith("basic_charts.py"):
            fixed_content = content.replace("\n}\n", "\n\n")
        elif file_path.endswith("sailing_charts.py"):
            fixed_content = re.sub(r'(\s+)\}\s*\n', r'\1\n', content)
        else:
            fixed_content = content
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"✅ 修正完了: {file_path}")

def fix_japanese_chars():
    """
    日本語句読点の構文エラーを修正
    """
    file_path = "sailing_data_processor/validation/visualization_improvements.py"
    print(f"修正中: {file_path}")
    
    # バックアップ作成
    backup_path = f"{file_path}.syntax.bak"
    shutil.copy2(file_path, backup_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 日本語を許可するために、該当行を三重引用符で囲む処理を追加
    lines = content.split('\n')
    modified_lines = []
    
    in_triple_quotes = False
    for i, line in enumerate(lines):
        # 全角文字を含む行があり、三重引用符内にない場合
        if re.search(r'[^\x00-\x7F]', line) and not in_triple_quotes and not line.strip().startswith('#'):
            # コメントでない場合、三重引用符でのコメントに変換
            if not line.strip().startswith('"""') and not line.strip().startswith("'''"):
                line = f'"""{line}"""'
            
        modified_lines.append(line)
        
        # 三重引用符の開始/終了を追跡
        if '"""' in line or "'''" in line:
            # 同じ行に偶数個ある場合は三重引用符の状態は変わらない
            if line.count('"""') % 2 == 1 or line.count("'''") % 2 == 1:
                in_triple_quotes = not in_triple_quotes
    
    fixed_content = '\n'.join(modified_lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"✅ 修正完了: {file_path}")

def main():
    """
    メイン関数
    """
    print("Python構文エラー修正を開始します...")
    
    # data_connector.pyのラムダ式修正
    fix_data_connector_lambda()
    
    # 閉じられていない三重引用符を修正
    fix_triple_quotes()
    
    # JavaScriptコメントを修正
    fix_javascript_comments()
    
    # 余分な閉じ括弧を修正
    fix_unmatched_braces()
    
    # 日本語句読点の構文エラーを修正
    fix_japanese_chars()
    
    print("\n全ての修正が完了しました")

if __name__ == "__main__":
    main()
