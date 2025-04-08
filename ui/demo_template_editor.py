"""
ui.demo_template_editor

テンプレートエディタのデモアプリケーションです。
このモジュールは、レポートテンプレートエディタの基本機能を実演します。
"""

import streamlit as st
import os
import sys
import pandas as pd
from pathlib import Path

# プロジェクトのルートディレクトリをPYTHONPATHに追加
root_dir = Path(__file__).parent.parent.absolute()
sys.path.append(str(root_dir))

from sailing_data_processor.reporting.templates.template_manager import TemplateManager
from sailing_data_processor.reporting.templates.template_model import (
    Template, Section, Element, ElementType, SectionType, TemplateOutputFormat
)
from ui.components.reporting.template_editor import TemplateEditor


def main():
    st.set_page_config(
        page_title="レポートテンプレートエディタ デモ",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("レポートテンプレートエディタ デモ")
    
    # テンプレートマネージャーの初期化
    template_dir = Path(root_dir) / "data" / "templates"
    os.makedirs(template_dir, exist_ok=True)
    
    template_manager = TemplateManager(template_dir)
    
    # サイドバー
    with st.sidebar:
        st.header("テンプレートエディタについて")
        st.markdown("""
        このデモアプリケーションは、セーリング戦略分析レポートのためのテンプレートを
        作成・編集するためのインターフェースを提供します。

        ### 主な機能

        - テンプレートの作成と管理
        - セクションと要素の編集
        - リアルタイムプレビュー
        - テンプレートのエクスポート/インポート

        ### 使い方

        1. 「テンプレート選択」タブで既存のテンプレートを選択するか、新規作成します
        2. 「テンプレート編集」タブでセクションや要素を編集します
        3. 「プレビュー」タブで実際の表示を確認します
        """)
        
        st.divider()
        
        # 標準テンプレート生成ボタン
        if st.button("標準テンプレートを生成", help="基本的な標準テンプレートを生成します"):
            try:
                # 標準テンプレートモジュールのインポート
                from sailing_data_processor.reporting.templates.standard_templates import get_all_standard_templates
                
                # 標準テンプレートを取得
                templates = get_all_standard_templates()
                
                # テンプレートを保存
                for template in templates:
                    template_manager.save_template(template)
                
                st.success(f"{len(templates)}個の標準テンプレートを生成しました")
            except Exception as e:
                st.error(f"標準テンプレートの生成に失敗しました: {str(e)}")
    
    # テンプレートエディタの表示
    template_editor = TemplateEditor(template_manager)
    template_editor.render()

if __name__ == "__main__":
    main()
