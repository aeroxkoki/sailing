"""
ui.integrated.components.feedback.feedback_component

フィードバックコンポーネント
操作状態や処理結果に関するフィードバックを提供します。
"""

import streamlit as st
import time
from typing import Optional, Callable, Dict, Any, List
import threading

class FeedbackComponent:
    """フィードバックコンポーネント"""
    
    def __init__(self):
        """初期化"""
        self.message_duration = 5  # デフォルトのメッセージ表示時間（秒）
    
    def show_success(self, message: str, duration: Optional[int] = None):
        """
        成功メッセージを表示
        
        Parameters
        ----------
        message : str
            表示するメッセージ
        duration : Optional[int], optional
            表示する秒数（Noneの場合は自動消去しない）, by default None
        """
        success_container = st.success(message)
        
        if duration is not None:
            self._auto_dismiss(success_container, duration)
    
    def show_info(self, message: str, duration: Optional[int] = None):
        """
        情報メッセージを表示
        
        Parameters
        ----------
        message : str
            表示するメッセージ
        duration : Optional[int], optional
            表示する秒数（Noneの場合は自動消去しない）, by default None
        """
        info_container = st.info(message)
        
        if duration is not None:
            self._auto_dismiss(info_container, duration)
    
    def show_warning(self, message: str, duration: Optional[int] = None):
        """
        警告メッセージを表示
        
        Parameters
        ----------
        message : str
            表示するメッセージ
        duration : Optional[int], optional
            表示する秒数（Noneの場合は自動消去しない）, by default None
        """
        warning_container = st.warning(message)
        
        if duration is not None:
            self._auto_dismiss(warning_container, duration)
    
    def show_error(self, message: str, recovery_actions: Optional[List[Dict[str, Any]]] = None, duration: Optional[int] = None):
        """
        エラーメッセージと回復オプションを表示
        
        Parameters
        ----------
        message : str
            表示するメッセージ
        recovery_actions : Optional[List[Dict[str, Any]]], optional
            回復アクションのリスト [{"label": "再試行", "action": callback_function}, ...], by default None
        duration : Optional[int], optional
            表示する秒数（Noneの場合は自動消去しない）, by default None
        """
        error_container = st.error(message)
        
        # 回復アクションの表示
        if recovery_actions:
            col_count = min(len(recovery_actions), 3)
            cols = st.columns(col_count)
            
            for i, action in enumerate(recovery_actions):
                with cols[i % col_count]:
                    if st.button(action["label"], key=f"recovery_action_{i}"):
                        # エラーメッセージを消去
                        error_container.empty()
                        # アクション実行
                        if callable(action["action"]):
                            action["action"]()
        
        if duration is not None:
            self._auto_dismiss(error_container, duration)
    
    def show_process_status(self, process_name: str, steps: List[str], current_step: int = 0):
        """
        処理状態をプログレスバーとともに表示
        
        Parameters
        ----------
        process_name : str
            処理の名前
        steps : List[str]
            処理ステップのリスト
        current_step : int, optional
            現在のステップ（0から始まる）, by default 0
        
        Returns
        -------
        Tuple[streamlit.empty, streamlit.progress]
            ステータステキストコンテナとプログレスバー
        """
        status_container = st.empty()
        progress_bar = st.progress(0)
        
        # 現在のステップを表示
        if 0 <= current_step < len(steps):
            step_text = steps[current_step]
            status_container.text(f"{process_name}: {step_text} ({current_step+1}/{len(steps)})")
            progress_value = (current_step + 1) / len(steps)
            progress_bar.progress(progress_value)
        
        return status_container, progress_bar
    
    def update_process_status(self, status_container, progress_bar, process_name: str, steps: List[str], current_step: int):
        """
        処理状態を更新
        
        Parameters
        ----------
        status_container : streamlit.empty
            ステータステキストコンテナ
        progress_bar : streamlit.progress
            プログレスバー
        process_name : str
            処理の名前
        steps : List[str]
            処理ステップのリスト
        current_step : int
            現在のステップ（0から始まる）
        """
        if 0 <= current_step < len(steps):
            step_text = steps[current_step]
            status_container.text(f"{process_name}: {step_text} ({current_step+1}/{len(steps)})")
            progress_value = (current_step + 1) / len(steps)
            progress_bar.progress(progress_value)
    
    def complete_process(self, status_container, progress_bar, process_name: str, success: bool = True):
        """
        処理完了を表示
        
        Parameters
        ----------
        status_container : streamlit.empty
            ステータステキストコンテナ
        progress_bar : streamlit.progress
            プログレスバー
        process_name : str
            処理の名前
        success : bool, optional
            処理が成功したかどうか, by default True
        """
        if success:
            status_container.success(f"{process_name}: 完了しました")
            progress_bar.progress(1.0)
        else:
            status_container.error(f"{process_name}: エラーが発生しました")
    
    def show_toast(self, message: str, icon: str = "info"):
        """
        トースト通知を表示（小さい通知）
        
        Parameters
        ----------
        message : str
            表示するメッセージ
        icon : str, optional
            アイコン ("info", "success", "error", "warning"), by default "info"
        """
        # トースト用のHTMLを生成
        icon_svg = self._get_icon_svg(icon)
        
        toast_html = f"""
        <div id="toast" style="visibility: hidden; position: fixed; bottom: 20px; right: 20px; 
                               min-width: 250px; max-width: 320px; background-color: white; 
                               box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-radius: 4px; z-index: 1000;
                               display: flex; align-items: center; padding: 10px;">
            <div style="margin-right: 10px; color: {self._get_icon_color(icon)};">
                {icon_svg}
            </div>
            <div style="flex-grow: 1;">
                {message}
            </div>
        </div>
        
        <script>
            (function() {{
                const toast = document.getElementById("toast");
                // スタイルを可視に変更
                toast.style.visibility = "visible";
                // 3秒後にトーストを非表示
                setTimeout(function(){{ 
                    toast.style.opacity = "0";
                    toast.style.transition = "opacity 0.5s";
                    setTimeout(function(){{ toast.style.display = "none"; }}, 500);
                }}, 3000);
            }})();
        </script>
        """
        
        st.markdown(toast_html, unsafe_allow_html=True)
    
    def show_confirmation_dialog(self, title: str, message: str, confirm_action: Callable, cancel_action: Optional[Callable] = None):
        """
        確認ダイアログを表示
        
        Parameters
        ----------
        title : str
            ダイアログのタイトル
        message : str
            確認メッセージ
        confirm_action : Callable
            確認ボタンを押した時のアクション
        cancel_action : Optional[Callable], optional
            キャンセルボタンを押した時のアクション, by default None
        """
        with st.expander(title, expanded=True):
            st.markdown(message)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("はい", use_container_width=True):
                    confirm_action()
            
            with col2:
                if st.button("いいえ", use_container_width=True):
                    if cancel_action:
                        cancel_action()
    
    def show_operation_result(self, success: bool, operation_name: str, result_details: Optional[Dict[str, Any]] = None):
        """
        操作結果のサマリーを表示
        
        Parameters
        ----------
        success : bool
            操作が成功したかどうか
        operation_name : str
            操作の名前
        result_details : Optional[Dict[str, Any]], optional
            結果の詳細情報, by default None
        """
        if success:
            with st.expander(f"{operation_name}が正常に完了しました", expanded=True):
                st.success("処理は正常に完了しました。")
                
                if result_details:
                    st.markdown("### 処理結果")
                    
                    for key, value in result_details.items():
                        st.markdown(f"**{key}**: {value}")
        else:
            with st.expander(f"{operation_name}中にエラーが発生しました", expanded=True):
                st.error("処理中にエラーが発生しました。")
                
                if result_details:
                    st.markdown("### エラー詳細")
                    
                    for key, value in result_details.items():
                        st.markdown(f"**{key}**: {value}")
    
    def _auto_dismiss(self, container, duration: int):
        """
        指定された時間後にコンテナを消去する
        
        Parameters
        ----------
        container : streamlit.delta_generator
            消去対象のコンテナ
        duration : int
            表示する秒数
        """
        # 非同期で一定時間後に消去
        def dismiss():
            time.sleep(duration)
            container.empty()
        
        threading.Thread(target=dismiss, daemon=True).start()
    
    def _get_icon_svg(self, icon: str) -> str:
        """
        アイコンのSVGを取得
        
        Parameters
        ----------
        icon : str
            アイコンタイプ
        
        Returns
        -------
        str
            SVG文字列
        """
        if icon == "success":
            return '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M8 12l2 2 4-4"></path></svg>'''
        elif icon == "error":
            return '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>'''
        elif icon == "warning":
            return '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'''
        else:  # info
            return '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'''
    
    def _get_icon_color(self, icon: str) -> str:
        """
        アイコンの色を取得
        
        Parameters
        ----------
        icon : str
            アイコンタイプ
        
        Returns
        -------
        str
            カラーコード
        """
        if icon == "success":
            return "#4CAF50"
        elif icon == "error":
            return "#F44336"
        elif icon == "warning":
            return "#FF9800"
        else:  # info
            return "#2196F3"
