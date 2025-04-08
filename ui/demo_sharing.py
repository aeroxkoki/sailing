"""
ui.demo_sharing

セーリング戦略分析システムの共有機能と通知機能のデモアプリケーション
"""

import streamlit as st
import sys
import os
import datetime
import json
from pathlib import Path
import uuid

# リポジトリのルートディレクトリをPythonパスに追加
repo_root = Path(__file__).parent.parent
sys.path.append(str(repo_root))

# カスタムモジュールのインポート
from sailing_data_processor.reporting.sharing.share_manager import ShareManager
from sailing_data_processor.reporting.sharing.permission_manager import PermissionManager
from sailing_data_processor.reporting.notification.notification_manager import NotificationManager
from sailing_data_processor.reporting.notification.notification_templates import NotificationTemplateManager
from ui.components.reporting.sharing.share_panel import SharePanel
from ui.components.reporting.notification.notification_panel import NotificationPanel

class DemoReportManager:
    """シンプルなレポート管理のデモクラス"""
    
    def __init__(self):
        # サンプルレポートデータ
        self.reports = [
            {"id": "report1", "title": "2024年春季レガッタ分析", "description": "春季レガッタのセーリング分析レポート", "created_at": "2024-04-01"},
            {"id": "report2", "title": "トレーニングセッション評価", "description": "4月第2週のトレーニングデータ分析", "created_at": "2024-04-10"},
            {"id": "report3", "title": "風向変化パターン分析", "description": "湾内の風向変化パターンの詳細分析", "created_at": "2024-04-15"},
            {"id": "report4", "title": "スタート戦術の最適化", "description": "様々な風条件下でのスタート戦術分析", "created_at": "2024-04-20"}
        ]
    
    def get_reports(self):
        """レポート一覧を取得"""
        return self.reports
    
    def get_report(self, report_id):
        """特定のレポートを取得"""
        for report in self.reports:
            if report["id"] == report_id:
                return report
        return None

class DemoUserManager:
    """シンプルなユーザー管理のデモクラス"""
    
    def __init__(self):
        # サンプルユーザーデータ
        self.users = [
            {"id": "user1", "name": "山田太郎", "email": "yamada@example.com", "role": "coach"},
            {"id": "user2", "name": "佐藤花子", "email": "sato@example.com", "role": "athlete"},
            {"id": "user3", "name": "鈴木一郎", "email": "suzuki@example.com", "role": "athlete"},
            {"id": "user4", "name": "田中誠", "email": "tanaka@example.com", "role": "analyst"}
        ]
        
        # サンプルグループデータ
        self.groups = [
            {"id": "group1", "name": "コーチングチーム", "description": "コーチとアナリスト", "members": ["user1", "user4"]},
            {"id": "group2", "name": "アスリートチーム", "description": "競技選手", "members": ["user2", "user3"]}
        ]
    
    def get_user(self, user_id):
        """ユーザー情報を取得"""
        for user in self.users:
            if user["id"] == user_id:
                return user
        return None
    
    def get_group(self, group_id):
        """グループ情報を取得"""
        for group in self.groups:
            if group["id"] == group_id:
                return group
        return None
    
    def search_users(self, query):
        """ユーザーを検索"""
        query = query.lower()
        return [u for u in self.users 
                if query in u["name"].lower() or 
                query in u.get("email", "").lower()]
    
    def search_groups(self, query):
        """グループを検索"""
        query = query.lower()
        return [g for g in self.groups 
                if query in g["name"].lower() or 
                query in g.get("description", "").lower()]
    
    def get_recent_users(self, limit=10):
        """最近のユーザーを取得"""
        return self.users[:limit]
    
    def get_groups(self, limit=10):
        """グループを取得"""
        return self.groups[:limit]
    
    def user_exists(self, user_id):
        """ユーザーが存在するか確認"""
        return any(u["id"] == user_id for u in self.users)
    
    def get_current_user(self):
        """現在のユーザーIDを取得"""
        return st.session_state.get("user_id", "user1")

class DemoStorageManager:
    """シンプルなストレージ管理のデモクラス"""
    
    def __init__(self, storage_dir="./.demo_data"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # サブディレクトリの作成
        self.share_dir = os.path.join(storage_dir, "shares")
        self.notification_dir = os.path.join(storage_dir, "notifications")
        
        os.makedirs(self.share_dir, exist_ok=True)
        os.makedirs(self.notification_dir, exist_ok=True)
        
        # データキャッシュ
        self._share_settings = {}
        self._share_links = {}
        self._share_history = {}
        self._notifications = {}
        self._subscriptions = {}
        
        # 初期データの読み込み
        self._load_data()
    
    def _load_data(self):
        """保存されたデータを読み込む"""
        # 共有設定
        share_settings_path = os.path.join(self.share_dir, "share_settings.json")
        if os.path.exists(share_settings_path):
            try:
                with open(share_settings_path, "r", encoding="utf-8") as f:
                    self._share_settings = json.load(f)
            except Exception as e:
                print(f"Error loading share settings: {e}")
        
        # 共有リンク
        share_links_path = os.path.join(self.share_dir, "share_links.json")
        if os.path.exists(share_links_path):
            try:
                with open(share_links_path, "r", encoding="utf-8") as f:
                    self._share_links = json.load(f)
            except Exception as e:
                print(f"Error loading share links: {e}")
        
        # 共有履歴
        share_history_path = os.path.join(self.share_dir, "share_history.json")
        if os.path.exists(share_history_path):
            try:
                with open(share_history_path, "r", encoding="utf-8") as f:
                    self._share_history = json.load(f)
            except Exception as e:
                print(f"Error loading share history: {e}")
        
        # 通知
        notifications_path = os.path.join(self.notification_dir, "notifications.json")
        if os.path.exists(notifications_path):
            try:
                with open(notifications_path, "r", encoding="utf-8") as f:
                    self._notifications = json.load(f)
            except Exception as e:
                print(f"Error loading notifications: {e}")
        
        # 購読設定
        subscriptions_path = os.path.join(self.notification_dir, "subscriptions.json")
        if os.path.exists(subscriptions_path):
            try:
                with open(subscriptions_path, "r", encoding="utf-8") as f:
                    self._subscriptions = json.load(f)
            except Exception as e:
                print(f"Error loading subscriptions: {e}")
    
    def save_share_settings(self, share_settings):
        """共有設定を保存"""
        self._share_settings = share_settings
        share_settings_path = os.path.join(self.share_dir, "share_settings.json")
        try:
            with open(share_settings_path, "w", encoding="utf-8") as f:
                json.dump(share_settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving share settings: {e}")
    
    def save_share_links(self, share_links):
        """共有リンクを保存"""
        self._share_links = share_links
        share_links_path = os.path.join(self.share_dir, "share_links.json")
        try:
            with open(share_links_path, "w", encoding="utf-8") as f:
                json.dump(share_links, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving share links: {e}")
    
    def save_share_history(self, share_history):
        """共有履歴を保存"""
        self._share_history = share_history
        share_history_path = os.path.join(self.share_dir, "share_history.json")
        try:
            with open(share_history_path, "w", encoding="utf-8") as f:
                json.dump(share_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving share history: {e}")
    
    def save_notifications(self, notifications):
        """通知を保存"""
        self._notifications = notifications
        notifications_path = os.path.join(self.notification_dir, "notifications.json")
        try:
            with open(notifications_path, "w", encoding="utf-8") as f:
                json.dump(notifications, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving notifications: {e}")
    
    def save_subscriptions(self, subscriptions):
        """購読設定を保存"""
        self._subscriptions = subscriptions
        subscriptions_path = os.path.join(self.notification_dir, "subscriptions.json")
        try:
            with open(subscriptions_path, "w", encoding="utf-8") as f:
                json.dump(subscriptions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving subscriptions: {e}")
    
    def load_share_settings(self):
        """共有設定を読み込む"""
        return self._share_settings
    
    def load_share_links(self):
        """共有リンクを読み込む"""
        return self._share_links
    
    def load_share_history(self):
        """共有履歴を読み込む"""
        return self._share_history
    
    def load_notifications(self):
        """通知を読み込む"""
        return self._notifications
    
    def load_subscriptions(self):
        """購読設定を読み込む"""
        return self._subscriptions

def setup_demo_managers():
    """デモ用の各種マネージャーをセットアップ"""
    # ストレージマネージャー
    storage_manager = DemoStorageManager()
    
    # ユーザーマネージャー
    user_manager = DemoUserManager()
    
    # レポートマネージャー
    report_manager = DemoReportManager()
    
    # 通知テンプレートマネージャー
    template_manager = NotificationTemplateManager()
    
    # 権限マネージャー
    permission_manager = PermissionManager(storage_manager, user_manager)
    
    # 共有マネージャー
    share_manager = ShareManager(
        storage_manager=storage_manager, 
        auth_manager=user_manager,
        permission_manager=permission_manager
    )
    
    # 通知マネージャー
    notification_manager = NotificationManager(
        storage_manager=storage_manager,
        user_manager=user_manager,
        template_manager=template_manager
    )
    
    return {
        "storage_manager": storage_manager,
        "user_manager": user_manager,
        "report_manager": report_manager,
        "template_manager": template_manager,
        "permission_manager": permission_manager,
        "share_manager": share_manager,
        "notification_manager": notification_manager
    }

def initialize_session_state():
    """セッション状態を初期化"""
    # ユーザー情報
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = "user1"
    
    if "user_name" not in st.session_state:
        st.session_state["user_name"] = "山田太郎"
    
    # アクティブタブ
    if "active_tab" not in st.session_state:
        st.session_state["active_tab"] = "share"

def sidebar_user_selector(user_manager):
    """サイドバーのユーザー選択UI"""
    st.sidebar.header("ユーザー切り替え")
    
    # ユーザー一覧を取得
    users = user_manager.get_recent_users()
    
    # ユーザー選択
    user_options = {user["id"]: f"{user['name']} ({user['role']})" for user in users}
    selected_user_id = st.sidebar.selectbox(
        "ユーザーを選択",
        options=list(user_options.keys()),
        format_func=lambda x: user_options[x],
        index=list(user_options.keys()).index(st.session_state["user_id"])
    )
    
    if selected_user_id != st.session_state["user_id"]:
        # ユーザー情報を更新
        user_info = user_manager.get_user(selected_user_id)
        st.session_state["user_id"] = selected_user_id
        st.session_state["user_name"] = user_info["name"]
        st.sidebar.success(f"ユーザーを {user_info['name']} に変更しました")
        st.experimental_rerun()
    
    # 現在のユーザー情報
    user_info = user_manager.get_user(st.session_state["user_id"])
    st.sidebar.write(f"ログイン中: **{user_info['name']}**")
    st.sidebar.write(f"メール: {user_info['email']}")
    st.sidebar.write(f"役割: {user_info['role']}")
    
    st.sidebar.divider()

def create_test_notification(notification_manager, user_id, user_name):
    """テスト通知を作成するUI"""
    st.sidebar.header("テスト通知作成")
    
    # イベントタイプ
    event_types = {
        "report_shared": "レポート共有",
        "report_updated": "レポート更新",
        "comment_added": "コメント追加",
        "team_invitation": "チーム招待",
        "analysis_completed": "分析完了",
        "strategy_point_detected": "戦略ポイント検出"
    }
    
    event_type = st.sidebar.selectbox(
        "通知タイプ",
        options=list(event_types.keys()),
        format_func=lambda x: event_types[x]
    )
    
    # 受信者選択
    users = [{"id": "user1", "name": "山田太郎"},
             {"id": "user2", "name": "佐藤花子"},
             {"id": "user3", "name": "鈴木一郎"},
             {"id": "user4", "name": "田中誠"}]
    
    recipient = st.sidebar.selectbox(
        "受信者",
        options=[u["id"] for u in users],
        format_func=lambda x: next((u["name"] for u in users if u["id"] == x), x)
    )
    
    # 優先度
    priority = st.sidebar.radio(
        "優先度",
        options=["normal", "high", "low"],
        format_func=lambda x: "普通" if x == "normal" else "高" if x == "high" else "低"
    )
    
    # 通知作成ボタン
    if st.sidebar.button("通知を作成", type="primary"):
        # イベントタイプに応じたデータを準備
        if event_type == "report_shared":
            event_data = {
                "user_name": user_name,
                "report_name": "2024年春季レガッタ分析",
                "report_id": "report1"
            }
        elif event_type == "report_updated":
            event_data = {
                "user_name": user_name,
                "report_name": "トレーニングセッション評価",
                "report_id": "report2",
                "changes": ["風向データの更新", "パフォーマンス指標の追加"]
            }
        elif event_type == "comment_added":
            event_data = {
                "user_name": user_name,
                "item_type": "レポート",
                "item_name": "風向変化パターン分析",
                "item_id": "report3",
                "comment_text": "東向きの風のときの戦略を再検討する必要があります。"
            }
        elif event_type == "team_invitation":
            event_data = {
                "user_name": user_name,
                "team_name": "高性能分析チーム",
                "team_id": "team1"
            }
        elif event_type == "analysis_completed":
            event_data = {
                "session_name": "4月第3週トレーニングセッション",
                "session_id": "session1",
                "findings": "スタート時の加速に改善の余地があります。"
            }
        elif event_type == "strategy_point_detected":
            event_data = {
                "session_name": "春季レガッタ予選",
                "session_id": "session2",
                "point_type": "タック判断の最適化ポイント",
                "location": "第2マーク付近"
            }
        else:
            event_data = {"event": event_type}
        
        # 通知を作成
        notification_ids = notification_manager.create_notification(
            event_type=event_type,
            event_data=event_data,
            recipients=[recipient],
            priority=priority
        )
        
        if notification_ids:
            st.sidebar.success(f"通知を作成しました: {notification_ids[0]}")
        else:
            st.sidebar.error("通知の作成に失敗しました")
    
    st.sidebar.divider()

def main():
    """メイン関数"""
    # Streamlit設定
    st.set_page_config(
        page_title="セーリング戦略分析 - 共有・通知デモ",
        page_icon="🔄",
        layout="wide"
    )
    
    # タイトル
    st.title("セーリング戦略分析システム")
    st.subheader("レポート共有と通知機能のデモ")
    
    # セッション状態の初期化
    initialize_session_state()
    
    # デモ用マネージャーのセットアップ
    managers = setup_demo_managers()
    
    # サイドバー
    sidebar_user_selector(managers["user_manager"])
    create_test_notification(
        managers["notification_manager"], 
        st.session_state["user_id"],
        st.session_state["user_name"]
    )
    
    # タブ
    share_tab, notification_tab = st.tabs(["共有機能", "通知機能"])
    
    # 共有機能タブ
    with share_tab:
        # 共有パネル
        share_panel = SharePanel(
            key="demo_share",
            report_manager=managers["report_manager"],
            user_manager=managers["user_manager"],
            share_manager=managers["share_manager"]
        )
        
        share_panel.render()
    
    # 通知機能タブ
    with notification_tab:
        # 通知パネル
        notification_panel = NotificationPanel(
            key="demo_notification",
            notification_manager=managers["notification_manager"],
            user_manager=managers["user_manager"]
        )
        
        notification_panel.render(user_id=st.session_state["user_id"])
    
    # フッター
    st.markdown("---")
    st.caption("セーリング戦略分析システム - 共有・通知機能デモ © 2024")

if __name__ == "__main__":
    main()
