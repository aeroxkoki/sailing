"""
セーリング戦略分析システム - スタイル定義

UI/UXデザインガイドラインに基づいたスタイル定義とユーティリティ関数
"""

import streamlit as st

# カラーパレット
class Colors:
    # ブランドカラー
    PRIMARY = "#1565C0"
    SECONDARY = "#00ACC1"
    
    # アクセントカラー
    ALERT = "#E63946"
    SAILING_YELLOW = "#FFD700"
    
    # 中性色
    WHITE = "#FFFFFF"
    GRAY_1 = "#F5F5F5"
    GRAY_2 = "#E0E0E0"
    GRAY_MID = "#9E9E9E"
    DARK_1 = "#616161"
    DARK_2 = "#212121"
    
    # 状態色
    SUCCESS = "#26A69A"
    WARNING = "#FFA726"
    ERROR = "#EF5350"
    INFO = "#2196F3"
    
    # チャートカラー
    CHART_COLORS = [
        "#1565C0",  # プライマリ
        "#26A69A",  # 緑青
        "#FFA726",  # オレンジ
        "#5C6BC0",  # 青紫
        "#66BB6A",  # 緑
        "#EF5350",  # 赤
        "#7E57C2",  # 紫
        "#FFEE58",  # 黄色
    ]


# スペーシング
class Spacing:
    XS = "4px"
    S = "8px"
    M = "16px"
    L = "24px"
    XL = "32px"
    XXL = "48px"
    XXXL = "64px"


# シャドウ
class Shadows:
    SHADOW_1 = "0 2px 4px rgba(0,0,0,0.1)"
    SHADOW_2 = "0 4px 8px rgba(0,0,0,0.15)"
    SHADOW_3 = "0 8px 16px rgba(0,0,0,0.2)"


# 角丸
class BorderRadius:
    SMALL = "4px"
    MEDIUM = "8px"
    LARGE = "16px"


# トランジション時間
class Transitions:
    INSTANT = "100ms"
    FAST = "200ms"
    NORMAL = "300ms"
    SLOW = "500ms"


# フォントサイズ
class FontSizes:
    XLARGE_HEADING = "48px"  # 3rem
    LARGE_HEADING = "36px"   # 2.25rem
    MEDIUM_HEADING = "30px"  # 1.875rem
    SMALL_HEADING = "24px"   # 1.5rem
    TITLE = "20px"           # 1.25rem
    SUBTITLE = "18px"        # 1.125rem
    BODY_LARGE = "16px"      # 1rem
    BODY = "14px"            # 0.875rem
    SMALL = "12px"           # 0.75rem


# フォントウェイト
class FontWeights:
    NORMAL = "400"
    MEDIUM = "500"
    SEMIBOLD = "600"
    BOLD = "700"


# グローバルCSS適用関数
def apply_global_css():
    """
    グローバルCSSをStreamlitアプリケーションに適用する
    """
    css = f"""
    <style>
        /* ベースカラーとタイポグラフィ */
        .main {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, 
                       Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            color: {Colors.DARK_2};
        }}
        
        /* ヘッダースタイル */
        .main h1 {{
            color: {Colors.DARK_2};
            font-weight: {FontWeights.BOLD};
            font-size: {FontSizes.LARGE_HEADING};
            line-height: 1.2;
            padding-top: {Spacing.M};
            padding-bottom: {Spacing.M};
        }}
        
        .main h2 {{
            color: {Colors.DARK_2};
            font-weight: {FontWeights.BOLD};
            font-size: {FontSizes.MEDIUM_HEADING};
            line-height: 1.2;
            padding-top: {Spacing.S};
            padding-bottom: {Spacing.S};
        }}
        
        .main h3 {{
            color: {Colors.DARK_2};
            font-weight: {FontWeights.BOLD};
            font-size: {FontSizes.SMALL_HEADING};
            line-height: 1.2;
            padding-top: {Spacing.S};
            padding-bottom: {Spacing.XS};
        }}
        
        /* リンクスタイル */
        .main a {{
            color: {Colors.PRIMARY};
            text-decoration: none;
        }}
        
        .main a:hover {{
            text-decoration: underline;
        }}
        
        /* ウィジェット全体のスタイル */
        div.stButton > button:first-child {{
            background-color: {Colors.PRIMARY};
            color: {Colors.WHITE};
            border: none;
            border-radius: {BorderRadius.SMALL};
            padding: 0.5rem 1rem;
            font-weight: {FontWeights.MEDIUM};
            transition: all {Transitions.FAST} ease-out;
        }}
        
        div.stButton > button:hover {{
            background-color: #0D47A1;
            box-shadow: {Shadows.SHADOW_1};
        }}
        
        /* 入力フィールドのスタイル */
        div.stTextInput > div > div > input {{
            border: 1px solid {Colors.GRAY_2};
            border-radius: {BorderRadius.SMALL};
            padding: 8px 12px;
            transition: all {Transitions.FAST} ease-out;
        }}
        
        div.stTextInput > div > div > input:focus {{
            border-color: {Colors.PRIMARY};
            box-shadow: 0 0 0 1px {Colors.PRIMARY};
        }}
        
        /* セレクトボックスのスタイル */
        div.stSelectbox > div > div > select {{
            border: 1px solid {Colors.GRAY_2};
            border-radius: {BorderRadius.SMALL};
            padding: 8px 12px;
            transition: all {Transitions.FAST} ease-out;
        }}
        
        div.stSelectbox > div > div > select:focus {{
            border-color: {Colors.PRIMARY};
            box-shadow: 0 0 0 1px {Colors.PRIMARY};
        }}
        
        /* ダークモード対応 */
        @media (prefers-color-scheme: dark) {{
            .main {{
                color: {Colors.GRAY_1};
            }}
            
            .main h1, .main h2, .main h3 {{
                color: {Colors.WHITE};
            }}
        }}
        
        /* カスタムカードスタイル */
        .card {{
            background-color: {Colors.WHITE};
            border-radius: {BorderRadius.MEDIUM};
            padding: {Spacing.M};
            box-shadow: {Shadows.SHADOW_1};
            margin-bottom: {Spacing.M};
        }}
        
        .card-title {{
            font-size: {FontSizes.TITLE};
            font-weight: {FontWeights.SEMIBOLD};
            margin-bottom: {Spacing.S};
        }}
        
        .card-subtitle {{
            font-size: {FontSizes.SUBTITLE};
            color: {Colors.DARK_1};
            margin-bottom: {Spacing.S};
        }}
        
        .card-content {{
            font-size: {FontSizes.BODY};
            line-height: 1.5;
        }}
        
        /* アラートスタイル */
        .alert {{
            padding: {Spacing.S} {Spacing.M};
            border-radius: {BorderRadius.SMALL};
            margin-bottom: {Spacing.M};
        }}
        
        .alert-info {{
            background-color: #E3F2FD;
            border-left: 4px solid {Colors.INFO};
        }}
        
        .alert-success {{
            background-color: #E8F5E9;
            border-left: 4px solid {Colors.SUCCESS};
        }}
        
        .alert-warning {{
            background-color: #FFF3E0;
            border-left: 4px solid {Colors.WARNING};
        }}
        
        .alert-error {{
            background-color: #FFEBEE;
            border-left: 4px solid {Colors.ERROR};
        }}
        
        /* テーブルスタイル */
        .stDataFrame {{
            border: 1px solid {Colors.GRAY_2};
            border-radius: {BorderRadius.SMALL};
            overflow: hidden;
        }}
        
        .stDataFrame thead tr th {{
            background-color: {Colors.GRAY_1};
            color: {Colors.DARK_2};
            font-weight: {FontWeights.SEMIBOLD};
            padding: {Spacing.S} {Spacing.M};
            text-align: left;
        }}
        
        .stDataFrame tbody tr:nth-child(even) {{
            background-color: {Colors.WHITE};
        }}
        
        .stDataFrame tbody tr:nth-child(odd) {{
            background-color: {Colors.GRAY_1};
        }}
        
        .stDataFrame tbody tr:hover {{
            background-color: #E3F2FD;
        }}
        
        /* タブスタイル */
        .stTabs [data-baseweb="tab-list"] {{
            gap: {Spacing.XS};
        }}
        
        .stTabs [data-baseweb="tab"] {{
            padding: {Spacing.S} {Spacing.M};
            border-radius: {BorderRadius.SMALL} {BorderRadius.SMALL} 0 0;
        }}
        
        .stTabs [aria-selected="true"] {{
            background-color: {Colors.WHITE};
            border-bottom: 2px solid {Colors.PRIMARY};
            color: {Colors.PRIMARY};
            font-weight: {FontWeights.SEMIBOLD};
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ユーティリティ関数
def create_custom_card(title=None, subtitle=None, content=None, footer=None):
    """
    カスタムカードコンポーネントを作成する

    Parameters:
    -----------
    title : str, optional
        カードのタイトル
    subtitle : str, optional
        カードのサブタイトル
    content : str, optional
        カードの本文内容
    footer : str, optional
        カードのフッター内容
    """
    card_html = f"""
    <div class="card">
        {f'<div class="card-title">{title}</div>' if title else ''}
        {f'<div class="card-subtitle">{subtitle}</div>' if subtitle else ''}
        {f'<div class="card-content">{content}</div>' if content else ''}
        {f'<div class="card-footer" style="margin-top: 16px; padding-top: 8px; border-top: 1px solid {Colors.GRAY_2};">{footer}</div>' if footer else ''}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def create_alert(message, alert_type="info"):
    """
    アラートコンポーネントを作成する

    Parameters:
    -----------
    message : str
        アラートに表示するメッセージ
    alert_type : str, optional
        アラートのタイプ ("info", "success", "warning", "error")
    """
    alert_html = f"""
    <div class="alert alert-{alert_type}">
        {message}
    </div>
    """
    st.markdown(alert_html, unsafe_allow_html=True)


def create_spacer(size="M"):
    """
    スペーサーを作成する

    Parameters:
    -----------
    size : str, optional
        スペーサーのサイズ ("XS", "S", "M", "L", "XL", "XXL", "XXXL")
    """
    spacing = getattr(Spacing, size, Spacing.M)
    spacer_html = f"""
    <div style="margin-top: {spacing};"></div>
    """
    st.markdown(spacer_html, unsafe_allow_html=True)


def create_divider(margin="M"):
    """
    区切り線を作成する

    Parameters:
    -----------
    margin : str, optional
        区切り線の上下マージン ("XS", "S", "M", "L", "XL")
    """
    spacing = getattr(Spacing, margin, Spacing.M)
    divider_html = f"""
    <hr style="border: 0; height: 1px; background-color: {Colors.GRAY_2}; margin: {spacing} 0;" />
    """
    st.markdown(divider_html, unsafe_allow_html=True)
