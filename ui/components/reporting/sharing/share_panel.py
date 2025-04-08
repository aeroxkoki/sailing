"""
ui.components.reporting.sharing.share_panel

レポート共有設定のためのUIコンポーネント
"""

import streamlit as st
import os
import datetime
from typing import Dict, List, Any, Optional, Callable, Union
import pyperclip
from urllib.parse import urljoin

class SharePanel:
    """
    共有設定パネルクラス
    
    レポートやデータの共有設定を行うためのUIコンポーネントを提供します。
    """
    
    def __init__(self, key: str = "share_panel", 
                 report_manager=None, 
                 user_manager=None,
                 share_manager=None,
                 on_change: Optional[Callable[[str], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントの一意のキー, by default "share_panel"
        report_manager : object, optional
            レポート管理オブジェクト, by default None
        user_manager : object, optional
            ユーザー管理オブジェクト, by default None
        share_manager : object, optional
            共有管理オブジェクト, by default None
        on_change : Optional[Callable[[str], None]], optional
            変更時のコールバック関数, by default None
        """
        self.key = key
        self.report_manager = report_manager
        self.user_manager = user_manager
        self.share_manager = share_manager
        self.on_change = on_change
        
        # セッション状態の初期化
        self._init_session_state()
    
    def _init_session_state(self):
        """セッション状態を初期化"""
        key_vars = {
            "selected_report": None,
            "share_type": "link",  # "link" or "user"
            "selected_users": [],
            "selected_groups": [],
            "permission": "view",
            "expiration_days": 7,
            "access_limit": None,
            "require_password": False,
            "password": "",
            "custom_message": "",
            "generated_link": None,
            "show_history": False,
            "filtered_users": [],
            "search_term": "",
            "active_tab": "create"
        }
        
        # 不足している状態変数を初期化
        for var_name, default_value in key_vars.items():
            state_key = f"{self.key}_{var_name}"
            if state_key not in st.session_state:
                st.session_state[state_key] = default_value
    
    def render(self, reports: List[Dict[str, Any]] = None, 
               report_id: str = None, key_prefix: str = ""):
        """
        共有設定パネルを表示
        
        Parameters
        ----------
        reports : List[Dict[str, Any]], optional
            共有可能なレポートリスト, by default None
        report_id : str, optional
            選択するレポートID, by default None
        key_prefix : str, optional
            キー接頭辞, by default ""
            
        Returns
        -------
        Dict[str, Any]
            変更されたプロパティ情報
        """
        st.markdown("### レポート共有設定")
        
        changes = {}
        
        # レポートの取得
        if reports is None and self.report_manager is not None:
            try:
                reports = self.report_manager.get_reports()
            except Exception as e:
                st.error(f"レポートの取得に失敗しました: {str(e)}")
                reports = []
        
        if not reports:
            st.info("共有可能なレポートがありません。")
            return changes
        
        # レポート選択
        if report_id:
            # 特定のレポートIDが指定された場合
            report_name = None
            for report in reports:
                if report["id"] == report_id:
                    report_name = report["title"]
                    break
            
            st.session_state[f"{self.key}_selected_report"] = report_id
            st.write(f"レポート: {report_name or report_id}")
        else:
            # レポートを選択する場合
            report_options = {r["id"]: r["title"] for r in reports}
            selected_report_id = st.selectbox(
                "共有するレポート",
                options=list(report_options.keys()),
                format_func=lambda x: report_options[x],
                key=f"{self.key}_report_select{key_prefix}"
            )
            
            if selected_report_id:
                st.session_state[f"{self.key}_selected_report"] = selected_report_id
        
        selected_report_id = st.session_state[f"{self.key}_selected_report"]
        if not selected_report_id:
            st.warning("レポートを選択してください。")
            return changes
        
        # 共有タイプを選択（タブで表示）
        tab1, tab2 = st.tabs(["リンク共有", "ユーザー/グループ共有"])
        
        with tab1:
            if st.session_state[f"{self.key}_share_type"] != "link":
                st.session_state[f"{self.key}_share_type"] = "link"
            
            link_changes = self._render_link_share_tab(selected_report_id, key_prefix)
            changes.update(link_changes)
        
        with tab2:
            if st.session_state[f"{self.key}_share_type"] != "user":
                st.session_state[f"{self.key}_share_type"] = "user"
            
            user_changes = self._render_user_share_tab(selected_report_id, key_prefix)
            changes.update(user_changes)
        
        # 共有状況表示（共通エリア）
        if st.checkbox(
            "共有履歴を表示", 
            value=st.session_state[f"{self.key}_show_history"],
            key=f"{self.key}_show_history_check{key_prefix}"
        ):
            st.session_state[f"{self.key}_show_history"] = True
            self._render_share_history(selected_report_id, key_prefix)
        else:
            st.session_state[f"{self.key}_show_history"] = False
        
        # コールバック呼び出し
        if changes and self.on_change:
            self.on_change("share_settings_changed")
        
        return changes
    
    def _render_link_share_tab(self, report_id: str, key_prefix: str) -> Dict[str, Any]:
        """
        リンク共有タブを表示
        
        Parameters
        ----------
        report_id : str
            レポートID
        key_prefix : str
            キー接頭辞
            
        Returns
        -------
        Dict[str, Any]
            変更情報
        """
        changes = {}
        
        # すでに生成されたリンクの表示
        generated_link = st.session_state.get(f"{self.key}_generated_link")
        if generated_link:
            st.success("共有リンクが生成されています")
            st.code(generated_link["url"], language=None)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("クリップボードにコピー", key=f"{self.key}_copy_link{key_prefix}"):
                    try:
                        pyperclip.copy(generated_link["url"])
                        st.success("リンクをコピーしました")
                    except Exception as e:
                        st.error(f"リンクのコピーに失敗しました: {str(e)}")
            
            with col2:
                if st.button("新しいリンクを作成", key=f"{self.key}_new_link{key_prefix}"):
                    st.session_state[f"{self.key}_generated_link"] = None
                    st.experimental_rerun()
        
        else:
            # リンク設定
            st.subheader("リンク共有設定")
            
            # 権限設定
            col1, col2 = st.columns(2)
            
            with col1:
                permission = st.radio(
                    "アクセス権限",
                    options=["view", "comment", "edit"],
                    format_func=lambda x: "閲覧のみ" if x == "view" else 
                                         "コメント可能" if x == "comment" else "編集可能",
                    index=["view", "comment", "edit"].index(st.session_state[f"{self.key}_permission"]),
                    key=f"{self.key}_permission_radio{key_prefix}"
                )
                
                st.session_state[f"{self.key}_permission"] = permission
                changes["permission"] = permission
            
            with col2:
                expiration_days = st.slider(
                    "有効期限（日数）",
                    min_value=1,
                    max_value=90,
                    value=st.session_state[f"{self.key}_expiration_days"],
                    key=f"{self.key}_expiration_slider{key_prefix}"
                )
                
                expiry_date = datetime.datetime.now() + datetime.timedelta(days=expiration_days)
                st.info(f"有効期限: {expiry_date.strftime('%Y年%m月%d日 %H:%M')}")
                
                st.session_state[f"{self.key}_expiration_days"] = expiration_days
                changes["expiration_days"] = expiration_days
            
            # 追加設定
            with st.expander("詳細設定"):
                # アクセス回数制限
                use_access_limit = st.checkbox(
                    "アクセス回数を制限する",
                    value=st.session_state[f"{self.key}_access_limit"] is not None,
                    key=f"{self.key}_use_access_limit{key_prefix}"
                )
                
                if use_access_limit:
                    access_limit = st.number_input(
                        "最大アクセス回数",
                        min_value=1,
                        value=st.session_state[f"{self.key}_access_limit"] or 10,
                        key=f"{self.key}_access_limit_input{key_prefix}"
                    )
                    st.session_state[f"{self.key}_access_limit"] = access_limit
                    changes["access_limit"] = access_limit
                else:
                    st.session_state[f"{self.key}_access_limit"] = None
                    changes["access_limit"] = None
                
                # パスワード保護
                require_password = st.checkbox(
                    "パスワードで保護する",
                    value=st.session_state[f"{self.key}_require_password"],
                    key=f"{self.key}_require_password{key_prefix}"
                )
                
                if require_password:
                    password = st.text_input(
                        "パスワード",
                        type="password",
                        value=st.session_state[f"{self.key}_password"],
                        key=f"{self.key}_password_input{key_prefix}"
                    )
                    st.session_state[f"{self.key}_password"] = password
                    changes["password"] = password
                else:
                    st.session_state[f"{self.key}_require_password"] = False
                    st.session_state[f"{self.key}_password"] = ""
                    changes["password"] = None
                
                # 共有メッセージ
                custom_message = st.text_area(
                    "共有メッセージ",
                    value=st.session_state[f"{self.key}_custom_message"],
                    key=f"{self.key}_custom_message{key_prefix}",
                    placeholder="受信者に表示されるメッセージを入力してください..."
                )
                
                st.session_state[f"{self.key}_custom_message"] = custom_message
                changes["custom_message"] = custom_message
            
            # リンク生成ボタン
            if st.button("共有リンクを生成", key=f"{self.key}_generate_link{key_prefix}", type="primary"):
                if self.share_manager:
                    try:
                        # 共有リンクの作成
                        link_id = self.share_manager.generate_share_link(
                            item_id=report_id,
                            permission=permission,
                            expiration_days=expiration_days,
                            access_limit=st.session_state[f"{self.key}_access_limit"],
                            password=st.session_state[f"{self.key}_password"] if require_password else None,
                            custom_settings={"message": custom_message} if custom_message else None
                        )
                        
                        if link_id:
                            # リンク情報を取得
                            link_info = self.share_manager.get_share_link(link_id)
                            
                            # 表示用のURL生成
                            base_url = "http://localhost:8501"  # 実際の環境に応じて変更
                            link_url = urljoin(base_url, f"shared/{link_id}")
                            
                            # 生成されたリンク情報を保存
                            st.session_state[f"{self.key}_generated_link"] = {
                                "id": link_id,
                                "url": link_url,
                                "expires": link_info.get("expiration"),
                                "permission": permission
                            }
                            
                            st.success("共有リンクを生成しました")
                            st.experimental_rerun()
                        else:
                            st.error("リンクの生成に失敗しました")
                    except Exception as e:
                        st.error(f"リンク生成中にエラーが発生しました: {str(e)}")
                else:
                    st.error("共有マネージャーが設定されていません")
        
        return changes
    
    def _render_user_share_tab(self, report_id: str, key_prefix: str) -> Dict[str, Any]:
        """
        ユーザー/グループ共有タブを表示
        
        Parameters
        ----------
        report_id : str
            レポートID
        key_prefix : str
            キー接頭辞
            
        Returns
        -------
        Dict[str, Any]
            変更情報
        """
        changes = {}
        
        st.subheader("ユーザー/グループ共有設定")
        
        # ユーザー検索/選択
        search_term = st.text_input(
            "ユーザーまたはグループを検索",
            value=st.session_state[f"{self.key}_search_term"],
            key=f"{self.key}_user_search{key_prefix}",
            placeholder="名前またはメールアドレスを入力..."
        )
        
        st.session_state[f"{self.key}_search_term"] = search_term
        
        # ユーザーリストを取得
        users = []
        groups = []
        
        if self.user_manager:
            if search_term:
                try:
                    # ユーザーとグループを検索
                    users = self.user_manager.search_users(search_term)
                    groups = self.user_manager.search_groups(search_term)
                except Exception as e:
                    st.error(f"ユーザー検索中にエラーが発生しました: {str(e)}")
            else:
                try:
                    # 最新のユーザーとグループを取得
                    users = self.user_manager.get_recent_users(limit=10)
                    groups = self.user_manager.get_groups(limit=5)
                except Exception as e:
                    st.error(f"ユーザー取得中にエラーが発生しました: {str(e)}")
        else:
            # テスト用のダミーデータ
            users = [
                {"id": "user1", "name": "テストユーザー1", "email": "user1@example.com"},
                {"id": "user2", "name": "テストユーザー2", "email": "user2@example.com"},
                {"id": "user3", "name": "テストユーザー3", "email": "user3@example.com"}
            ]
            groups = [
                {"id": "group1", "name": "開発チーム", "member_count": 5},
                {"id": "group2", "name": "マーケティングチーム", "member_count": 3}
            ]
        
        # 選択済みのユーザーとグループID
        selected_users = st.session_state[f"{self.key}_selected_users"]
        selected_groups = st.session_state[f"{self.key}_selected_groups"]
        
        # 共有先の選択UI（2カラム表示）
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("ユーザー")
            
            # 選択済みユーザーの表示/削除
            if selected_users:
                for user_id in list(selected_users):  # コピーを作成して反復中の削除を可能に
                    user_name = None
                    user_email = None
                    
                    # ユーザー情報を検索
                    for user in users:
                        if user["id"] == user_id:
                            user_name = user["name"]
                            user_email = user.get("email")
                            break
                    
                    # 選択済みユーザーの表示（削除ボタン付き）
                    user_col, btn_col = st.columns([4, 1])
                    with user_col:
                        display_name = user_name or user_id
                        if user_email:
                            display_name += f" ({user_email})"
                        st.text(display_name)
                    
                    with btn_col:
                        if st.button("削除", key=f"{self.key}_remove_user_{user_id}{key_prefix}"):
                            selected_users.remove(user_id)
                            changes["selected_users"] = selected_users
                            st.experimental_rerun()
            
            # 検索結果からのユーザー追加
            if users:
                st.markdown("---")
                st.markdown("ユーザーを追加:")
                
                for user in users:
                    if user["id"] not in selected_users:
                        user_col, btn_col = st.columns([4, 1])
                        with user_col:
                            display_name = user["name"]
                            if "email" in user:
                                display_name += f" ({user['email']})"
                            st.text(display_name)
                        
                        with btn_col:
                            if st.button("追加", key=f"{self.key}_add_user_{user['id']}{key_prefix}"):
                                selected_users.append(user["id"])
                                st.session_state[f"{self.key}_selected_users"] = selected_users
                                changes["selected_users"] = selected_users
                                st.experimental_rerun()
        
        with col2:
            st.subheader("グループ")
            
            # 選択済みグループの表示/削除
            if selected_groups:
                for group_id in list(selected_groups):  # コピーを作成して反復中の削除を可能に
                    group_name = None
                    member_count = None
                    
                    # グループ情報を検索
                    for group in groups:
                        if group["id"] == group_id:
                            group_name = group["name"]
                            member_count = group.get("member_count")
                            break
                    
                    # 選択済みグループの表示（削除ボタン付き）
                    group_col, btn_col = st.columns([4, 1])
                    with group_col:
                        display_name = group_name or group_id
                        if member_count:
                            display_name += f" ({member_count}名)"
                        st.text(display_name)
                    
                    with btn_col:
                        if st.button("削除", key=f"{self.key}_remove_group_{group_id}{key_prefix}"):
                            selected_groups.remove(group_id)
                            st.session_state[f"{self.key}_selected_groups"] = selected_groups
                            changes["selected_groups"] = selected_groups
                            st.experimental_rerun()
            
            # 検索結果からのグループ追加
            if groups:
                st.markdown("---")
                st.markdown("グループを追加:")
                
                for group in groups:
                    if group["id"] not in selected_groups:
                        group_col, btn_col = st.columns([4, 1])
                        with group_col:
                            display_name = group["name"]
                            if "member_count" in group:
                                display_name += f" ({group['member_count']}名)"
                            st.text(display_name)
                        
                        with btn_col:
                            if st.button("追加", key=f"{self.key}_add_group_{group['id']}{key_prefix}"):
                                selected_groups.append(group["id"])
                                st.session_state[f"{self.key}_selected_groups"] = selected_groups
                                changes["selected_groups"] = selected_groups
                                st.experimental_rerun()
        
        # 共有権限設定
        st.markdown("---")
        st.subheader("共有設定")
        
        # 権限設定
        permission = st.radio(
            "アクセス権限",
            options=["view", "comment", "edit"],
            format_func=lambda x: "閲覧のみ" if x == "view" else 
                                "コメント可能" if x == "comment" else "編集可能",
            index=["view", "comment", "edit"].index(st.session_state[f"{self.key}_permission"]),
            key=f"{self.key}_user_permission_radio{key_prefix}"
        )
        
        st.session_state[f"{self.key}_permission"] = permission
        changes["permission"] = permission
        
        # 有効期限の設定
        use_expiration = st.checkbox(
            "有効期限を設定する",
            value=st.session_state[f"{self.key}_expiration_days"] is not None,
            key=f"{self.key}_use_expiration{key_prefix}"
        )
        
        if use_expiration:
            expiration_days = st.slider(
                "有効期限（日数）",
                min_value=1,
                max_value=365,
                value=st.session_state[f"{self.key}_expiration_days"] or 30,
                key=f"{self.key}_user_expiration_slider{key_prefix}"
            )
            
            expiry_date = datetime.datetime.now() + datetime.timedelta(days=expiration_days)
            st.info(f"有効期限: {expiry_date.strftime('%Y年%m月%d日 %H:%M')}")
            
            st.session_state[f"{self.key}_expiration_days"] = expiration_days
            changes["expiration_days"] = expiration_days
        else:
            st.session_state[f"{self.key}_expiration_days"] = None
            changes["expiration_days"] = None
        
        # 通知メッセージ
        custom_message = st.text_area(
            "共有メッセージ",
            value=st.session_state[f"{self.key}_custom_message"],
            key=f"{self.key}_user_custom_message{key_prefix}",
            placeholder="受信者に表示される通知メッセージを入力してください..."
        )
        
        st.session_state[f"{self.key}_custom_message"] = custom_message
        changes["custom_message"] = custom_message
        
        # 共有ボタン
        if (selected_users or selected_groups) and st.button("共有を実行", key=f"{self.key}_share_execute{key_prefix}", type="primary"):
            if self.share_manager:
                shared_count = 0
                
                try:
                    # ユーザーへの共有
                    for user_id in selected_users:
                        share_id = self.share_manager.share_item(
                            item_id=report_id,
                            user_id=user_id,
                            permission=permission,
                            expiration=datetime.datetime.now() + datetime.timedelta(days=expiration_days) if expiration_days else None,
                            custom_settings={"message": custom_message} if custom_message else None
                        )
                        
                        if share_id:
                            shared_count += 1
                    
                    # グループへの共有
                    for group_id in selected_groups:
                        share_id = self.share_manager.share_item(
                            item_id=report_id,
                            group_id=group_id,
                            permission=permission,
                            expiration=datetime.datetime.now() + datetime.timedelta(days=expiration_days) if expiration_days else None,
                            custom_settings={"message": custom_message} if custom_message else None
                        )
                        
                        if share_id:
                            shared_count += 1
                    
                    # 成功メッセージ
                    user_count = len(selected_users)
                    group_count = len(selected_groups)
                    
                    success_msg = f"{shared_count}件の共有を実行しました。"
                    if user_count > 0:
                        success_msg += f" {user_count}名のユーザー"
                    if group_count > 0:
                        if user_count > 0:
                            success_msg += f"と{group_count}個のグループ"
                        else:
                            success_msg += f" {group_count}個のグループ"
                    
                    st.success(success_msg)
                    
                    # 選択をクリア
                    st.session_state[f"{self.key}_selected_users"] = []
                    st.session_state[f"{self.key}_selected_groups"] = []
                    changes["share_executed"] = True
                    
                    # 少し待ってから再読み込み
                    from time import sleep
                    sleep(0.5)
                    st.experimental_rerun()
                    
                except Exception as e:
                    st.error(f"共有処理中にエラーが発生しました: {str(e)}")
            else:
                st.error("共有マネージャーが設定されていません")
        
        return changes
    
    def _render_share_history(self, report_id: str, key_prefix: str):
        """
        共有履歴を表示
        
        Parameters
        ----------
        report_id : str
            レポートID
        key_prefix : str
            キー接頭辞
        """
        st.subheader("共有履歴")
        
        if not self.share_manager:
            st.info("共有マネージャーが設定されていないため、履歴を表示できません。")
            return
        
        try:
            # 共有履歴の取得
            history = self.share_manager.get_item_share_history(report_id)
            
            if not history:
                st.info("このレポートはまだ共有されていません。")
                return
            
            # 共有履歴を表示
            for entry in history:
                with st.container():
                    # 日時
                    timestamp = datetime.datetime.fromisoformat(entry["timestamp"])
                    timestamp_str = timestamp.strftime("%Y/%m/%d %H:%M:%S")
                    
                    # アクション
                    action = entry["action"]
                    action_display = {
                        "shared": "共有",
                        "share_revoked": "共有取り消し",
                        "link_created": "リンク作成",
                        "link_accessed": "リンクアクセス",
                        "link_revoked": "リンク取り消し",
                        "link_extended": "リンク延長",
                        "link_disabled": "リンク無効化",
                        "link_updated": "リンク更新",
                        "share_updated": "共有更新"
                    }.get(action, action)
                    
                    # 詳細情報
                    details = entry.get("details", {})
                    user_id = entry.get("user_id", "不明")
                    
                    # ユーザー名（ユーザーマネージャーがあれば解決）
                    user_name = user_id
                    if self.user_manager:
                        try:
                            user_info = self.user_manager.get_user(user_id)
                            if user_info:
                                user_name = user_info.get("name", user_id)
                        except:
                            pass
                    
                    # 表示内容の生成
                    if action == "shared":
                        target_id = details.get("user_id") or details.get("group_id")
                        target_type = "ユーザー" if details.get("user_id") else "グループ"
                        target_name = target_id
                        
                        # 名前解決（ユーザーマネージャーがあれば）
                        if self.user_manager:
                            try:
                                if details.get("user_id"):
                                    target_info = self.user_manager.get_user(target_id)
                                    if target_info:
                                        target_name = target_info.get("name", target_id)
                                elif details.get("group_id"):
                                    target_info = self.user_manager.get_group(target_id)
                                    if target_info:
                                        target_name = target_info.get("name", target_id)
                            except:
                                pass
                        
                        display_text = f"{user_name} が {target_type} **{target_name}** に"
                        display_text += f"権限 **{details.get('permission', '不明')}** で共有しました"
                    
                    elif action == "share_revoked":
                        target_id = details.get("user_id") or details.get("group_id")
                        target_type = "ユーザー" if details.get("user_id") else "グループ"
                        display_text = f"{user_name} が {target_type} **{target_id}** との共有を取り消しました"
                    
                    elif action == "link_created":
                        display_text = f"{user_name} が共有リンク（権限: **{details.get('permission', '不明')}**）を作成しました"
                    
                    elif action == "link_accessed":
                        display_text = f"共有リンク **{details.get('link_id', '不明')}** がアクセスされました（合計 {details.get('access_count', '不明')} 回）"
                    
                    elif action == "link_revoked":
                        display_text = f"{user_name} が共有リンク **{details.get('link_id', '不明')}** を無効化しました"
                    
                    elif action == "link_extended":
                        display_text = f"{user_name} が共有リンク **{details.get('link_id', '不明')}** の有効期限を {details.get('extended_days', '不明')} 日延長しました"
                    
                    else:
                        display_text = f"{action_display}: {json.dumps(details)}"
                    
                    # 履歴エントリの表示
                    st.markdown(f"**{timestamp_str}**: {display_text}")
            
            # 履歴の終わりを示すマーカー
            st.markdown("---")
        
        except Exception as e:
            st.error(f"共有履歴の取得中にエラーが発生しました: {str(e)}")


def share_panel(report_manager=None, user_manager=None, share_manager=None,
               on_change=None, key_prefix=""):
    """
    共有設定パネルを表示（簡易関数版）
    
    Parameters
    ----------
    report_manager : object, optional
        レポート管理オブジェクト, by default None
    user_manager : object, optional
        ユーザー管理オブジェクト, by default None
    share_manager : object, optional
        共有管理オブジェクト, by default None
    on_change : Optional[Callable[[str], None]], optional
        変更時のコールバック, by default None
    key_prefix : str, optional
        キー接頭辞, by default ""
        
    Returns
    -------
    Dict[str, Any]
        変更されたプロパティ情報
    """
    panel = SharePanel(
        key=f"share_panel_{key_prefix}",
        report_manager=report_manager,
        user_manager=user_manager,
        share_manager=share_manager,
        on_change=on_change
    )
    
    return panel.render(key_prefix=key_prefix)
