"""
ui.components.reporting.notification.notification_panel

通知表示と管理のためのUIコンポーネント
"""

import streamlit as st
import datetime
from typing import Dict, List, Any, Optional, Callable, Union
import json

class NotificationPanel:
    """
    通知パネルクラス
    
    ユーザーの通知表示と管理のためのUIコンポーネントを提供します。
    """
    
    def __init__(self, key: str = "notification_panel", 
                 notification_manager=None, 
                 user_manager=None,
                 on_change: Optional[Callable[[str], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントの一意のキー, by default "notification_panel"
        notification_manager : object, optional
            通知管理オブジェクト, by default None
        user_manager : object, optional
            ユーザー管理オブジェクト, by default None
        on_change : Optional[Callable[[str], None]], optional
            変更時のコールバック関数, by default None
        """
        self.key = key
        self.notification_manager = notification_manager
        self.user_manager = user_manager
        self.on_change = on_change
        
        # セッション状態の初期化
        self._init_session_state()
    
    def _init_session_state(self):
        """セッション状態を初期化"""
        key_vars = {
            "active_tab": "center",  # "center" or "settings"
            "show_unread_only": False,
            "filter_event_type": "all",
            "filter_priority": "all",
            "page": 0,
            "page_size": 10,
            "selected_notification": None,
            "expanded_subscriptions": False
        }
        
        # 不足している状態変数を初期化
        for var_name, default_value in key_vars.items():
            state_key = f"{self.key}_{var_name}"
            if state_key not in st.session_state:
                st.session_state[state_key] = default_value
    
    def render(self, user_id: str, key_prefix: str = ""):
        """
        通知パネルを表示
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        key_prefix : str, optional
            キー接頭辞, by default ""
            
        Returns
        -------
        Dict[str, Any]
            変更されたプロパティ情報
        """
        st.markdown("### 通知パネル")
        
        changes = {}
        
        if not self.notification_manager:
            st.warning("通知管理システムが設定されていません。")
            return changes
        
        # 未読通知数の取得
        unread_count = self.notification_manager.get_unread_count(user_id)
        
        # タブの表示
        tab_labels = [
            f"通知センター ({unread_count}件の未読)" if unread_count > 0 else "通知センター",
            "通知設定"
        ]
        tab1, tab2 = st.tabs(tab_labels)
        
        with tab1:
            if st.session_state[f"{self.key}_active_tab"] != "center":
                st.session_state[f"{self.key}_active_tab"] = "center"
            
            center_changes = self._render_notification_center(user_id, key_prefix)
            changes.update(center_changes)
        
        with tab2:
            if st.session_state[f"{self.key}_active_tab"] != "settings":
                st.session_state[f"{self.key}_active_tab"] = "settings"
            
            settings_changes = self._render_notification_settings(user_id, key_prefix)
            changes.update(settings_changes)
        
        # コールバック呼び出し
        if changes and self.on_change:
            self.on_change("notification_settings_changed")
        
        return changes
    
    def _render_notification_center(self, user_id: str, key_prefix: str) -> Dict[str, Any]:
        """
        通知センターを表示
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        key_prefix : str
            キー接頭辞
            
        Returns
        -------
        Dict[str, Any]
            変更情報
        """
        changes = {}
        
        # フィルターエリア
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 未読フィルター
            show_unread_only = st.checkbox(
                "未読のみ表示", 
                value=st.session_state[f"{self.key}_show_unread_only"],
                key=f"{self.key}_unread_filter{key_prefix}"
            )
            
            if show_unread_only != st.session_state[f"{self.key}_show_unread_only"]:
                st.session_state[f"{self.key}_show_unread_only"] = show_unread_only
                st.session_state[f"{self.key}_page"] = 0  # ページをリセット
                changes["show_unread_only"] = show_unread_only
                st.experimental_rerun()
        
        with col2:
            # イベントタイプフィルター
            event_types = self._get_available_event_types(user_id)
            event_options = {"all": "すべて"}
            for e_type in event_types:
                # イベントタイプの日本語表示名
                display_name = {
                    "report_shared": "レポート共有",
                    "report_updated": "レポート更新",
                    "comment_added": "コメント追加",
                    "team_invitation": "チーム招待",
                    "analysis_completed": "分析完了",
                    "strategy_point_detected": "戦略ポイント検出"
                }.get(e_type, e_type)
                
                event_options[e_type] = display_name
            
            filter_event_type = st.selectbox(
                "イベントタイプ",
                options=list(event_options.keys()),
                format_func=lambda x: event_options[x],
                index=list(event_options.keys()).index(st.session_state[f"{self.key}_filter_event_type"]) 
                    if st.session_state[f"{self.key}_filter_event_type"] in event_options else 0,
                key=f"{self.key}_event_filter{key_prefix}"
            )
            
            if filter_event_type != st.session_state[f"{self.key}_filter_event_type"]:
                st.session_state[f"{self.key}_filter_event_type"] = filter_event_type
                st.session_state[f"{self.key}_page"] = 0  # ページをリセット
                changes["filter_event_type"] = filter_event_type
                st.experimental_rerun()
        
        with col3:
            # 優先度フィルター
            priority_options = {
                "all": "すべて",
                "high": "高",
                "normal": "普通",
                "low": "低"
            }
            
            filter_priority = st.selectbox(
                "優先度",
                options=list(priority_options.keys()),
                format_func=lambda x: priority_options[x],
                index=list(priority_options.keys()).index(st.session_state[f"{self.key}_filter_priority"]),
                key=f"{self.key}_priority_filter{key_prefix}"
            )
            
            if filter_priority != st.session_state[f"{self.key}_filter_priority"]:
                st.session_state[f"{self.key}_filter_priority"] = filter_priority
                st.session_state[f"{self.key}_page"] = 0  # ページをリセット
                changes["filter_priority"] = filter_priority
                st.experimental_rerun()
        
        # アクションボタン
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("すべて既読にする", key=f"{self.key}_mark_all_read{key_prefix}"):
                event_type = None
                if st.session_state[f"{self.key}_filter_event_type"] != "all":
                    event_type = st.session_state[f"{self.key}_filter_event_type"]
                
                count = self.notification_manager.mark_all_as_read(user_id, event_type)
                
                if count > 0:
                    st.success(f"{count}件の通知を既読にしました")
                    changes["marked_all_read"] = True
                    st.experimental_rerun()
                else:
                    st.info("既読にする未読通知はありませんでした")
        
        with col2:
            if st.button("既読の通知をクリア", key=f"{self.key}_clear_read{key_prefix}"):
                count = self.notification_manager.delete_all_notifications(
                    user_id, 
                    event_type=None if st.session_state[f"{self.key}_filter_event_type"] == "all" else st.session_state[f"{self.key}_filter_event_type"],
                    read_only=True
                )
                
                if count > 0:
                    st.success(f"{count}件の既読通知を削除しました")
                    changes["cleared_read"] = True
                    st.experimental_rerun()
                else:
                    st.info("削除する既読通知はありませんでした")
        
        # 通知の取得
        notifications = self._get_filtered_notifications(
            user_id, 
            unread_only=show_unread_only,
            event_type=None if filter_event_type == "all" else filter_event_type,
            priority=None if filter_priority == "all" else filter_priority
        )
        
        # 通知の表示
        if not notifications:
            st.info("表示する通知はありません")
            return changes
        
        # ページング
        page_size = st.session_state[f"{self.key}_page_size"]
        current_page = st.session_state[f"{self.key}_page"]
        total_pages = (len(notifications) - 1) // page_size + 1
        
        # ページに合わせて通知を取得
        start_idx = current_page * page_size
        end_idx = min(start_idx + page_size, len(notifications))
        page_notifications = notifications[start_idx:end_idx]
        
        # 通知の表示
        for notification in page_notifications:
            self._render_notification_item(notification, user_id, key_prefix)
        
        # ページングコントロール
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                if current_page > 0:
                    if st.button("前へ", key=f"{self.key}_prev_page{key_prefix}"):
                        st.session_state[f"{self.key}_page"] = current_page - 1
                        st.experimental_rerun()
            
            with col2:
                st.write(f"ページ {current_page + 1}/{total_pages} ({len(notifications)}件中 {start_idx + 1}-{end_idx}件を表示)")
            
            with col3:
                if current_page < total_pages - 1:
                    if st.button("次へ", key=f"{self.key}_next_page{key_prefix}"):
                        st.session_state[f"{self.key}_page"] = current_page + 1
                        st.experimental_rerun()
        
        return changes
    
    def _render_notification_settings(self, user_id: str, key_prefix: str) -> Dict[str, Any]:
        """
        通知設定を表示
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        key_prefix : str
            キー接頭辞
            
        Returns
        -------
        Dict[str, Any]
            変更情報
        """
        changes = {}
        
        st.subheader("通知設定")
        
        # 利用可能なイベントタイプの取得
        event_types = self._get_all_event_types()
        
        # ユーザーの購読設定の取得
        user_subscriptions = self.notification_manager.get_user_subscriptions(user_id)
        
        # イベントタイプごとの設定
        for event_type in event_types:
            # イベントタイプの表示名
            display_name = {
                "report_shared": "レポート共有",
                "report_updated": "レポート更新",
                "comment_added": "コメント追加",
                "team_invitation": "チーム招待",
                "analysis_completed": "分析完了",
                "strategy_point_detected": "戦略ポイント検出"
            }.get(event_type, event_type)
            
            # 現在の購読設定
            current_subscription = user_subscriptions.get(event_type, {})
            
            # デフォルト設定
            is_muted = current_subscription.get("muted", False)
            channels = current_subscription.get("channels", ["app"])
            has_subscription = event_type in user_subscriptions
            
            with st.expander(f"{display_name}", expanded=has_subscription):
                # 購読状態
                subscribe = st.checkbox(
                    "このイベントの通知を受け取る",
                    value=has_subscription,
                    key=f"{self.key}_subscribe_{event_type}{key_prefix}"
                )
                
                if subscribe != has_subscription:
                    if subscribe:
                        # 購読開始
                        self.notification_manager.subscribe_to_event(
                            user_id, event_type, channels=["app"]
                        )
                        changes[f"subscribe_{event_type}"] = True
                    else:
                        # 購読解除
                        self.notification_manager.unsubscribe_from_event(
                            user_id, event_type
                        )
                        changes[f"unsubscribe_{event_type}"] = True
                    
                    # 再読み込み
                    st.experimental_rerun()
                
                if has_subscription:
                    # ミュート設定
                    mute = st.checkbox(
                        "通知をミュート",
                        value=is_muted,
                        key=f"{self.key}_mute_{event_type}{key_prefix}"
                    )
                    
                    if mute != is_muted:
                        self.notification_manager.mute_event(
                            user_id, event_type, muted=mute
                        )
                        changes[f"mute_{event_type}"] = mute
                        st.experimental_rerun()
                    
                    # 通知チャネル
                    st.write("通知チャネル:")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        app_notify = st.checkbox(
                            "アプリ内通知",
                            value="app" in channels,
                            key=f"{self.key}_app_channel_{event_type}{key_prefix}"
                        )
                    
                    with col2:
                        email_notify = st.checkbox(
                            "メール通知",
                            value="email" in channels,
                            key=f"{self.key}_email_channel_{event_type}{key_prefix}"
                        )
                    
                    with col3:
                        slack_notify = st.checkbox(
                            "Slack通知",
                            value="slack" in channels,
                            key=f"{self.key}_slack_channel_{event_type}{key_prefix}"
                        )
                    
                    # チャネル設定の更新
                    new_channels = []
                    if app_notify:
                        new_channels.append("app")
                    if email_notify:
                        new_channels.append("email")
                    if slack_notify:
                        new_channels.append("slack")
                    
                    if set(new_channels) != set(channels):
                        # チャネル設定の保存
                        self.notification_manager.update_subscription(
                            user_id, event_type, {"channels": new_channels}
                        )
                        changes[f"channels_{event_type}"] = new_channels
                        st.experimental_rerun()
        
        # 通知クリーンアップ
        st.markdown("---")
        st.subheader("通知のクリーンアップ")
        
        max_age_days = st.slider(
            "通知を保持する期間（日数）",
            min_value=1,
            max_value=90,
            value=30,
            key=f"{self.key}_max_age_days{key_prefix}"
        )
        
        if st.button("古い通知を削除", key=f"{self.key}_clean_notifications{key_prefix}"):
            count = self.notification_manager.clean_old_notifications(max_age_days)
            
            if count > 0:
                st.success(f"{count}件の古い通知を削除しました")
                changes["cleaned_notifications"] = True
                st.experimental_rerun()
            else:
                st.info("削除する古い通知はありませんでした")
        
        return changes
    
    def _render_notification_item(self, notification: Dict[str, Any], user_id: str, key_prefix: str):
        """
        通知アイテムを表示
        
        Parameters
        ----------
        notification : Dict[str, Any]
            通知データ
        user_id : str
            ユーザーID
        key_prefix : str
            キー接頭辞
        """
        notification_id = notification.get("notification_id")
        is_read = notification.get("read", False)
        priority = notification.get("priority", "normal")
        event_type = notification.get("event_type", "unknown")
        created_at = notification.get("created_at")
        title = notification.get("title", "通知")
        body = notification.get("body", "")
        
        # 通知の表示スタイル
        if is_read:
            container_style = "background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 10px;"
        else:
            container_style = "background-color: #e6f7ff; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 4px solid #1890ff;"
        
        # 優先度に応じた表示
        priority_badge = ""
        if priority == "high":
            priority_badge = "🔴"
        elif priority == "low":
            priority_badge = "🔵"
        
        # 通知コンテナ
        with st.container():
            st.markdown(f'<div style="{container_style}">', unsafe_allow_html=True)
            
            # タイトル行（タイトル、時間、アクションボタン）
            col1, col2 = st.columns([5, 1])
            
            with col1:
                # タイムスタンプの表示
                if created_at:
                    try:
                        created_dt = datetime.datetime.fromisoformat(created_at)
                        time_display = created_dt.strftime("%Y/%m/%d %H:%M")
                    except:
                        time_display = created_at
                else:
                    time_display = ""
                
                # タイトルとバッジの表示
                title_line = f"{priority_badge} **{title}**"
                if not is_read:
                    title_line += " 🆕"
                
                st.markdown(title_line)
                st.caption(time_display)
            
            with col2:
                # アクションボタン
                action_col1, action_col2 = st.columns(2)
                
                with action_col1:
                    # 既読/未読トグル
                    if is_read:
                        if st.button("未読", key=f"{self.key}_unread_{notification_id}{key_prefix}", help="未読にマーク"):
                            # 未読に戻す実装があれば実行
                            st.experimental_rerun()
                    else:
                        if st.button("既読", key=f"{self.key}_read_{notification_id}{key_prefix}", help="既読にマーク"):
                            self.notification_manager.mark_as_read(notification_id, user_id)
                            st.experimental_rerun()
                
                with action_col2:
                    # 削除ボタン
                    if st.button("🗑️", key=f"{self.key}_delete_{notification_id}{key_prefix}", help="削除"):
                        self.notification_manager.delete_notification(notification_id, user_id)
                        st.experimental_rerun()
            
            # 本文の表示
            st.markdown(body)
            
            # イベントタイプの表示（小さく）
            event_type_display = {
                "report_shared": "レポート共有",
                "report_updated": "レポート更新",
                "comment_added": "コメント追加",
                "team_invitation": "チーム招待",
                "analysis_completed": "分析完了",
                "strategy_point_detected": "戦略ポイント検出"
            }.get(event_type, event_type)
            
            st.caption(f"イベントタイプ: {event_type_display}")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def _get_filtered_notifications(self, user_id: str, unread_only: bool = False, 
                                  event_type: str = None, priority: str = None) -> List[Dict[str, Any]]:
        """
        フィルタリングされた通知を取得
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        unread_only : bool, optional
            未読のみを表示するかどうか, by default False
        event_type : str, optional
            イベントタイプでフィルタリング, by default None
        priority : str, optional
            優先度でフィルタリング, by default None
            
        Returns
        -------
        List[Dict[str, Any]]
            通知のリスト
        """
        # フィルター条件の構築
        filters = {}
        if event_type:
            filters["event_type"] = event_type
        if priority:
            filters["priority"] = priority
        
        # 通知の取得
        return self.notification_manager.get_user_notifications(
            user_id, 
            filters=filters or None,
            limit=100,  # 実運用時は適切な値に調整
            unread_only=unread_only
        )
    
    def _get_available_event_types(self, user_id: str) -> List[str]:
        """
        ユーザーが受信した通知のイベントタイプを取得
        
        Parameters
        ----------
        user_id : str
            ユーザーID
            
        Returns
        -------
        List[str]
            イベントタイプのリスト
        """
        # すべての通知を取得
        notifications = self.notification_manager.get_user_notifications(
            user_id, limit=1000
        )
        
        # イベントタイプの抽出
        event_types = set()
        for notification in notifications:
            if "event_type" in notification:
                event_types.add(notification["event_type"])
        
        return sorted(list(event_types))
    
    def _get_all_event_types(self) -> List[str]:
        """
        すべてのイベントタイプを取得
        
        Returns
        -------
        List[str]
            イベントタイプのリスト
        """
        # 標準イベントタイプ（本来はシステムから取得）
        return [
            "report_shared",
            "report_updated",
            "comment_added",
            "team_invitation",
            "analysis_completed",
            "strategy_point_detected"
        ]


def notification_panel(notification_manager=None, user_manager=None,
                     user_id: str = "current_user",
                     on_change=None, key_prefix=""):
    """
    通知パネルを表示（簡易関数版）
    
    Parameters
    ----------
    notification_manager : object, optional
        通知管理オブジェクト, by default None
    user_manager : object, optional
        ユーザー管理オブジェクト, by default None
    user_id : str, optional
        ユーザーID, by default "current_user"
    on_change : Optional[Callable[[str], None]], optional
        変更時のコールバック, by default None
    key_prefix : str, optional
        キー接頭辞, by default ""
        
    Returns
    -------
    Dict[str, Any]
        変更されたプロパティ情報
    """
    panel = NotificationPanel(
        key=f"notification_panel_{key_prefix}",
        notification_manager=notification_manager,
        user_manager=user_manager,
        on_change=on_change
    )
    
    return panel.render(user_id, key_prefix=key_prefix)
