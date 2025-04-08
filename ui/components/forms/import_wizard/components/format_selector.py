"""
ui.components.forms.import_wizard.components.format_selector

ファイル形式選択コンポーネント
"""

import streamlit as st
from typing import Dict, List, Any, Optional


def format_selector_card(formats: List[Dict[str, str]], 
                         selected_format: Optional[str] = None,
                         on_select: Optional[callable] = None,
                         key: str = "format_selector"):
    """
    ファイル形式選択カードUIを描画
    
    Parameters
    ----------
    formats : List[Dict[str, str]]
        サポートされるファイル形式のリスト（name, icon, ext, descを含む辞書）
    selected_format : Optional[str], optional
        現在選択されている形式, by default None
    on_select : Optional[callable], optional
        選択時のコールバック関数, by default None
    key : str, optional
        コンポーネントキー, by default "format_selector"
    
    Returns
    -------
    str
        選択されたファイル形式
    """
    st.write("### インポートするファイル形式を選択")
    
    # カードスタイルのレイアウト
    col1, col2 = st.columns(2)
    selected = selected_format
    
    for i, format_info in enumerate(formats):
        # 2列レイアウト用の列を選択
        col = col1 if i % 2 == 0 else col2
        
        # カードのCSSスタイル
        card_style = """
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        transition: all 0.3s;
        """
        
        if selected_format == format_info["name"]:
            card_style += """
            border-color: #1E88E5;
            background-color: #E3F2FD;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            """
        
        # カードコンテナ
        with col:
            with st.container():
                # スタイルタグ付きのdivでラップ
                st.markdown(f"<div style='{card_style}'>", unsafe_allow_html=True)
                
                # カードのコンテンツ
                st.markdown(f"<h3 style='margin: 0; font-size: 1.2em;'>{format_info['icon']} {format_info['name']}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='margin: 5px 0; font-size: 0.9em; color: #666;'>{format_info['desc']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='margin: 0; font-size: 0.8em; color: #999;'>ファイル拡張子: .{format_info['ext']}</p>", unsafe_allow_html=True)
                
                # 選択ボタン
                btn_label = "選択中" if selected_format == format_info["name"] else "選択"
                btn_type = "primary" if selected_format == format_info["name"] else "secondary"
                
                if st.button(btn_label, key=f"{key}_{format_info['name']}", 
                             type=btn_type, use_container_width=True):
                    selected = format_info["name"]
                    if on_select:
                        on_select(format_info["name"])
                
                st.markdown("</div>", unsafe_allow_html=True)
    
    return selected


def format_features_info(format_name: str):
    """
    選択されたファイル形式の特徴と機能を表示
    
    Parameters
    ----------
    format_name : str
        ファイル形式名
    """
    # 形式別の機能説明
    features = {
        "CSV": {
            "title": "CSV (Comma-Separated Values)",
            "description": "CSVは最も一般的なデータ交換形式で、様々なGPSデバイスやアプリケーションから出力されます。",
            "features": [
                "複数のデータソースで利用可能",
                "シンプルなテキスト形式で編集が容易",
                "カスタム列マッピングに対応",
                "区切り記号のカスタマイズが可能（カンマ、タブ、セミコロンなど）"
            ],
            "limitations": [
                "標準的なデータ構造がないため列名が異なる場合がある",
                "メタデータが含まれないことが多い"
            ]
        },
        "GPX": {
            "title": "GPX (GPS Exchange Format)",
            "description": "XMLベースのGPSデータ交換フォーマットで、ウェイポイント、ルート、トラックを格納できます。",
            "features": [
                "地理情報システムで広くサポートされている標準形式",
                "ウェイポイント、ルート、トラックをサポート",
                "拡張データ（高度、心拍数など）にも対応",
                "詳細なメタデータを含むことが可能"
            ],
            "limitations": [
                "ファイルサイズが大きくなりがち",
                "一部のGPSデバイスでは完全にサポートされていない場合がある"
            ]
        },
        "TCX": {
            "title": "TCX (Training Center XML)",
            "description": "Garminが開発したフィットネストレーニングデータに特化したXML形式です。",
            "features": [
                "マルチスポーツのワークアウトデータに最適",
                "心拍数やケイデンスなどの詳細な運動データをサポート",
                "ラップ情報やコースデータを含むことが可能",
                "拡張性の高いXML構造"
            ],
            "limitations": [
                "Garmin製品との互換性が高いが、他製品では制限がある場合も",
                "GPXよりも複雑な構造"
            ]
        },
        "FIT": {
            "title": "FIT (Flexible and Interoperable Data Transfer)",
            "description": "コンパクトなバイナリ形式で、スポーツデバイスで広く使用されています。",
            "features": [
                "非常にコンパクトなバイナリ形式",
                "高度なフィットネスデータ（パワー、運動学的データなど）",
                "マルチスポーツセッションのサポート",
                "ストレージ効率が高いためウェアラブルデバイスで人気"
            ],
            "limitations": [
                "専用のライブラリが必要で汎用性が低い",
                "テキストエディタで直接編集できない"
            ]
        }
    }
    
    # 選択された形式の情報がない場合
    if format_name not in features:
        st.info(f"{format_name}形式の詳細情報はありません。")
        return
    
    info = features[format_name]
    
    # 情報表示
    st.write(f"### {info['title']}")
    st.write(info['description'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**主な特徴:**")
        for feature in info['features']:
            st.markdown(f"- {feature}")
    
    with col2:
        st.write("**制限事項:**")
        for limitation in info['limitations']:
            st.markdown(f"- {limitation}")
