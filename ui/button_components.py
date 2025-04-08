"""
セーリング戦略分析システム - ボタンコンポーネント

UIガイドラインに従った再利用可能なボタンコンポーネント群
"""

import streamlit as st
from typing import Optional, Callable, Any, Dict, List, Tuple

def primary_button(
    label: str, 
    on_click: Optional[Callable] = None, 
    key: Optional[str] = None, 
    help: Optional[str] = None,
    args: Optional[Tuple] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    use_container_width: bool = False,
    small: bool = False,
    icon: Optional[str] = None,
    disabled: bool = False
) -> bool:
    """
    プライマリアクションのためのメインボタン

    Parameters
    ----------
    label : str
        ボタンのテキスト
    on_click : Callable, optional
        クリック時のコールバック関数
    key : str, optional
        コンポーネントのキー
    help : str, optional
        ヘルプテキスト
    args : Tuple, optional
        コールバック関数に渡す位置引数
    kwargs : Dict[str, Any], optional
        コールバック関数に渡すキーワード引数
    use_container_width : bool, optional
        親コンテナの幅いっぱいに表示するか
    small : bool, optional
        小さいボタンとして表示するか
    icon : str, optional
        Font Awesomeアイコン名（例: "arrow-right"）
    disabled : bool, optional
        ボタンの無効化

    Returns
    -------
    bool
        ボタンがクリックされたかどうか
    """
    # アイコンがある場合、ラベルの前に追加
    if icon:
        label = f"<i class='fas fa-{icon}'></i> {label}"
    
    # サイズに応じたスタイルの適用
    padding = "6px 12px" if small else "8px 16px"
    font_size = "14px" if small else "16px"

    # カスタムスタイルの定義
    custom_styles = f"""
        <style>
            div[data-testid="stButton"] > button:first-child {{
                background-color: {'#e7e7e7' if disabled else '#1565C0'};
                color: {'#9E9E9E' if disabled else 'white'};
                border: none;
                border-radius: 4px;
                padding: {padding};
                font-weight: 500;
                font-size: {font_size};
                letter-spacing: 0.3px;
                transition: all 0.2s ease;
                {'width: 100%;' if use_container_width else ''}
                {'opacity: 0.7; cursor: not-allowed;' if disabled else ''}
            }}
            div[data-testid="stButton"] > button:first-child:hover {{
                background-color: {'#e7e7e7' if disabled else '#0D47A1'};
                transform: {'none' if disabled else 'translateY(-1px)'};
            }}
            div[data-testid="stButton"] > button:first-child:active {{
                transform: {'none' if disabled else 'translateY(0px)'};
            }}
        </style>
    """
    
    # カスタムスタイルの適用
    st.markdown(custom_styles, unsafe_allow_html=True)
    
    # 標準的なStreamlitボタンを表示
    return st.button(
        label,
        key=key,
        help=help,
        on_click=on_click,
        args=args,
        kwargs=kwargs,
        disabled=disabled,
        type="primary",
        use_container_width=use_container_width
    )

def secondary_button(
    label: str, 
    on_click: Optional[Callable] = None, 
    key: Optional[str] = None, 
    help: Optional[str] = None,
    args: Optional[Tuple] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    use_container_width: bool = False,
    small: bool = False,
    icon: Optional[str] = None,
    disabled: bool = False
) -> bool:
    """
    セカンダリアクションのための補助ボタン

    Parameters
    ----------
    label : str
        ボタンのテキスト
    on_click : Callable, optional
        クリック時のコールバック関数
    key : str, optional
        コンポーネントのキー
    help : str, optional
        ヘルプテキスト
    args : Tuple, optional
        コールバック関数に渡す位置引数
    kwargs : Dict[str, Any], optional
        コールバック関数に渡すキーワード引数
    use_container_width : bool, optional
        親コンテナの幅いっぱいに表示するか
    small : bool, optional
        小さいボタンとして表示するか
    icon : str, optional
        Font Awesomeアイコン名（例: "arrow-right"）
    disabled : bool, optional
        ボタンの無効化

    Returns
    -------
    bool
        ボタンがクリックされたかどうか
    """
    # アイコンがある場合、ラベルの前に追加
    if icon:
        label = f"<i class='fas fa-{icon}'></i> {label}"
    
    # サイズに応じたスタイルの適用
    padding = "6px 12px" if small else "8px 16px"
    font_size = "14px" if small else "16px"

    # カスタムスタイルの定義
    custom_styles = f"""
        <style>
            div[data-testid="stButton"] > button:first-child {{
                background-color: {'#f5f5f5' if disabled else 'white'};
                color: {'#9E9E9E' if disabled else '#1565C0'};
                border: 1px solid {'#e0e0e0' if disabled else '#1565C0'};
                border-radius: 4px;
                padding: {padding};
                font-weight: 500;
                font-size: {font_size};
                letter-spacing: 0.3px;
                transition: all 0.2s ease;
                {'width: 100%;' if use_container_width else ''}
                {'opacity: 0.7; cursor: not-allowed;' if disabled else ''}
            }}
            div[data-testid="stButton"] > button:first-child:hover {{
                background-color: {'#f5f5f5' if disabled else '#E3F2FD'};
                transform: {'none' if disabled else 'translateY(-1px)'};
            }}
            div[data-testid="stButton"] > button:first-child:active {{
                transform: {'none' if disabled else 'translateY(0px)'};
            }}
        </style>
    """
    
    # カスタムスタイルの適用
    st.markdown(custom_styles, unsafe_allow_html=True)
    
    # 標準的なStreamlitボタンを表示（セカンダリタイプ）
    return st.button(
        label,
        key=key,
        help=help,
        on_click=on_click,
        args=args,
        kwargs=kwargs,
        disabled=disabled,
        type="secondary",
        use_container_width=use_container_width
    )

def text_button(
    label: str, 
    on_click: Optional[Callable] = None, 
    key: Optional[str] = None, 
    help: Optional[str] = None,
    args: Optional[Tuple] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    icon: Optional[str] = None,
    disabled: bool = False
) -> bool:
    """
    テキストのみのミニマルなボタン

    Parameters
    ----------
    label : str
        ボタンのテキスト
    on_click : Callable, optional
        クリック時のコールバック関数
    key : str, optional
        コンポーネントのキー
    help : str, optional
        ヘルプテキスト
    args : Tuple, optional
        コールバック関数に渡す位置引数
    kwargs : Dict[str, Any], optional
        コールバック関数に渡すキーワード引数
    icon : str, optional
        Font Awesomeアイコン名（例: "arrow-right"）
    disabled : bool, optional
        ボタンの無効化

    Returns
    -------
    bool
        ボタンがクリックされたかどうか
    """
    # アイコンがある場合、ラベルの前に追加
    if icon:
        label = f"<i class='fas fa-{icon}'></i> {label}"
    
    # カスタムスタイルの定義（テキストのみ）
    custom_styles = f"""
        <style>
            div[data-testid="stButton"] > button:first-child {{
                background-color: transparent;
                color: {'#9E9E9E' if disabled else '#1565C0'};
                border: none;
                padding: 4px 8px;
                font-weight: 500;
                font-size: 14px;
                transition: all 0.2s ease;
                {'opacity: 0.7; cursor: not-allowed;' if disabled else ''}
            }}
            div[data-testid="stButton"] > button:first-child:hover {{
                background-color: {'transparent' if disabled else '#F5F5F5'};
                text-decoration: {'none' if disabled else 'underline'};
            }}
        </style>
    """
    
    # カスタムスタイルの適用
    st.markdown(custom_styles, unsafe_allow_html=True)
    
    # 標準的なStreamlitボタンを表示
    return st.button(
        label,
        key=key,
        help=help,
        on_click=on_click,
        args=args,
        kwargs=kwargs,
        disabled=disabled
    )

def warning_button(
    label: str, 
    on_click: Optional[Callable] = None, 
    key: Optional[str] = None, 
    help: Optional[str] = None,
    args: Optional[Tuple] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    use_container_width: bool = False,
    small: bool = False,
    icon: Optional[str] = None,
    disabled: bool = False,
    confirmation: bool = False,
    confirmation_message: str = "この操作を実行してもよろしいですか？"
) -> bool:
    """
    警告アクションのためのボタン（例: 削除、リセットなど）

    Parameters
    ----------
    label : str
        ボタンのテキスト
    on_click : Callable, optional
        クリック時のコールバック関数
    key : str, optional
        コンポーネントのキー
    help : str, optional
        ヘルプテキスト
    args : Tuple, optional
        コールバック関数に渡す位置引数
    kwargs : Dict[str, Any], optional
        コールバック関数に渡すキーワード引数
    use_container_width : bool, optional
        親コンテナの幅いっぱいに表示するか
    small : bool, optional
        小さいボタンとして表示するか
    icon : str, optional
        Font Awesomeアイコン名（例: "trash"）
    disabled : bool, optional
        ボタンの無効化
    confirmation : bool, optional
        確認ダイアログを表示するか
    confirmation_message : str, optional
        確認ダイアログのメッセージ

    Returns
    -------
    bool
        ボタンがクリックされ、確認された場合はTrue
    """
    # アイコンがない場合、デフォルトでexclamation-triangleを使用
    if icon is None:
        icon = "exclamation-triangle"
        
    # アイコンがある場合、ラベルの前に追加
    if icon:
        label = f"<i class='fas fa-{icon}'></i> {label}"
    
    # サイズに応じたスタイルの適用
    padding = "6px 12px" if small else "8px 16px"
    font_size = "14px" if small else "16px"

    # カスタムスタイルの定義
    custom_styles = f"""
        <style>
            div[data-testid="stButton"] > button:first-child {{
                background-color: {'#f5f5f5' if disabled else '#EF5350'};
                color: {'#9E9E9E' if disabled else 'white'};
                border: none;
                border-radius: 4px;
                padding: {padding};
                font-weight: 500;
                font-size: {font_size};
                letter-spacing: 0.3px;
                transition: all 0.2s ease;
                {'width: 100%;' if use_container_width else ''}
                {'opacity: 0.7; cursor: not-allowed;' if disabled else ''}
            }}
            div[data-testid="stButton"] > button:first-child:hover {{
                background-color: {'#f5f5f5' if disabled else '#C62828'};
                transform: {'none' if disabled else 'translateY(-1px)'};
            }}
            div[data-testid="stButton"] > button:first-child:active {{
                transform: {'none' if disabled else 'translateY(0px)'};
            }}
        </style>
    """
    
    # カスタムスタイルの適用
    st.markdown(custom_styles, unsafe_allow_html=True)
    
    # 確認が必要かつボタンが有効な場合の処理
    if confirmation and not disabled:
        # 状態管理のためのセッション変数を設定
        confirm_key = f"confirm_{key}" if key else "confirm_warning_button"
        if confirm_key not in st.session_state:
            st.session_state[confirm_key] = False
            
        # 確認ダイアログを表示するためのボタン
        if not st.session_state[confirm_key]:
            clicked = st.button(
                label,
                key=key,
                help=help,
                disabled=disabled,
                use_container_width=use_container_width
            )
            
            if clicked:
                st.session_state[confirm_key] = True
                st.experimental_rerun()
                
            return False
        else:
            # 確認ダイアログ
            st.warning(confirmation_message)
            col1, col2 = st.columns([1, 1])
            
            with col1:
                cancel = st.button("キャンセル", key=f"{key}_cancel" if key else "warning_cancel")
                if cancel:
                    st.session_state[confirm_key] = False
                    st.experimental_rerun()
                    
            with col2:
                confirm = st.button(
                    "確認する",
                    key=f"{key}_confirm" if key else "warning_confirm",
                    on_click=on_click,
                    args=args,
                    kwargs=kwargs
                )
                
                if confirm:
                    st.session_state[confirm_key] = False
                    return True
                    
            return False
    else:
        # 通常のボタン（確認なし）
        return st.button(
            label,
            key=key,
            help=help,
            on_click=on_click,
            args=args,
            kwargs=kwargs,
            disabled=disabled,
            use_container_width=use_container_width
        )

def button_group(
    buttons: List[Dict[str, Any]], 
    key_prefix: Optional[str] = None,
    equal_width: bool = True,
    align: str = "center"
) -> Dict[str, bool]:
    """
    複数のボタンをグループとして表示

    Parameters
    ----------
    buttons : List[Dict[str, Any]]
        各ボタンの定義辞書。必須キー: 'label', 'type'。
        オプションキー: 'icon', 'key', 'help', 'disabled', 'on_click', 'args', 'kwargs'。
        typeは 'primary', 'secondary', 'text', 'warning' のいずれか。
    key_prefix : str, optional
        ボタンキーのプレフィックス
    equal_width : bool, optional
        すべてのボタンを同じ幅にするか
    align : str, optional
        ボタングループの配置（'left', 'center', 'right'）

    Returns
    -------
    Dict[str, bool]
        各ボタンのクリック状態を示す辞書。キーはボタンのキーまたはラベル。
    """
    # 結果辞書（各ボタンのクリック状態を保持）
    results = {}
    
    # ボタンの数
    num_buttons = len(buttons)
    
    # 配置に応じたスタイル
    if align == "left":
        align_style = "justify-content: flex-start;"
    elif align == "right":
        align_style = "justify-content: flex-end;"
    else:  # center
        align_style = "justify-content: center;"
    
    # ボタングループのコンテナ
    st.markdown(f"""
        <div style="display: flex; flex-wrap: wrap; gap: 8px; {align_style}">
        </div>
    """, unsafe_allow_html=True)
    
    # 均等幅の場合は列を使用
    if equal_width:
        cols = st.columns(num_buttons)
        
        for i, button_def in enumerate(buttons):
            with cols[i]:
                # ボタン定義から必須パラメータを取得
                label = button_def['label']
                button_type = button_def.get('type', 'primary')
                
                # オプションパラメータを取得
                icon = button_def.get('icon')
                button_key = button_def.get('key')
                help_text = button_def.get('help')
                disabled = button_def.get('disabled', False)
                on_click = button_def.get('on_click')
                args = button_def.get('args')
                kwargs = button_def.get('kwargs')
                small = button_def.get('small', False)
                
                # キーの設定
                if not button_key:
                    button_key = f"{key_prefix}_{i}" if key_prefix else f"btn_group_{i}"
                elif key_prefix:
                    button_key = f"{key_prefix}_{button_key}"
                
                # ボタンタイプに応じたボタン生成
                clicked = False
                if button_type == 'primary':
                    clicked = primary_button(
                        label, on_click, button_key, help_text, args, kwargs,
                        use_container_width=True, small=small, icon=icon, disabled=disabled
                    )
                elif button_type == 'secondary':
                    clicked = secondary_button(
                        label, on_click, button_key, help_text, args, kwargs,
                        use_container_width=True, small=small, icon=icon, disabled=disabled
                    )
                elif button_type == 'text':
                    clicked = text_button(
                        label, on_click, button_key, help_text, args, kwargs,
                        icon=icon, disabled=disabled
                    )
                elif button_type == 'warning':
                    confirmation = button_def.get('confirmation', False)
                    confirmation_message = button_def.get('confirmation_message', "この操作を実行してもよろしいですか？")
                    clicked = warning_button(
                        label, on_click, button_key, help_text, args, kwargs,
                        use_container_width=True, small=small, icon=icon, disabled=disabled,
                        confirmation=confirmation, confirmation_message=confirmation_message
                    )
                
                # 結果に追加
                key_for_result = button_key if button_key else label
                results[key_for_result] = clicked
    else:
        # 均等幅でない場合は順番に表示
        for i, button_def in enumerate(buttons):
            # ボタン定義から必須パラメータを取得
            label = button_def['label']
            button_type = button_def.get('type', 'primary')
            
            # オプションパラメータを取得
            icon = button_def.get('icon')
            button_key = button_def.get('key')
            help_text = button_def.get('help')
            disabled = button_def.get('disabled', False)
            on_click = button_def.get('on_click')
            args = button_def.get('args')
            kwargs = button_def.get('kwargs')
            small = button_def.get('small', False)
            use_container_width = button_def.get('use_container_width', False)
            
            # キーの設定
            if not button_key:
                button_key = f"{key_prefix}_{i}" if key_prefix else f"btn_group_{i}"
            elif key_prefix:
                button_key = f"{key_prefix}_{button_key}"
            
            # ボタンタイプに応じたボタン生成
            clicked = False
            if button_type == 'primary':
                clicked = primary_button(
                    label, on_click, button_key, help_text, args, kwargs,
                    use_container_width=use_container_width, small=small, 
                    icon=icon, disabled=disabled
                )
            elif button_type == 'secondary':
                clicked = secondary_button(
                    label, on_click, button_key, help_text, args, kwargs,
                    use_container_width=use_container_width, small=small, 
                    icon=icon, disabled=disabled
                )
            elif button_type == 'text':
                clicked = text_button(
                    label, on_click, button_key, help_text, args, kwargs,
                    icon=icon, disabled=disabled
                )
            elif button_type == 'warning':
                confirmation = button_def.get('confirmation', False)
                confirmation_message = button_def.get('confirmation_message', "この操作を実行してもよろしいですか？")
                clicked = warning_button(
                    label, on_click, button_key, help_text, args, kwargs,
                    use_container_width=use_container_width, small=small, 
                    icon=icon, disabled=disabled,
                    confirmation=confirmation, confirmation_message=confirmation_message
                )
            
            # 結果に追加
            key_for_result = button_key if button_key else label
            results[key_for_result] = clicked
    
    return results

def icon_button(
    icon: str,
    label: Optional[str] = None,
    on_click: Optional[Callable] = None,
    key: Optional[str] = None,
    help: Optional[str] = None,
    args: Optional[Tuple] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    size: str = "medium",
    color: Optional[str] = None,
    disabled: bool = False,
    tooltip: Optional[str] = None
) -> bool:
    """
    アイコンのみ、またはアイコン付きラベルのボタン

    Parameters
    ----------
    icon : str
        Font Awesomeアイコン名（例: "edit", "trash"）
    label : str, optional
        ボタンのテキスト（省略するとアイコンのみになる）
    on_click : Callable, optional
        クリック時のコールバック関数
    key : str, optional
        コンポーネントのキー
    help : str, optional
        ヘルプテキスト
    args : Tuple, optional
        コールバック関数に渡す位置引数
    kwargs : Dict[str, Any], optional
        コールバック関数に渡すキーワード引数
    size : str, optional
        ボタンのサイズ（"small", "medium", "large"）
    color : str, optional
        アイコンの色（CSS色名または16進数）
    disabled : bool, optional
        ボタンの無効化
    tooltip : str, optional
        ホバー時に表示するツールチップ

    Returns
    -------
    bool
        ボタンがクリックされたかどうか
    """
    # サイズに応じたアイコンとパディングの設定
    if size == "small":
        icon_size = "16px"
        padding = "4px"
    elif size == "large":
        icon_size = "32px"
        padding = "12px"
    else:  # medium
        icon_size = "24px"
        padding = "8px"
    
    # 色の設定
    if color is None:
        color = "#1565C0"  # デフォルトはメインカラー
    
    # ボタンの表示内容
    if label:
        display_content = f"<i class='fas fa-{icon}'></i> {label}"
    else:
        display_content = f"<i class='fas fa-{icon}'></i>"
    
    # ツールチップの設定
    tooltip_attr = f"title='{tooltip}'" if tooltip else ""
    
    # カスタムHTMLボタンの生成
    button_html = f"""
    <div {tooltip_attr} style="display: inline-block;">
        <button
            onclick="Streamlit.setComponentValue({'disabled' if disabled else 'true'})"
            style="
                background-color: transparent;
                color: {color if not disabled else '#9E9E9E'};
                border: none;
                border-radius: 4px;
                padding: {padding};
                font-size: {icon_size};
                cursor: {'not-allowed' if disabled else 'pointer'};
                transition: all 0.2s ease;
                opacity: {0.7 if disabled else 1.0};
            "
            onmouseover="this.style.backgroundColor='{'' if disabled else '#F5F5F5'}'"
            onmouseout="this.style.backgroundColor='transparent'"
        >
            {display_content}
        </button>
    </div>
    """
    
    # ボタンの表示
    clicked = st.markdown(button_html, unsafe_allow_html=True)
    
    # クリック処理
    if clicked and not disabled and on_click:
        if args and kwargs:
            on_click(*args, **kwargs)
        elif args:
            on_click(*args)
        elif kwargs:
            on_click(**kwargs)
        else:
            on_click()
    
    return clicked and not disabled

def floating_action_button(
    icon: str,
    on_click: Optional[Callable] = None,
    key: Optional[str] = None,
    help: Optional[str] = None,
    args: Optional[Tuple] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    color: str = "#1565C0",
    position: str = "bottom-right",
    size: str = "large",
    tooltip: Optional[str] = None,
    disabled: bool = False
) -> bool:
    """
    フローティングアクションボタン（FAB）

    Parameters
    ----------
    icon : str
        Font Awesomeアイコン名（例: "plus", "pencil-alt"）
    on_click : Callable, optional
        クリック時のコールバック関数
    key : str, optional
        コンポーネントのキー
    help : str, optional
        ヘルプテキスト
    args : Tuple, optional
        コールバック関数に渡す位置引数
    kwargs : Dict[str, Any], optional
        コールバック関数に渡すキーワード引数
    color : str, optional
        背景色（CSS色名または16進数）
    position : str, optional
        ボタンの位置（"bottom-right", "bottom-left", "top-right", "top-left"）
    size : str, optional
        ボタンのサイズ（"medium", "large"）
    tooltip : str, optional
        ホバー時に表示するツールチップ
    disabled : bool, optional
        ボタンの無効化

    Returns
    -------
    bool
        ボタンがクリックされたかどうか
    """
    # サイズに応じた設定
    if size == "medium":
        button_size = "48px"
        icon_size = "24px"
    else:  # large
        button_size = "56px"
        icon_size = "28px"
    
    # 位置に応じた設定
    if position == "bottom-left":
        position_css = "bottom: 20px; left: 20px;"
    elif position == "top-right":
        position_css = "top: 20px; right: 20px;"
    elif position == "top-left":
        position_css = "top: 20px; left: 20px;"
    else:  # bottom-right
        position_css = "bottom: 20px; right: 20px;"
    
    # ツールチップの設定
    tooltip_attr = f"title='{tooltip}'" if tooltip else ""
    
    # カスタムHTMLボタンの生成
    button_html = f"""
    <div style="position: fixed; {position_css} z-index: 9999;" {tooltip_attr}>
        <button
            onclick="Streamlit.setComponentValue({'disabled' if disabled else 'true'})"
            style="
                width: {button_size};
                height: {button_size};
                border-radius: 50%;
                background-color: {color if not disabled else '#e0e0e0'};
                color: white;
                border: none;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                cursor: {'not-allowed' if disabled else 'pointer'};
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
                transform: scale(1);
            "
            onmouseover="this.style.transform='scale(1.1)'; this.style.boxShadow='0 6px 12px rgba(0,0,0,0.3)';"
            onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.2)';"
        >
            <i class="fas fa-{icon}" style="font-size: {icon_size};"></i>
        </button>
    </div>
    """
    
    # ボタンの表示
    clicked = st.markdown(button_html, unsafe_allow_html=True)
    
    # クリック処理
    if clicked and not disabled and on_click:
        if args and kwargs:
            on_click(*args, **kwargs)
        elif args:
            on_click(*args)
        elif kwargs:
            on_click(**kwargs)
        else:
            on_click()
    
    return clicked and not disabled
