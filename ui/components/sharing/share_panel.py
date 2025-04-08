"""
ui.components.sharing.share_panel

セッション結果の共有リンク生成と管理のためのUIコンポーネント
"""

import streamlit as st
import os
import datetime
from typing import List, Dict, Any, Optional, Callable, Union
import pyperclip
from urllib.parse import urljoin

from sailing_data_processor.project.session_model import SessionModel
from sailing_data_processor.sharing.link_manager import LinkManager


class SharePanelComponent:
    """
    共有パネルUIコンポーネント
    
    セッションやエクスポート結果の共有リンク生成と管理を行うUIを提供します。
    """
    
    def __init__(self, key: str = "share_panel", 
                 session_manager=None, 
                 link_manager: Optional[LinkManager] = None,
                 base_url: Optional[str] = None,
                 on_link_created: Optional[Callable[[str], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントの一意のキー, by default "share_panel"
        session_manager : optional
            セッションマネージャー, by default None
        link_manager : Optional[LinkManager], optional
            リンク管理クラスのインスタンス, by default None
        base_url : Optional[str], optional
            共有リンクのベースURL, by default None
        on_link_created : Optional[Callable[[str], None]], optional
            リンク作成時のコールバック関数, by default None
        """
        self.key = key
        self.session_manager = session_manager
        self.on_link_created = on_link_created
        
        # リンクマネージャーの初期化
        if link_manager is None:
            self.link_manager = LinkManager()
        else:
            self.link_manager = link_manager
        
        # 共有リンクのベースURL
        self.base_url = base_url or "http://localhost:8501"
        
        # ステート管理
        if f"{key}_selected_session" not in st.session_state:
            st.session_state[f"{key}_selected_session"] = None
        if f"{key}_expiration_days" not in st.session_state:
            st.session_state[f"{key}_expiration_days"] = 7
        if f"{key}_access_level" not in st.session_state:
            st.session_state[f"{key}_access_level"] = "view"
        if f"{key}_generated_link" not in st.session_state:
            st.session_state[f"{key}_generated_link"] = None
        if f"{key}_shared_file_path" not in st.session_state:
            st.session_state[f"{key}_shared_file_path"] = None
        if f"{key}_active_tab" not in st.session_state:
            st.session_state[f"{key}_active_tab"] = "create"
    
    def render(self, sessions: Optional[List[SessionModel]] = None, 
              file_path: Optional[str] = None, 
              session_id: Optional[str] = None,
              item_type: str = "session"):
        """
        共有パネルを表示
        
        Parameters
        ----------
        sessions : Optional[List[SessionModel]], optional
            共有可能なセッションリスト, by default None
            Noneの場合はセッションマネージャーから取得
        file_path : Optional[str], optional
            共有するファイルのパス, by default None
        session_id : Optional[str], optional
            共有するセッションID, by default None
        item_type : str, optional
            共有するアイテムの種類, by default "session"
            "session", "project", "export"のいずれか
        """
        st.header("共有パネル")
        
        # タブの表示
        tab1, tab2 = st.tabs(["共有リンク作成", "共有リンク管理"])
        
        # セッションの取得
        if sessions is None and self.session_manager is not None:
            try:
                sessions = self.session_manager.get_all_sessions()
            except:
                sessions = []
        
        if sessions is None:
            sessions = []
        
        # 共有リンク作成タブ
        with tab1:
            if st.session_state[f"{self.key}_active_tab"] != "create":
                st.session_state[f"{self.key}_active_tab"] = "create"
            self._render_create_link_tab(sessions, file_path, session_id, item_type)
        
        # 共有リンク管理タブ
        with tab2:
            if st.session_state[f"{self.key}_active_tab"] != "manage":
                st.session_state[f"{self.key}_active_tab"] = "manage"
            self._render_manage_links_tab()
    
    def _render_create_link_tab(self, sessions: List[SessionModel], 
                               file_path: Optional[str] = None,
                               session_id: Optional[str] = None,
                               item_type: str = "session"):
        """
        共有リンク作成タブを表示
        
        Parameters
        ----------
        sessions : List[SessionModel]
            共有可能なセッションリスト
        file_path : Optional[str], optional
            共有するファイルのパス, by default None
        session_id : Optional[str], optional
            共有するセッションID, by default None
        item_type : str, optional
            共有するアイテムの種類, by default "session"
        """
        st.subheader("共有リンクの作成")
        
        # 共有するアイテムの選択
        if item_type == "export" and file_path:
            # エクスポート結果ファイルの共有
            st.session_state[f"{self.key}_shared_file_path"] = file_path
            item_id = os.path.basename(file_path)
            st.write(f"エクスポートファイル: {os.path.basename(file_path)}")
        elif item_type == "session" and session_id:
            # 特定のセッションの共有
            item_id = session_id
            session_name = None
            
            # セッション名を取得
            for session in sessions:
                if session.session_id == session_id:
                    session_name = session.name
                    break
            
            if session_name:
                st.write(f"セッション: {session_name}")
            else:
                st.write(f"セッションID: {session_id}")
        else:
            # セッション選択UI
            if sessions:
                session_options = {s.session_id: f"{s.name} ({s.category})" for s in sessions}
                selected_session_id = st.selectbox(
                    "共有するセッションを選択",
                    options=list(session_options.keys()),
                    format_func=lambda x: session_options[x],
                    key=f"{self.key}_session_selector"
                )
                item_id = selected_session_id
                item_type = "session"
            else:
                st.warning("共有可能なセッションがありません。")
                return
        
        # 共有設定
        st.write("共有設定")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 有効期限の設定
            expiration_days = st.slider(
                "リンクの有効期限（日数）",
                min_value=1,
                max_value=30,
                value=st.session_state[f"{self.key}_expiration_days"],
                step=1,
                key=f"{self.key}_expiration_slider"
            )
            # 有効期限日を表示
            expiry_date = datetime.datetime.now() + datetime.timedelta(days=expiration_days)
            st.info(f"有効期限: {expiry_date.strftime('%Y年%m月%d日 %H:%M')}")
            
            # 有効期限を保存
            st.session_state[f"{self.key}_expiration_days"] = expiration_days
        
        with col2:
            # アクセスレベルの設定
            access_level = st.radio(
                "アクセスレベル",
                options=["view", "edit", "full"],
                format_func=lambda x: "閲覧のみ" if x == "view" else "編集可能" if x == "edit" else "フルアクセス",
                index=0 if st.session_state[f"{self.key}_access_level"] == "view" else 
                      1 if st.session_state[f"{self.key}_access_level"] == "edit" else 2,
                key=f"{self.key}_access_level"
            )
            
            # アクセスレベルを保存
            st.session_state[f"{self.key}_access_level"] = access_level
        
        # セキュリティの説明
        with st.expander("セキュリティについて"):
            st.write("""
            **共有リンクのセキュリティについて**
            
            - 共有リンクはランダムに生成されたIDを含むため、推測は困難です。
            - 有効期限を過ぎたリンクは自動的に無効になります。
            - アクセスレベルによって、閲覧者ができる操作を制限できます。
            - 共有が不要になった場合は、いつでもリンクを削除できます。
            """)
        
        # リンク生成ボタン
        if st.button("共有リンクを生成", key=f"{self.key}_generate_btn", type="primary"):
            self._generate_link(item_id, item_type, expiration_days, access_level)
        
        # 生成されたリンクの表示
        if st.session_state[f"{self.key}_generated_link"]:
            st.success("共有リンクが生成されました！")
            
            # リンク情報
            link_data = st.session_state[f"{self.key}_generated_link"]
            
            # リンクの表示
            st.code(link_data["url"], language=None)
            
            # コピーボタン
            if st.button("クリップボードにコピー", key=f"{self.key}_copy_btn"):
                try:
                    pyperclip.copy(link_data["url"])
                    st.success("リンクをクリップボードにコピーしました")
                except:
                    st.error("クリップボードへのコピーに失敗しました")
            
            # 共有オプション
            st.write("共有オプション")
            
            # メールで共有
            email_subject = f"セーリングデータ分析: {link_data['item_name']}の共有"
            email_body = f"""
            こんにちは、
            
            セーリングデータ分析の結果を共有します。
            
            {link_data['item_name']}
            
            下記のリンクからアクセスしてください：
            {link_data['url']}
            
            （このリンクは{link_data['expires_in']}日後に期限切れになります）
            """
            email_link = f"mailto:?subject={email_subject}&body={email_body}"
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"[メールで共有]({email_link})")
            with col2:
                # 埋め込みコード
                if st.button("埋め込みコードを表示", key=f"{self.key}_embed_btn"):
                    embed_code = f"""<iframe src="{link_data['url']}" width="800" height="600" frameborder="0"></iframe>"""
                    st.code(embed_code, language="html")
    
    def _render_manage_links_tab(self):
        """共有リンク管理タブを表示"""
        st.subheader("共有リンク管理")
        
        # 有効なリンクを取得
        active_links = self.link_manager.get_all_active_links()
        
        if not active_links:
            st.info("現在有効な共有リンクはありません。")
            return
        
        # リンク一覧の表示
        st.write(f"現在の有効な共有リンク: {len(active_links)}件")
        
        # リンクのフィルタリングオプション
        filter_options = ["すべて", "セッション", "プロジェクト", "エクスポート"]
        filter_selection = st.selectbox(
            "表示するリンクの種類",
            options=filter_options,
            index=0,
            key=f"{self.key}_filter"
        )
        
        # フィルタリング
        filtered_links = active_links
        if filter_selection != "すべて":
            item_type_map = {
                "セッション": "session",
                "プロジェクト": "project",
                "エクスポート": "export"
            }
            
            if filter_selection in item_type_map:
                filtered_links = [link for link in active_links if link["item_type"] == item_type_map[filter_selection]]
        
        # リンク一覧の表示
        for link in filtered_links:
            # リンク情報の取得
            link_id = link["link_id"]
            item_id = link["item_id"]
            item_type = link["item_type"]
            created_at = datetime.datetime.fromisoformat(link["created_at"])
            expires_at = datetime.datetime.fromisoformat(link["expires_at"])
            visit_count = link["visit_count"]
            
            # 残り日数の計算
            days_remaining = (expires_at - datetime.datetime.now()).days
            
            # リンクURL
            link_url = urljoin(self.base_url, f"shared/{link_id}")
            
            # リンク情報の表示
            with st.container():
                st.write("---")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # アイテム情報
                    item_type_display = {
                        "session": "セッション",
                        "project": "プロジェクト",
                        "export": "エクスポート"
                    }.get(item_type, item_type)
                    
                    st.write(f"**{item_type_display}**: {item_id}")
                    st.write(f"**リンク**: [{link_url}]({link_url})")
                    st.write(f"**作成日時**: {created_at.strftime('%Y/%m/%d %H:%M')}")
                    st.write(f"**有効期限**: {expires_at.strftime('%Y/%m/%d %H:%M')} (残り{days_remaining}日)")
                    st.write(f"**アクセス数**: {visit_count}回")
                
                with col2:
                    # 操作ボタン
                    if st.button("コピー", key=f"{self.key}_copy_{link_id}"):
                        try:
                            pyperclip.copy(link_url)
                            st.success("リンクをコピーしました")
                        except:
                            st.error("コピーに失敗しました")
                    
                    if st.button("延長", key=f"{self.key}_extend_{link_id}"):
                        # 延長日数の入力
                        extension_days = st.number_input(
                            "延長する日数",
                            min_value=1,
                            max_value=30,
                            value=7,
                            key=f"{self.key}_extend_days_{link_id}"
                        )
                        
                        if st.button("確定", key=f"{self.key}_confirm_extend_{link_id}"):
                            # リンクの延長
                            if self.link_manager.extend_link_expiration(link_id, extension_days):
                                st.success(f"リンクの有効期限を{extension_days}日延長しました")
                                st.experimental_rerun()
                            else:
                                st.error("リンクの延長に失敗しました")
                    
                    if st.button("削除", key=f"{self.key}_delete_{link_id}"):
                        if st.button("本当に削除しますか？", key=f"{self.key}_confirm_delete_{link_id}"):
                            # リンクの削除
                            if self.link_manager.delete_link(link_id):
                                st.success("リンクを削除しました")
                                st.experimental_rerun()
                            else:
                                st.error("リンクの削除に失敗しました")
                
                st.write("---")
    
    def _generate_link(self, item_id: str, item_type: str, expiration_days: int, access_level: str):
        """
        共有リンクを生成
        
        Parameters
        ----------
        item_id : str
            共有するアイテムのID
        item_type : str
            アイテムの種類
        expiration_days : int
            リンクの有効期限（日数）
        access_level : str
            アクセスレベル
        """
        try:
            # アクセス制限の設定
            access_restriction = {"level": access_level}
            
            # ファイルパスの取得
            file_path = st.session_state.get(f"{self.key}_shared_file_path")
            
            # リンクの作成
            link_id = self.link_manager.create_link(
                item_id=item_id, 
                item_type=item_type, 
                expiration_days=expiration_days, 
                access_restriction=access_restriction,
                file_path=file_path
            )
            
            if link_id:
                # リンクURLの生成
                link_url = urljoin(self.base_url, f"shared/{link_id}")
                
                # アイテム名の取得
                item_name = item_id
                if item_type == "session" and self.session_manager:
                    try:
                        session = self.session_manager.get_session(item_id)
                        if session:
                            item_name = session.name
                    except:
                        pass
                elif item_type == "export" and file_path:
                    item_name = os.path.basename(file_path)
                
                # リンク情報を保存
                link_info = {
                    "link_id": link_id,
                    "url": link_url,
                    "item_id": item_id,
                    "item_type": item_type,
                    "item_name": item_name,
                    "expires_in": expiration_days,
                    "access_level": access_level
                }
                
                st.session_state[f"{self.key}_generated_link"] = link_info
                
                # コールバック関数を呼び出し
                if self.on_link_created:
                    try:
                        self.on_link_created(link_id)
                    except Exception as e:
                        st.error(f"コールバック実行中にエラーが発生しました: {str(e)}")
                
                return True
            else:
                st.error("リンクの生成に失敗しました")
                return False
        
        except Exception as e:
            st.error(f"リンク生成中にエラーが発生しました: {str(e)}")
            return False
