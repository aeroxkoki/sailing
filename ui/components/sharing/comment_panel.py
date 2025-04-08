"""
ui.components.sharing.comment_panel

コメントパネルUIコンポーネント
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Callable
import datetime
import re

from sailing_data_processor.sharing import CommentManager


class CommentPanelComponent:
    """
    コメントパネルUIコンポーネント
    
    セッション、プロジェクト、特定の戦略ポイントなどにコメントを追加・表示する
    UIコンポーネントです。返信やメンション機能をサポートします。
    """
    
    def __init__(self, key="comment_panel", 
                 comment_manager: Optional[CommentManager] = None, 
                 user_id: Optional[str] = None,
                 user_name: Optional[str] = None):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネント一意のキー, by default "comment_panel"
        comment_manager : Optional[CommentManager], optional
            コメント管理クラス, by default None
        user_id : Optional[str], optional
            現在のユーザーID, by default None
        user_name : Optional[str], optional
            ユーザー名, by default None
        """
        self.key = key
        self.comment_manager = comment_manager
        self.user_id = user_id
        self.user_name = user_name or user_id
        
        # 状態の初期化
        if f"{key}_reply_to" not in st.session_state:
            st.session_state[f"{key}_reply_to"] = None
        if f"{key}_edit_comment" not in st.session_state:
            st.session_state[f"{key}_edit_comment"] = None
        if f"{key}_sort_order" not in st.session_state:
            st.session_state[f"{key}_sort_order"] = "newest"
        if f"{key}_filter" not in st.session_state:
            st.session_state[f"{key}_filter"] = "all"
    
    def render(self, item_id: str, item_type: str, reference_data: Optional[Dict[str, Any]] = None):
        """
        コンポーネントのレンダリング
        
        Parameters
        ----------
        item_id : str
            コメント対象アイテムID
        item_type : str
            アイテム種類 ("session", "project", "result" etc.)
        reference_data : Optional[Dict[str, Any]], optional
            参照データ（戦略ポイントなど）, by default None
        """
        st.subheader("コメント")
        
        # コメント管理クラスやユーザーIDがない場合はエラー表示
        if not self.comment_manager or not self.user_id:
            st.error("コメント管理が設定されていないか、ユーザーIDが不明です。")
            return
        
        # コメント入力フォーム
        self._render_comment_input(item_id, item_type, reference_data)
        
        # コメント一覧
        self._render_comment_list(item_id, item_type)
    
    def _render_comment_input(self, item_id: str, item_type: str, reference_data: Optional[Dict[str, Any]] = None):
        """
        コメント入力フォームの表示
        
        Parameters
        ----------
        item_id : str
            コメント対象アイテムID
        item_type : str
            アイテム種類
        reference_data : Optional[Dict[str, Any]], optional
            参照データ, by default None
        """
        # 返信モードの場合は対象コメントを表示
        reply_to = st.session_state[f"{self.key}_reply_to"]
        if reply_to and self.comment_manager:
            parent_comment = None
            
            # コメント一覧から親コメントを検索
            comments = self.comment_manager.get_comments(item_id, item_type)
            for comment in comments:
                if comment.comment_id == reply_to:
                    parent_comment = comment
                    break
            
            if parent_comment:
                st.info(f"**{parent_comment.user_name}** へ返信:\\n\\n{parent_comment.content[:100]}...")
                
                # 返信キャンセルボタン
                if st.button("返信をキャンセル", key=f"{self.key}_cancel_reply"):
                    st.session_state[f"{self.key}_reply_to"] = None
                    st.experimental_rerun()
        
        # 編集モードの場合は既存コメントの内容を表示
        edit_comment_id = st.session_state[f"{self.key}_edit_comment"]
        initial_content = ""
        
        if edit_comment_id and self.comment_manager:
            # コメント一覧から編集対象コメントを検索
            comments = self.comment_manager.get_comments(item_id, item_type)
            for comment in comments:
                if comment.comment_id == edit_comment_id:
                    initial_content = comment.content
                    break
        
        # 参照データがある場合は参照タイプを表示
        reference_type = None
        if reference_data:
            reference_type = reference_data.get("type")
            reference_label = "時間参照" if reference_type == "time" else "ポイント参照" if reference_type == "point" else "参照"
            st.info(f"**{reference_label}** 付きコメントを作成しています")
        
        # コメント入力フォーム
        with st.form(key=f"{self.key}_comment_form"):
            # コメント内容入力
            content = st.text_area(
                "コメント",
                value=initial_content,
                height=100,
                key=f"{self.key}_comment_content"
            )
            
            # メンション機能の説明
            st.caption("コメント内で@ユーザー名 と入力すると、そのユーザーにメンションできます")
            
            # 送信ボタン
            action = "更新" if edit_comment_id else "返信" if reply_to else "送信"
            submit = st.form_submit_button(action)
            
            if submit and content:
                try:
                    if edit_comment_id:
                        # コメント編集
                        success = self.comment_manager.update_comment(
                            item_id=item_id,
                            comment_id=edit_comment_id,
                            content=content
                        )
                        
                        if success:
                            st.success("コメントを更新しました")
                            st.session_state[f"{self.key}_edit_comment"] = None
                            st.experimental_rerun()
                        else:
                            st.error("コメントの更新に失敗しました")
                    elif reference_data and reference_data.get("point_id"):
                        # 戦略ポイントへのコメント
                        point_comment = self.comment_manager.add_point_comment(
                            item_id=item_id,
                            item_type=item_type,
                            content=content,
                            user_id=self.user_id,
                            user_name=self.user_name,
                            point_id=reference_data["point_id"],
                            timestamp=reference_data.get("timestamp"),
                            lat=reference_data.get("lat"),
                            lon=reference_data.get("lon"),
                            parent_id=reply_to
                        )
                        
                        if point_comment:
                            st.success("コメントを投稿しました")
                            
                            # 返信モードをリセット
                            if reply_to:
                                st.session_state[f"{self.key}_reply_to"] = None
                                
                            # 入力欄をクリア
                            st.session_state[f"{self.key}_comment_content"] = ""
                            
                            st.experimental_rerun()
                        else:
                            st.error("コメントの投稿に失敗しました")
                    else:
                        # 通常のコメント
                        comment = self.comment_manager.add_comment(
                            item_id=item_id,
                            item_type=item_type,
                            content=content,
                            user_id=self.user_id,
                            user_name=self.user_name,
                            parent_id=reply_to
                        )
                        
                        if comment:
                            st.success("コメントを投稿しました")
                            
                            # 返信モードをリセット
                            if reply_to:
                                st.session_state[f"{self.key}_reply_to"] = None
                                
                            # 入力欄をクリア
                            st.session_state[f"{self.key}_comment_content"] = ""
                            
                            st.experimental_rerun()
                        else:
                            st.error("コメントの投稿に失敗しました")
                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}")
    
    def _render_comment_list(self, item_id: str, item_type: str):
        """
        コメント一覧の表示
        
        Parameters
        ----------
        item_id : str
            アイテムID
        item_type : str
            アイテム種類
        """
        if not self.comment_manager:
            return
            
        # コメント一覧の取得
        sort_options = {
            "newest": "新しい順",
            "oldest": "古い順"
        }
        
        # コントロールバー（ソート順、フィルタリングなど）
        col1, col2 = st.columns([1, 3])
        
        with col1:
            sort_order = st.selectbox(
                "並び順",
                options=list(sort_options.keys()),
                format_func=lambda x: sort_options.get(x, x),
                key=f"{self.key}_sort_select"
            )
            
            # 並び順変更時に状態を更新
            if sort_order != st.session_state[f"{self.key}_sort_order"]:
                st.session_state[f"{self.key}_sort_order"] = sort_order
                st.experimental_rerun()
        
        # デバイダー
        st.markdown("---")
        
        # コメントスレッド構造の取得
        thread_data = self.comment_manager.get_comment_threads(item_id, item_type)
        
        # トップレベルコメント（ルートコメント）の取得
        root_comments = thread_data.get("root", [])
        
        if not root_comments:
            st.info("コメントはまだありません。最初のコメントを投稿しましょう！")
            return
        
        # コメントのソート
        reverse_sort = st.session_state[f"{self.key}_sort_order"] == "newest"
        root_comments.sort(key=lambda c: c.created_at, reverse=reverse_sort)
        
        # コメントの表示
        for comment in root_comments:
            self._render_comment_card(comment, thread_data.get(comment.comment_id, []), item_id, item_type)
    
    def _render_comment_card(self, comment, replies, item_id, item_type, is_reply=False):
        """
        コメントカードの表示
        
        Parameters
        ----------
        comment : Comment
            コメント情報
        replies : List
            返信リスト
        item_id : str
            アイテムID
        item_type : str
            アイテム種類
        is_reply : bool, optional
            返信コメントかどうか, by default False
        """
        comment_id = comment.comment_id
        author_id = comment.user_id
        author_name = comment.user_name
        content = comment.content
        created_at = datetime.datetime.fromisoformat(comment.created_at)
        updated_at = datetime.datetime.fromisoformat(comment.updated_at)
        is_edited = created_at != updated_at
        is_deleted = getattr(comment, "deleted", False)
        
        # 返信であればインデント
        indent = st.container() if not is_reply else st.container().columns([0.1, 0.9])[1]
        
        with indent:
            # カードスタイルのコメント
            card_style = {} if not is_reply else {"border": "none", "margin-top": "0"}
            
            with st.container():
                # 削除済みコメントの場合は表示
                if is_deleted:
                    st.markdown("*このコメントは削除されました*")
                    return
                
                # ヘッダー（ユーザー名、日時）
                header_col1, header_col2 = st.columns([3, 1])
                
                with header_col1:
                    # ユーザー名（自分の場合は強調）
                    if author_id == self.user_id:
                        st.markdown(f"**{author_name}** (あなた)")
                    else:
                        st.markdown(f"**{author_name}**")
                
                with header_col2:
                    # 日時（相対表示）
                    time_diff = datetime.datetime.now() - created_at
                    if time_diff.days > 0:
                        time_str = f"{time_diff.days}日前"
                    elif time_diff.seconds // 3600 > 0:
                        time_str = f"{time_diff.seconds // 3600}時間前"
                    else:
                        time_str = f"{time_diff.seconds // 60}分前"
                    
                    # 編集された場合は表示
                    if is_edited:
                        time_str += " (編集済)"
                    
                    st.markdown(f"*{time_str}*")
                
                # 戦略ポイント情報の表示
                if hasattr(comment, "point_id") and comment.point_id:
                    point_id = comment.point_id
                    
                    # 位置情報がある場合は表示
                    if hasattr(comment, "lat") and comment.lat is not None and hasattr(comment, "lon") and comment.lon is not None:
                        st.info(f"📍 **ポイント参照**: {point_id} (緯度: {comment.lat:.6f}, 経度: {comment.lon:.6f})")
                    else:
                        st.info(f"📍 **ポイント参照**: {point_id}")
                
                # コメント内容（メンションをハイライト）
                formatted_content = self._format_content_with_mentions(content)
                st.markdown(formatted_content)
                
                # アクションボタン
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    # 返信ボタン
                    if st.button("返信", key=f"{self.key}_reply_{comment_id}"):
                        st.session_state[f"{self.key}_reply_to"] = comment_id
                        st.session_state[f"{self.key}_edit_comment"] = None
                        st.experimental_rerun()
                
                with col2:
                    # 自分のコメントの場合は編集ボタン
                    if author_id == self.user_id:
                        if st.button("編集", key=f"{self.key}_edit_{comment_id}"):
                            st.session_state[f"{self.key}_edit_comment"] = comment_id
                            st.session_state[f"{self.key}_reply_to"] = None
                            st.experimental_rerun()
                
                with col3:
                    # 自分のコメントの場合は削除ボタン
                    if author_id == self.user_id:
                        # 削除ボタン（確認付き）
                        delete_key = f"{self.key}_delete_{comment_id}"
                        confirm_key = f"{self.key}_confirm_{comment_id}"
                        
                        if confirm_key not in st.session_state:
                            st.session_state[confirm_key] = False
                            
                        if st.session_state[confirm_key]:
                            if st.button("削除確認", key=f"{delete_key}_confirm"):
                                # コメントの削除
                                success = self.comment_manager.delete_comment(item_id, comment_id)
                                if success:
                                    st.success("コメントを削除しました")
                                    st.session_state[confirm_key] = False
                                    st.experimental_rerun()
                                else:
                                    st.error("コメントの削除に失敗しました")
                                
                            if st.button("キャンセル", key=f"{delete_key}_cancel"):
                                st.session_state[confirm_key] = False
                                st.experimental_rerun()
                        else:
                            if st.button("削除", key=delete_key):
                                st.session_state[confirm_key] = True
                                st.experimental_rerun()
            
            # 返信の表示
            if replies:
                # 返信のソート
                reverse_sort = st.session_state[f"{self.key}_sort_order"] == "newest"
                sorted_replies = sorted(replies, key=lambda r: r.created_at, reverse=reverse_sort)
                
                for reply in sorted_replies:
                    self._render_comment_card(reply, [], item_id, item_type, is_reply=True)
    
    def _format_content_with_mentions(self, content: str) -> str:
        """
        メンションをハイライトした内容の整形
        
        Parameters
        ----------
        content : str
            コメント内容
            
        Returns
        -------
        str
            整形されたコメント内容
        """
        # メンション（@ユーザー名）をハイライト
        formatted = re.sub(r'@(\w+)', r'**@\1**', content)
        
        return formatted


# より簡単に使用するためのAPIヘルパー関数
def CommentPanel(item_id: str, item_type: str, 
                comment_manager=None, user_id=None, user_name=None, 
                reference_data=None, key="comment_panel"):
    """
    コメントパネルのレンダリング
    
    Parameters
    ----------
    item_id : str
        コメント対象アイテムID
    item_type : str
        アイテム種類
    comment_manager : optional
        コメント管理クラス, by default None
    user_id : optional
        現在のユーザーID, by default None
    user_name : optional
        ユーザー名, by default None
    reference_data : optional
        参照データ, by default None
    key : str, optional
        コンポーネント一意のキー, by default "comment_panel"
    """
    component = CommentPanelComponent(
        key=key,
        comment_manager=comment_manager,
        user_id=user_id,
        user_name=user_name
    )
    component.render(item_id, item_type, reference_data)
