"""
セーリング戦略分析システム - ファイルアップローダーコンポーネント

ファイルアップロードを提供するコンポーネントです。
"""

import streamlit as st
from ..styles import Colors, BorderRadius, FontSizes, Spacing, Transitions, FontWeights

def create_file_uploader(
    label,
    type=None,
    accept_multiple_files=False,
    help=None,
    key=None,
    label_visibility="visible"
):
    """
    ファイルアップローダーを作成します。
    
    Parameters:
    -----------
    label : str
        ファイルアップローダーのラベル
    type : str or list of str, optional
        受け入れるファイルタイプ（例: ["csv", "txt"], "pdf"）
    accept_multiple_files : bool, optional
        複数ファイルのアップロードを許可するかどうか
    help : str, optional
        ヘルプテキスト
    key : str, optional
        コンポーネントの一意のキー
    label_visibility : str, optional
        ラベルの表示設定 ("visible", "hidden", "collapsed")
        
    Returns:
    --------
    file or list of files
        アップロードされたファイル（複数の場合はリスト）
    """
    # CSSスタイルの定義
    uploader_style = f"""
    <style>
    div[data-testid="stFileUploader"] label {{
        font-size: {FontSizes.BODY};
        color: {Colors.DARK_2};
        font-weight: 500;
        margin-bottom: {Spacing.XS};
    }}
    
    div[data-testid="stFileUploader"] div[data-testid="stFileUploadDropzone"] {{
        background-color: {Colors.WHITE};
        border: 1px dashed {Colors.GRAY_MID};
        border-radius: {BorderRadius.SMALL};
        transition: border-color {Transitions.FAST} ease-out;
        padding: {Spacing.M};
    }}
    
    div[data-testid="stFileUploader"] div[data-testid="stFileUploadDropzone"]:hover {{
        border-color: {Colors.PRIMARY};
        background-color: {Colors.GRAY_1};
    }}
    
    div[data-testid="stFileUploader"] div[data-testid="stFileUploadDropzone"] p {{
        font-size: {FontSizes.BODY};
        color: {Colors.DARK_1};
    }}
    
    div[data-testid="stFileUploader"] button[kind="primary"] {{
        background-color: {Colors.PRIMARY};
        color: {Colors.WHITE};
        border: none;
        border-radius: {BorderRadius.SMALL};
        padding: 0.5rem 1rem;
        font-weight: {FontWeights.MEDIUM};
        transition: all {Transitions.FAST} ease-out;
    }}
    
    div[data-testid="stFileUploader"] button[kind="primary"]:hover {{
        background-color: #0D47A1;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    div[data-testid="stFileUploader"] div[data-testid="stUploadedFileList"] {{
        margin-top: {Spacing.S};
    }}
    
    div[data-testid="stFileUploader"] div[data-testid="stUploadedFileList"] div {{
        background-color: {Colors.WHITE};
        border: 1px solid {Colors.GRAY_2};
        border-radius: {BorderRadius.SMALL};
        padding: {Spacing.XS} {Spacing.S};
        margin-bottom: {Spacing.XS};
    }}
    </style>
    """
    
    st.markdown(uploader_style, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        label=label,
        type=type,
        accept_multiple_files=accept_multiple_files,
        help=help,
        key=key,
        label_visibility=label_visibility
    )
    
    return uploaded_files
