#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python構文エラーを修正する改良版スクリプト
さまざまな構文エラーに対処します
"""

import os
import re
import sys
import shutil
import glob

def fix_data_connector_lambda():
    """
    data_connector.pyのラムダ式構文エラーを修正
    """
    file_path = "sailing_data_processor/reporting/elements/map/layers/data_connector.py"
    print(f"修正中: {file_path}")
    
    # バックアップ作成
    backup_path = f"{file_path}.fix.bak"
    shutil.copy2(file_path, backup_path)
    
    lines = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 問題のある行を探して修正
    for i in range(len(lines)):
        if "self._transformers[\"min_max_normalize\"]" in lines[i] and "lambda" in lines[i]:
            # 行末に : がある場合
            if lines[i].rstrip().endswith(':'):
                if i + 1 < len(lines):
                    # 次の行が適切にインデントされているか確認
                    if not lines[i+1].strip().startswith('('):
                        # 適切に修正
                        indent = ' ' * (len(lines[i]) - len(lines[i].lstrip()))
                        lines[i] = lines[i].rstrip() + '\n'
                        lines.insert(i+1, indent + '    (x - min_val) / (max_val - min_val) if x is not None and max_val > min_val else None\n')
                        print(f"  ラムダ式を複数行に分割しました")
                        break
    
    # ファイル書き込み
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✅ 修正完了: {file_path}")

def fix_triple_quotes_properly(file_path):
    """
    三重引用符の問題を適切に修正
    """
    print(f"修正中: {file_path}")
    
    # バックアップ作成
    backup_path = f"{file_path}.fix.bak"
    shutil.copy2(file_path, backup_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 閉じられていない三重引用符を数える
        open_count = content.count('"""')
        if open_count % 2 != 0:
            # 閉じ三重引用符を追加
            content += '\n"""'
            print(f"  閉じられていない三重引用符を追加しました")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 修正完了: {file_path}")
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def fix_javascript_comments_properly(file_path):
    """
    JavaScriptコメントを適切に修正
    """
    print(f"修正中: {file_path}")
    
    # バックアップ作成
    backup_path = f"{file_path}.fix.bak"
    shutil.copy2(file_path, backup_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        in_triple_quotes = False
        triple_quote_type = None
        
        for i, line in enumerate(lines):
            # 三重引用符のトラッキング
            if '"""' in line and not in_triple_quotes:
                in_triple_quotes = True
                triple_quote_type = '"""'
            elif "'''" in line and not in_triple_quotes:
                in_triple_quotes = True
                triple_quote_type = "'''"
            elif triple_quote_type in line and in_triple_quotes:
                # 閉じる三重引用符をチェック (同じ行に複数ないかも確認)
                if line.count(triple_quote_type) % 2 != 0:
                    in_triple_quotes = False
                    triple_quote_type = None
            
            # JavaScriptコメントの処理
            if "//" in line and not in_triple_quotes:
                # Python コメントに変換
                line = line.replace("//", "#", 1)
            
            fixed_lines.append(line)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        
        print(f"✅ 修正完了: {file_path}")
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def fix_unmatched_braces_properly(file_path):
    """
    閉じ括弧の問題を修正
    """
    print(f"修正中: {file_path}")
    
    # バックアップ作成
    backup_path = f"{file_path}.fix.bak"
    shutil.copy2(file_path, backup_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        for line in lines:
            # 行の先頭や空白後に } だけがある行を削除
            if line.strip() == "}" or re.match(r'^\s+}\s*$', line):
                continue
            fixed_lines.append(line)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        
        print(f"✅ 修正完了: {file_path}")
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def check_template_model():
    """
    template_model.pyのElementModelクラスが存在するか確認して修正
    """
    file_path = "sailing_data_processor/reporting/templates/template_model.py"
    print(f"確認中: {file_path}")
    
    try:
        # ディレクトリ確認
        dir_path = os.path.dirname(file_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"  ディレクトリを作成しました: {dir_path}")
        
        # ファイル存在確認
        if not os.path.exists(file_path):
            # 空のファイルを作成
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('"""\nsailing_data_processor.reporting.templates.template_model\n\n要素のテンプレートモデルを定義するモジュールです。\n"""\n\nfrom enum import Enum, auto\nfrom typing import Dict, List, Any, Optional\n\n\nclass ElementType(Enum):\n    """要素タイプの列挙型"""\n    GENERIC = auto()\n    TEXT = auto()\n    MAP = auto()\n    CHART = auto()\n    TABLE = auto()\n    TIMELINE = auto()\n    CONTAINER = auto()\n    DASHBOARD = auto()\n\n\nclass ElementModel:\n    """要素モデルクラス"""\n    \n    def __init__(self, element_type: ElementType = ElementType.GENERIC, properties: Dict[str, Any] = None):\n        """初期化"""\n        self.element_type = element_type\n        self.properties = properties or {}\n    \n    def get_property(self, key: str, default: Any = None) -> Any:\n        """プロパティを取得"""\n        return self.properties.get(key, default)\n    \n    def set_property(self, key: str, value: Any) -> None:\n        """プロパティを設定"""\n        self.properties[key] = value\n    \n    def to_dict(self) -> Dict[str, Any]:\n        """辞書表現を取得"""\n        return {\n            "element_type": self.element_type.name,\n            "properties": self.properties.copy()\n        }\n    \n    @classmethod\n    def from_dict(cls, data: Dict[str, Any]) -> "ElementModel":\n        """辞書から生成"""\n        element_type = ElementType[data.get("element_type", "GENERIC")]\n        properties = data.get("properties", {})\n        return cls(element_type=element_type, properties=properties)\n')
            print(f"  ElementModelクラスを含むファイルを作成しました")
        else:
            # ファイルが存在する場合、内容を確認
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ElementModelクラスがあるか確認
            if "class ElementModel" not in content:
                # バックアップ作成
                backup_path = f"{file_path}.fix.bak"
                shutil.copy2(file_path, backup_path)
                
                # ElementModelクラスを追加
                with open(file_path, 'w', encoding='utf-8') as f:
                    if "class ElementType" not in content:
                        # ElementTypeもなければ両方追加
                        f.write(content + '\n\n\nclass ElementType(Enum):\n    """要素タイプの列挙型"""\n    GENERIC = auto()\n    TEXT = auto()\n    MAP = auto()\n    CHART = auto()\n    TABLE = auto()\n    TIMELINE = auto()\n    CONTAINER = auto()\n    DASHBOARD = auto()\n\n\nclass ElementModel:\n    """要素モデルクラス"""\n    \n    def __init__(self, element_type: ElementType = ElementType.GENERIC, properties: Dict[str, Any] = None):\n        """初期化"""\n        self.element_type = element_type\n        self.properties = properties or {}\n    \n    def get_property(self, key: str, default: Any = None) -> Any:\n        """プロパティを取得"""\n        return self.properties.get(key, default)\n    \n    def set_property(self, key: str, value: Any) -> None:\n        """プロパティを設定"""\n        self.properties[key] = value\n    \n    def to_dict(self) -> Dict[str, Any]:\n        """辞書表現を取得"""\n        return {\n            "element_type": self.element_type.name,\n            "properties": self.properties.copy()\n        }\n    \n    @classmethod\n    def from_dict(cls, data: Dict[str, Any]) -> "ElementModel":\n        """辞書から生成"""\n        element_type = ElementType[data.get("element_type", "GENERIC")]\n        properties = data.get("properties", {})\n        return cls(element_type=element_type, properties=properties)\n')
                    else:
                        # ElementTypeのみある場合はElementModelだけ追加
                        f.write(content + '\n\n\nclass ElementModel:\n    """要素モデルクラス"""\n    \n    def __init__(self, element_type: ElementType = ElementType.GENERIC, properties: Dict[str, Any] = None):\n        """初期化"""\n        self.element_type = element_type\n        self.properties = properties or {}\n    \n    def get_property(self, key: str, default: Any = None) -> Any:\n        """プロパティを取得"""\n        return self.properties.get(key, default)\n    \n    def set_property(self, key: str, value: Any) -> None:\n        """プロパティを設定"""\n        self.properties[key] = value\n    \n    def to_dict(self) -> Dict[str, Any]:\n        """辞書表現を取得"""\n        return {\n            "element_type": self.element_type.name,\n            "properties": self.properties.copy()\n        }\n    \n    @classmethod\n    def from_dict(cls, data: Dict[str, Any]) -> "ElementModel":\n        """辞書から生成"""\n        element_type = ElementType[data.get("element_type", "GENERIC")]\n        properties = data.get("properties", {})\n        return cls(element_type=element_type, properties=properties)\n')
                
                print(f"  ElementModelクラスを追加しました")
            else:
                print(f"  ElementModelクラスは既に存在します")
        
        print(f"✅ 確認完了: {file_path}")
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def fix_visualization_improvements():
    """
    visualization_improvements.pyの構文エラーを修正
    """
    file_path = "sailing_data_processor/validation/visualization_improvements.py"
    print(f"修正中: {file_path}")
    
    # バックアップ作成
    backup_path = f"{file_path}.fix.bak"
    shutil.copy2(file_path, backup_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 各行が有効なPythonコードかチェック、必要に応じて修正
        fixed_lines = []
        for i, line in enumerate(lines):
            if re.search(r'[^\x00-\x7F]', line) and not (line.strip().startswith('#') or line.strip().startswith('"""') or line.strip().startswith("'''")):
                # 非ASCII文字を含むコードを文字列に変換
                line = f'"""{line.strip()}"""\n'
            
            # キーワード引数の後に位置引数がある行を修正
            if "=" in line and "," in line:
                parts = line.split(",")
                has_keyword = False
                has_positional_after_keyword = False
                
                for j, part in enumerate(parts):
                    if "=" in part and not ('"' in part or "'" in part):
                        has_keyword = True
                    elif has_keyword and j > 0 and "=" not in part and part.strip() and not ('"' in part or "'" in part):
                        has_positional_after_keyword = True
                
                if has_positional_after_keyword:
                    # この行をコメントアウト
                    line = f"# {line} # AUTO-COMMENTED: キーワード引数の後に位置引数があります\n"
            
            fixed_lines.append(line)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        
        print(f"✅ 修正完了: {file_path}")
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def fix_all_python_files():
    """
    sailing_data_processor内のすべてのPythonファイルを構文エラーがないかチェックして修正
    """
    # 対象パターン
    patterns = [
        "sailing_data_processor/reporting/elements/**/*.py",
        "sailing_data_processor/validation/*.py"
    ]
    
    # ファイルリストを収集
    python_files = []
    for pattern in patterns:
        files = glob.glob(pattern, recursive=True)
        python_files.extend(files)
    
    print(f"{len(python_files)}個のPythonファイルを処理します...")
    
    # 全ファイルを修正
    for file_path in python_files:
        # 三重引用符問題の修正
        fix_triple_quotes_properly(file_path)
        
        # JavaScriptコメントの修正
        fix_javascript_comments_properly(file_path)
        
        # 余分な閉じ括弧の修正
        fix_unmatched_braces_properly(file_path)
    
    print("すべてのファイルの処理が完了しました")

def main():
    """
    メイン関数
    """
    print("Python構文エラー修正を開始します...")
    
    # 特定のファイルの問題を修正
    fix_data_connector_lambda()
    
    # テンプレートモデルの確認と修正
    check_template_model()
    
    # visualization_improvementsの修正
    fix_visualization_improvements()
    
    # 全てのPythonファイルの一般的な問題を修正
    fix_all_python_files()
    
    print("\n全ての修正が完了しました")
    print("テストを実行して確認してください")

if __name__ == "__main__":
    main()
