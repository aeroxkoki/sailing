# -*- coding: utf-8 -*-
"""
プロジェクト検索機能修正パッチ

- ProjectStorageクラスのsearch_projectsメソッドを修正
- 日本語でのクエリ検索およびタグ検索の動作を改善
"""

from pathlib import Path
import shutil
import re

def apply_patch():
    """プロジェクト検索機能の修正を適用する"""
    # 修正するファイルのパス
    file_path = Path(__file__).parents[2] / "sailing_data_processor" / "project" / "project_storage.py"
    
    # バックアップを作成
    backup_path = file_path.with_suffix(".py.bak")
    shutil.copy2(file_path, backup_path)
    print(f"バックアップを作成しました: {backup_path}")
    
    # ファイルを読み込む
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # search_projects関数を探す
    func_pattern = r'def search_projects\(self, query: str = None, tags: List\[str\] = None\) -> List\[Project\]:.*?(?=\n    def|\n\n|$)'
    func_match = re.search(func_pattern, content, re.DOTALL)
    
    if not func_match:
        print("search_projects関数が見つかりませんでした。")
        return False
    
    old_func = func_match.group(0)
    
    # 修正後の関数（インデントに注意）
    new_func = '''def search_projects(self, query: str = None, tags: List[str] = None) -> List[Project]:
        """
        プロジェクトを検索
        
        Parameters
        ----------
        query : str, optional
            検索クエリ, by default None
        tags : List[str], optional
            タグでフィルタリング, by default None
            
        Returns
        -------
        List[Project]
            マッチするプロジェクトのリスト
        """
        # すべてのプロジェクトを取得
        all_projects = list(self.projects.values())
        results = []
        
        # クエリがなく、タグもない場合はすべてのプロジェクトを返す
        if not query and not tags:
            return all_projects
        
        # クエリで検索
        if query:
            query = query.lower()
            for project in all_projects:
                # 名前または説明文に部分一致するものを追加
                project_name = project.name.lower() if project.name else ""
                project_desc = project.description.lower() if project.description else ""
                
                if query in project_name or query in project_desc:
                    results.append(project)
        else:
            # クエリがない場合は全プロジェクトを対象にする
            results = all_projects
        
        # タグで検索
        if tags:
            tag_results = []
            
            for project in results:
                # プロジェクトにタグリストがなければ空リストとして扱う
                project_tags = project.tags if project.tags else []
                
                # タグのいずれかが一致する場合に含める
                if any(tag in project_tags for tag in tags):
                    tag_results.append(project)
            
            results = tag_results
        
        return results'''
    
    # 関数の置換
    new_content = content.replace(old_func, new_func)
    
    # 修正を適用
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"プロジェクト検索機能の修正を適用しました: {file_path}")
    return True

if __name__ == "__main__":
    apply_patch()
