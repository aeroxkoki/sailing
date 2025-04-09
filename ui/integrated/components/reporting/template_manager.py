"""
ui.integrated.components.reporting.template_manager

セーリング戦略分析システムのレポートテンプレート管理モジュール
"""

import os
import json
import datetime
import streamlit as st
from typing import Dict, Any, List, Optional, Tuple, Union
import uuid


class TemplateManager:
    """
    レポートテンプレートを管理するクラス。
    テンプレートの読み込み、保存、編集、適用などの機能を提供します。
    """
    
    # テンプレートのタイプリスト
    TEMPLATE_TYPES = [
        "標準分析レポート",
        "簡易サマリー",
        "詳細技術レポート",
        "コーチング用レポート",
        "レース分析レポート",
        "チーム共有レポート",
        "カスタムテンプレート"
    ]
    
    # テンプレートのセクションリスト
    SECTION_TYPES = [
        "基本情報",
        "風向分析",
        "パフォーマンス指標",
        "戦略ポイント分析",
        "マップビュー",
        "統計チャート",
        "データ品質",
        "改善提案",
        "比較分析",
        "カスタムセクション"
    ]
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        テンプレートマネージャーの初期化
        
        Args:
            template_dir: テンプレートファイルが保存されているディレクトリパス
                          指定がない場合はデフォルトの場所を使用
        """
        # デフォルトのテンプレートディレクトリ
        if template_dir is None:
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
            self.template_dir = os.path.join(root_dir, 'data', 'templates')
            # ディレクトリが存在しない場合は作成
            os.makedirs(self.template_dir, exist_ok=True)
        else:
            self.template_dir = template_dir
        
        # セッション状態の初期化
        if 'template_cache' not in st.session_state:
            st.session_state.template_cache = {}
        
        # テンプレートの読み込み
        self.templates = self._load_templates()
        
        # テンプレートが存在しない場合はデフォルトテンプレートを作成
        if not self.templates:
            self._create_default_templates()
            self.templates = self._load_templates()

    def get_templates(self) -> Dict[str, Any]:
        """
        利用可能なすべてのテンプレートを取得
        
        Returns:
            テンプレートの辞書（キー: テンプレートID, 値: テンプレート情報）
        """
        return self.templates

    def get_template(self, template_id: str) -> Dict[str, Any]:
        """
        指定されたIDのテンプレートを取得
        
        Args:
            template_id: テンプレートID
            
        Returns:
            テンプレート情報の辞書
            
        Raises:
            ValueError: 指定されたIDのテンプレートが存在しない場合
        """
        if template_id in self.templates:
            return self.templates[template_id]
        else:
            raise ValueError(f"テンプレートID '{template_id}' は存在しません")

    def create_template(self, name: str, template_type: str, 
                        sections: List[Dict[str, Any]], 
                        description: str = "") -> str:
        """
        新しいテンプレートを作成
        
        Args:
            name: テンプレート名
            template_type: テンプレートのタイプ
            sections: セクションのリスト
            description: テンプレートの説明
            
        Returns:
            作成されたテンプレートのID
        """
        template_id = str(uuid.uuid4())
        
        template = {
            "id": template_id,
            "name": name,
            "type": template_type,
            "description": description,
            "sections": sections,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        # テンプレートの保存
        self.templates[template_id] = template
        self._save_template(template)
        
        return template_id

    def update_template(self, template_id: str, 
                        updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        既存のテンプレートを更新
        
        Args:
            template_id: 更新するテンプレートのID
            updates: 更新する項目の辞書
            
        Returns:
            更新されたテンプレート情報
            
        Raises:
            ValueError: 指定されたIDのテンプレートが存在しない場合
        """
        if template_id not in self.templates:
            raise ValueError(f"テンプレートID '{template_id}' は存在しません")
        
        template = self.templates[template_id].copy()
        
        # 更新可能なフィールド
        allowed_fields = ["name", "type", "description", "sections"]
        
        for field, value in updates.items():
            if field in allowed_fields:
                template[field] = value
        
        # 更新日時を設定
        template["updated_at"] = datetime.datetime.now().isoformat()
        
        # テンプレートの保存
        self.templates[template_id] = template
        self._save_template(template)
        
        return template

    def delete_template(self, template_id: str) -> bool:
        """
        テンプレートを削除
        
        Args:
            template_id: 削除するテンプレートのID
            
        Returns:
            削除が成功したかどうか
            
        Raises:
            ValueError: 指定されたIDのテンプレートが存在しない場合
        """
        if template_id not in self.templates:
            raise ValueError(f"テンプレートID '{template_id}' は存在しません")
        
        # テンプレートの削除
        template_file = os.path.join(self.template_dir, f"{template_id}.json")
        if os.path.exists(template_file):
            os.remove(template_file)
        
        # メモリ上のテンプレートも削除
        del self.templates[template_id]
        
        return True

    def import_template(self, template_data: Dict[str, Any]) -> str:
        """
        外部からテンプレートをインポート
        
        Args:
            template_data: インポートするテンプレートデータ
            
        Returns:
            インポートされたテンプレートのID
        """
        # テンプレートIDを新しく生成
        template_id = str(uuid.uuid4())
        
        template = template_data.copy()
        template["id"] = template_id
        template["imported_at"] = datetime.datetime.now().isoformat()
        
        if "created_at" not in template:
            template["created_at"] = datetime.datetime.now().isoformat()
        
        template["updated_at"] = datetime.datetime.now().isoformat()
        
        # テンプレートの保存
        self.templates[template_id] = template
        self._save_template(template)
        
        return template_id

    def export_template(self, template_id: str) -> Dict[str, Any]:
        """
        テンプレートをエクスポート
        
        Args:
            template_id: エクスポートするテンプレートのID
            
        Returns:
            エクスポート用のテンプレートデータ
            
        Raises:
            ValueError: 指定されたIDのテンプレートが存在しない場合
        """
        if template_id not in self.templates:
            raise ValueError(f"テンプレートID '{template_id}' は存在しません")
        
        return self.templates[template_id].copy()

    def clone_template(self, template_id: str, 
                       new_name: Optional[str] = None) -> str:
        """
        既存のテンプレートを複製
        
        Args:
            template_id: 複製するテンプレートのID
            new_name: 新しいテンプレート名（指定がない場合は "Copy of [元の名前]"）
            
        Returns:
            複製されたテンプレートのID
            
        Raises:
            ValueError: 指定されたIDのテンプレートが存在しない場合
        """
        if template_id not in self.templates:
            raise ValueError(f"テンプレートID '{template_id}' は存在しません")
        
        template = self.templates[template_id].copy()
        
        # 新しいテンプレート名の設定
        if new_name is None:
            new_name = f"{template['name']} のコピー"
        
        # 新しいテンプレートの作成
        return self.create_template(
            name=new_name,
            template_type=template["type"],
            sections=template["sections"],
            description=template["description"]
        )

    def render_template_selection(self) -> Tuple[str, Dict[str, Any]]:
        """
        テンプレート選択UIを描画
        
        Returns:
            選択されたテンプレートのIDとテンプレート情報
        """
        # テンプレートの一覧を表示
        template_options = [(tid, t["name"]) for tid, t in self.templates.items()]
        template_options.sort(key=lambda x: x[1])  # 名前でソート
        
        # テンプレートの選択
        selected_idx = st.selectbox(
            "テンプレートを選択",
            range(len(template_options)),
            format_func=lambda i: template_options[i][1]
        )
        
        selected_id = template_options[selected_idx][0]
        selected_template = self.templates[selected_id]
        
        # テンプレートの詳細を表示
        with st.expander("テンプレート詳細", expanded=False):
            st.write(f"**タイプ:** {selected_template['type']}")
            st.write(f"**作成日:** {self._format_datetime(selected_template['created_at'])}")
            st.write(f"**説明:** {selected_template['description']}")
            
            # セクションの一覧を表示
            st.write("**セクション:**")
            for i, section in enumerate(selected_template['sections']):
                st.write(f"{i+1}. {section['title']}")
        
        return selected_id, selected_template

    def render_template_editor(self, template_id: Optional[str] = None) -> Dict[str, Any]:
        """
        テンプレート編集UIを描画
        
        Args:
            template_id: 編集するテンプレートのID（新規作成の場合はNone）
            
        Returns:
            編集されたテンプレート情報
        """
        is_new = template_id is None
        
        if is_new:
            st.subheader("新規テンプレート作成")
            template = {
                "name": "",
                "type": "標準分析レポート",
                "description": "",
                "sections": []
            }
        else:
            st.subheader("テンプレート編集")
            template = self.get_template(template_id).copy()
        
        # 基本情報の編集
        template_name = st.text_input("テンプレート名", template["name"])
        template_type = st.selectbox("テンプレートタイプ", self.TEMPLATE_TYPES, 
                                   index=self.TEMPLATE_TYPES.index(template["type"]))
        template_desc = st.text_area("説明", template["description"])
        
        # セクションの編集
        st.subheader("セクション")
        
        # 現在のセクション
        sections = template.get("sections", []).copy()
        
        # セッション状態の初期化（セクション編集用）
        if "editing_section" not in st.session_state:
            st.session_state.editing_section = -1  # -1: 編集なし
        
        # セクション一覧の表示
        for i, section in enumerate(sections):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{i+1}. {section['title']}** ({section['type']})")
            
            with col2:
                if st.button("編集", key=f"edit_section_{i}"):
                    st.session_state.editing_section = i
            
            with col3:
                if st.button("削除", key=f"delete_section_{i}"):
                    sections.pop(i)
                    st.experimental_rerun()
        
        # セクションの追加ボタン
        if st.button("セクションを追加"):
            st.session_state.editing_section = len(sections)
            sections.append({
                "title": "新しいセクション",
                "type": "基本情報",
                "content": "",
                "options": {}
            })
            st.experimental_rerun()
        
        # セクション編集UI
        if st.session_state.editing_section >= 0:
            st.markdown("---")
            st.subheader("セクションの編集")
            
            i = st.session_state.editing_section
            if i < len(sections):
                section = sections[i]
                
                # セクション情報の編集
                section_title = st.text_input("セクションタイトル", section["title"])
                section_type = st.selectbox("セクションタイプ", self.SECTION_TYPES,
                                          index=self.SECTION_TYPES.index(section["type"]) 
                                                if section["type"] in self.SECTION_TYPES 
                                                else 0)
                
                # セクションの内容（テキスト）
                section_content = st.text_area("内容（マークダウン形式）", section.get("content", ""), height=200)
                
                # セクションオプションの編集（セクションタイプに応じて異なるオプション）
                st.subheader("セクションオプション")
                
                options = section.get("options", {}).copy()
                
                if section_type == "基本情報":
                    options["show_date"] = st.checkbox("日時を表示", options.get("show_date", True))
                    options["show_location"] = st.checkbox("場所を表示", options.get("show_location", True))
                    options["show_boat_type"] = st.checkbox("艇種を表示", options.get("show_boat_type", True))
                    options["show_conditions"] = st.checkbox("風況を表示", options.get("show_conditions", True))
                
                elif section_type in ["風向分析", "パフォーマンス指標", "データ品質"]:
                    options["show_charts"] = st.checkbox("チャートを表示", options.get("show_charts", True))
                    options["show_summary"] = st.checkbox("サマリーを表示", options.get("show_summary", True))
                    options["show_details"] = st.checkbox("詳細を表示", options.get("show_details", False))
                
                elif section_type == "マップビュー":
                    map_types = ["標準マップ", "風向マップ", "速度ヒートマップ", "VMGヒートマップ"]
                    options["map_type"] = st.selectbox("マップタイプ", map_types, 
                                                      index=map_types.index(options.get("map_type", "標準マップ")) 
                                                            if options.get("map_type") in map_types 
                                                            else 0)
                    options["show_track"] = st.checkbox("トラックを表示", options.get("show_track", True))
                    options["show_points"] = st.checkbox("ポイントを表示", options.get("show_points", True))
                
                # セクションの更新
                if st.button("セクションを更新"):
                    sections[i] = {
                        "title": section_title,
                        "type": section_type,
                        "content": section_content,
                        "options": options
                    }
                    st.session_state.editing_section = -1
                    st.experimental_rerun()
                
                if st.button("キャンセル"):
                    st.session_state.editing_section = -1
                    st.experimental_rerun()
        
        # テンプレートの保存
        st.markdown("---")
        if st.button("テンプレートを保存"):
            # テンプレートの更新
            updated_template = {
                "name": template_name,
                "type": template_type,
                "description": template_desc,
                "sections": sections
            }
            
            if is_new:
                # 新規テンプレートの作成
                self.create_template(
                    name=template_name,
                    template_type=template_type,
                    sections=sections,
                    description=template_desc
                )
                st.success("新しいテンプレートが作成されました。")
            else:
                # 既存テンプレートの更新
                self.update_template(template_id, updated_template)
                st.success("テンプレートが更新されました。")
            
            # 編集状態をリセット
            st.session_state.editing_section = -1
        
        return template

    def _load_templates(self) -> Dict[str, Any]:
        """
        テンプレートファイルからテンプレート情報を読み込む
        
        Returns:
            テンプレートの辞書（キー: テンプレートID, 値: テンプレート情報）
        """
        templates = {}
        
        # キャッシュがある場合はキャッシュを使用
        if st.session_state.template_cache:
            return st.session_state.template_cache
        
        # テンプレートディレクトリ内のJSONファイルを読み込む
        if os.path.exists(self.template_dir):
            for filename in os.listdir(self.template_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.template_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            template = json.load(file)
                            template_id = template.get('id')
                            if template_id:
                                templates[template_id] = template
                    except Exception as e:
                        st.warning(f"テンプレートファイル '{filename}' の読み込みに失敗しました: {e}")
        
        # キャッシュの更新
        st.session_state.template_cache = templates
        
        return templates

    def _save_template(self, template: Dict[str, Any]) -> bool:
        """
        テンプレート情報をファイルに保存
        
        Args:
            template: 保存するテンプレート情報
            
        Returns:
            保存が成功したかどうか
        """
        try:
            template_id = template['id']
            file_path = os.path.join(self.template_dir, f"{template_id}.json")
            
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(template, file, ensure_ascii=False, indent=2)
            
            # キャッシュの更新
            st.session_state.template_cache[template_id] = template
            
            return True
        except Exception as e:
            st.error(f"テンプレートの保存に失敗しました: {e}")
            return False

    def _create_default_templates(self) -> None:
        """
        デフォルトのテンプレートを作成
        """
        # 標準分析レポートテンプレート
        self.create_template(
            name="標準分析レポート",
            template_type="標準分析レポート",
            sections=[
                {
                    "title": "セッション概要",
                    "type": "基本情報",
                    "content": "## {session_name}\n\n{session_description}",
                    "options": {
                        "show_date": True,
                        "show_location": True,
                        "show_boat_type": True,
                        "show_conditions": True
                    }
                },
                {
                    "title": "風向分析",
                    "type": "風向分析",
                    "content": "## 風向風速分析\n\nセッション中の風向風速データの分析結果です。",
                    "options": {
                        "show_charts": True,
                        "show_summary": True,
                        "show_details": False
                    }
                },
                {
                    "title": "パフォーマンス指標",
                    "type": "パフォーマンス指標",
                    "content": "## パフォーマンス分析\n\n速度、VMG、タック効率などのパフォーマンス指標です。",
                    "options": {
                        "show_charts": True,
                        "show_summary": True,
                        "show_details": True
                    }
                },
                {
                    "title": "戦略ポイント",
                    "type": "戦略ポイント分析",
                    "content": "## 戦略的判断ポイント\n\n重要な戦略ポイントとその評価です。",
                    "options": {
                        "show_timeline": True,
                        "show_map": True,
                        "min_importance": "all"
                    }
                },
                {
                    "title": "コースマップ",
                    "type": "マップビュー",
                    "content": "## セッションマップ\n\nGPSトラックとイベントポイントの可視化です。",
                    "options": {
                        "map_type": "標準マップ",
                        "show_track": True,
                        "show_points": True
                    }
                },
                {
                    "title": "改善提案",
                    "type": "改善提案",
                    "content": "## 改善提案\n\nデータ分析に基づく改善ポイントの提案です。",
                    "options": {
                        "show_data_quality": True,
                        "show_performance": True,
                        "show_strategy": True
                    }
                }
            ],
            description="標準的な分析レポートのテンプレートです。セッションの基本情報、風向分析、パフォーマンス指標、戦略ポイント、マップビュー、改善提案を含みます。"
        )
        
        # 簡易サマリーテンプレート
        self.create_template(
            name="簡易サマリー",
            template_type="簡易サマリー",
            sections=[
                {
                    "title": "セッション概要",
                    "type": "基本情報",
                    "content": "# {session_name}\n\n**日時**: {session_date}\n**場所**: {session_location}",
                    "options": {
                        "show_date": True,
                        "show_location": True,
                        "show_boat_type": False,
                        "show_conditions": True
                    }
                },
                {
                    "title": "主要指標",
                    "type": "パフォーマンス指標",
                    "content": "## 主要パフォーマンス指標\n\n* 平均速度: {avg_speed} kt\n* 最高速度: {max_speed} kt\n* 風上VMG: {upwind_vmg} kt\n* 風下VMG: {downwind_vmg} kt",
                    "options": {
                        "show_charts": False,
                        "show_summary": True,
                        "show_details": False
                    }
                },
                {
                    "title": "主要ポイント",
                    "type": "戦略ポイント分析",
                    "content": "## 主要戦略ポイント\n\n{strategy_points_summary}",
                    "options": {
                        "show_timeline": False,
                        "show_map": False,
                        "min_importance": "high"
                    }
                }
            ],
            description="簡潔なサマリーレポートのテンプレートです。基本情報と主要なパフォーマンス指標のみを含みます。"
        )
        
        # 詳細技術レポート
        self.create_template(
            name="詳細技術レポート",
            template_type="詳細技術レポート",
            sections=[
                {
                    "title": "基本情報",
                    "type": "基本情報",
                    "content": "# 詳細技術分析レポート: {session_name}\n\n**分析日時**: {report_date}\n**セッション日時**: {session_date}\n**分析者**: {analyst_name}",
                    "options": {
                        "show_date": True,
                        "show_location": True,
                        "show_boat_type": True,
                        "show_conditions": True
                    }
                },
                {
                    "title": "データ品質分析",
                    "type": "データ品質",
                    "content": "## データ品質メトリクス\n\nセッションデータの品質分析結果です。",
                    "options": {
                        "show_charts": True,
                        "show_summary": True,
                        "show_details": True
                    }
                },
                {
                    "title": "詳細風向分析",
                    "type": "風向分析",
                    "content": "## 詳細風向分析\n\nセッション中の風向風速データの詳細分析です。",
                    "options": {
                        "show_charts": True,
                        "show_summary": True,
                        "show_details": True
                    }
                },
                {
                    "title": "詳細パフォーマンス分析",
                    "type": "パフォーマンス指標",
                    "content": "## 詳細パフォーマンス分析\n\n速度、VMG、タック効率などの詳細なパフォーマンス指標です。",
                    "options": {
                        "show_charts": True,
                        "show_summary": True,
                        "show_details": True
                    }
                },
                {
                    "title": "戦略分析",
                    "type": "戦略ポイント分析",
                    "content": "## 詳細戦略分析\n\n戦略的判断ポイントの詳細分析です。",
                    "options": {
                        "show_timeline": True,
                        "show_map": True,
                        "min_importance": "all"
                    }
                },
                {
                    "title": "高度なマップ分析",
                    "type": "マップビュー",
                    "content": "## 詳細マップ分析\n\n様々なデータレイヤーを含む詳細なマップ分析です。",
                    "options": {
                        "map_type": "風向マップ",
                        "show_track": True,
                        "show_points": True
                    }
                },
                {
                    "title": "統計チャート",
                    "type": "統計チャート",
                    "content": "## 詳細統計分析\n\n詳細な統計チャートと分析結果です。",
                    "options": {
                        "show_velocity": True,
                        "show_vmg": True,
                        "show_angles": True,
                        "show_polar": True
                    }
                },
                {
                    "title": "技術的改善提案",
                    "type": "改善提案",
                    "content": "## 技術的改善提案\n\n詳細な分析に基づく技術的な改善提案です。",
                    "options": {
                        "show_data_quality": True,
                        "show_performance": True,
                        "show_strategy": True
                    }
                }
            ],
            description="詳細な技術分析レポートのテンプレートです。データ品質分析、詳細な風向分析、パフォーマンス指標、戦略分析、高度なマップ分析、統計チャート、技術的改善提案を含みます。"
        )

    def _format_datetime(self, datetime_str: str) -> str:
        """
        ISO形式の日時文字列を読みやすい形式に変換
        
        Args:
            datetime_str: ISO形式の日時文字列
            
        Returns:
            読みやすい形式の日時文字列
        """
        try:
            dt = datetime.datetime.fromisoformat(datetime_str)
            return dt.strftime("%Y年%m月%d日 %H:%M")
        except:
            return datetime_str
