"""
ui.integrated.components.navigation.breadcrumb

パンくずナビゲーションコンポーネント
ユーザーが現在のページの階層構造を理解し、容易に前のページに戻れるようにします。
"""

import streamlit as st
from typing import List, Dict, Tuple, Optional

class BreadcrumbComponent:
    """パンくずナビゲーションコンポーネント"""
    
    def __init__(self, key_prefix: str = "breadcrumb"):
        """
        初期化
        
        Parameters
        ----------
        key_prefix : str, optional
            Streamlitコンポーネントキーのプレフィックス, by default "breadcrumb"
        """
        self.key_prefix = key_prefix
    
    def render(self, items: List[Dict[str, str]]):
        """
        パンくずナビゲーションを表示
        
        Parameters
        ----------
        items : List[Dict[str, str]]
            表示するナビゲーション項目のリスト
            各項目は{'label': 'ラベル', 'url': 'URL'(オプション)}の形式
            最後の項目はアクティブ（現在のページ）として表示される
        """
        # パンくずナビゲーションのスタイル
        breadcrumb_style = """
        <style>
            .breadcrumb {
                display: flex;
                flex-wrap: wrap;
                padding: 0.5rem 1rem;
                list-style: none;
                background-color: #f5f5f5;
                border-radius: 0.25rem;
                margin-bottom: 1rem;
                align-items: center;
                font-size: 0.9rem;
            }
            .breadcrumb-item {
                display: flex;
                align-items: center;
            }
            .breadcrumb-item + .breadcrumb-item::before {
                content: "›";
                display: inline-block;
                padding: 0 0.5rem;
                color: #666;
            }
            .breadcrumb-item a {
                color: #0366d6;
                text-decoration: none;
            }
            .breadcrumb-item a:hover {
                text-decoration: underline;
            }
            .breadcrumb-item.active {
                color: #6c757d;
                font-weight: 500;
            }
            .breadcrumb-home {
                margin-right: 5px;
            }
            .breadcrumb-separator {
                margin: 0 8px;
                color: #666;
            }
        </style>
        """
        
        # SVGアイコン（ホーム）
        home_icon = """
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" 
             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" 
             stroke-linejoin="round" class="breadcrumb-home">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
            <polyline points="9 22 9 12 15 12 15 22"></polyline>
        </svg>
        """
        
        # パンくずナビゲーションのHTML生成
        breadcrumb_html = f"""
        {breadcrumb_style}
        <nav aria-label="breadcrumb">
            <ol class="breadcrumb">
        """
        
        # 項目の追加
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            item_class = "breadcrumb-item active" if is_last else "breadcrumb-item"
            
            if i == 0:  # 最初の項目（ホーム）
                breadcrumb_html += f"""
                <li class="{item_class}">
                    {'<span>' if is_last else f'<a href="{item.get("url", "#")}">'}
                    {home_icon} {item['label']}
                    {'</span>' if is_last else '</a>'}
                </li>
                """
            else:
                breadcrumb_html += f"""
                <li class="{item_class}">
                    {'<span>' if is_last else f'<a href="{item.get("url", "#")}">'}
                    {item['label']}
                    {'</span>' if is_last else '</a>'}
                </li>
                """
        
        breadcrumb_html += """
            </ol>
        </nav>
        """
        
        st.markdown(breadcrumb_html, unsafe_allow_html=True)
    
    def create_path(self, current_page: str, page_hierarchy: Dict[str, List[str]] = None) -> List[Dict[str, str]]:
        """
        現在のページに基づいてパンくずナビゲーションのパスを作成
        
        Parameters
        ----------
        current_page : str
            現在のページ名
        page_hierarchy : Dict[str, List[str]], optional
            ページの階層構造, by default None
            
        Returns
        -------
        List[Dict[str, str]]
            パンくずナビゲーション項目のリスト
        """
        # デフォルトの階層構造
        if page_hierarchy is None:
            page_hierarchy = {
                "welcome": [],
                "project_list": [],
                "project_create": ["project_list"],
                "project_detail": ["project_list"],
                "data_import": [],
                "batch_import": ["data_import"],
                "data_validation": ["data_import"],
                "data_export": [],
                "export": [],
                "wind_estimation": ["dashboard"],
                "strategy_detection": ["dashboard"],
                "performance_analysis": ["dashboard"],
                "map_view": ["dashboard"],
                "chart_view": ["dashboard"],
                "timeline_view": ["dashboard"],
                "statistical_view": ["dashboard"],
                "report_builder": ["dashboard"],
                "dashboard": [],
                "results_dashboard": ["dashboard"],
                "workflow": []
            }
        
        # ページ名のマッピング
        page_names = {
            "welcome": "ホーム",
            "project_list": "プロジェクト一覧",
            "project_create": "新規プロジェクト",
            "project_detail": "プロジェクト詳細",
            "data_import": "データインポート",
            "batch_import": "バッチインポート",
            "data_validation": "データ検証",
            "data_export": "データエクスポート",
            "export": "エクスポート",
            "wind_estimation": "風推定",
            "strategy_detection": "戦略検出",
            "performance_analysis": "パフォーマンス分析",
            "map_view": "マップビュー",
            "chart_view": "チャートビュー",
            "timeline_view": "タイムラインビュー",
            "statistical_view": "統計ビュー",
            "report_builder": "レポート作成",
            "dashboard": "ダッシュボード",
            "results_dashboard": "分析結果",
            "workflow": "ワークフロー"
        }
        
        # パスを作成
        path = []
        
        # ホームページの追加
        path.append({
            "label": page_names.get("welcome", "ホーム"),
            "url": "?page=welcome"
        })
        
        # 親ページがある場合は追加
        if current_page in page_hierarchy and page_hierarchy[current_page]:
            for parent_page in page_hierarchy[current_page]:
                path.append({
                    "label": page_names.get(parent_page, parent_page),
                    "url": f"?page={parent_page}"
                })
        
        # 現在のページを追加
        path.append({
            "label": page_names.get(current_page, current_page)
        })
        
        return path
