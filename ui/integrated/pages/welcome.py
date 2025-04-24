# -*- coding: utf-8 -*-
"""
ui.integrated.pages.welcome

セーリング戦略分析システムのウェルカムページ
"""

import streamlit as st
import os
from datetime import datetime

def render_page():
    """
    ウェルカムページを表示する
    """
    # ヘッダーとイントロダクション
    st.markdown("<div class='main-header'>セーリング戦略分析システム</div>", unsafe_allow_html=True)
    
    # 2カラムレイアウト
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### システム概要
        
        セーリング戦略分析システムへようこそ！
        
        このアプリケーションは、GPSデータを活用してセーリングの風向風速を推定し、
        セーリング競技者の戦略的判断を客観的に評価するためのツールです。
        """)
        
        # 主要機能の説明
        st.markdown("""
        ### 主要機能
        
        * **風向風速推定**: GPSデータから風の状況を推定
        * **戦略的判断ポイント分析**: タック・ジャイブなどの重要な判断ポイントを特定
        * **パフォーマンス評価**: 意思決定の質とタイミングを評価
        * **データ可視化**: マップとチャートによる直感的な理解
        """)
        
        # 使い方ガイド
        with st.expander("使い方ガイド", expanded=False):
            st.markdown("""
            1. **プロジェクト作成**: 左サイドバーから「新規プロジェクト作成」を選択
            2. **データインポート**: GPSデータをアップロード
            3. **データ検証**: データの品質と整合性を確認
            4. **分析実行**: 風向風速分析、戦略判断分析などを実行
            5. **結果の確認**: マップビューや統計ダッシュボードで結果を確認
            """)
    
    with col2:
        # サイドカード: 最近のアップデート
        st.markdown("""
        ### 最新情報
        """)
        
        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
        st.markdown(f"""
        **現在のバージョン**: 1.0.0 (Beta)  
        **最終更新日**: {datetime.now().strftime('%Y-%m-%d')}
        
        **最近の更新**:
        - 統合アプリケーションの公開
        - プロジェクト管理機能の強化
        - 風推定アルゴリズムの精度向上
        """)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # クイックアクセス
        st.markdown("### クイックアクセス")
        
        # ボタングループ
        st.button("新規プロジェクト作成", 
                 on_click=lambda: st.session_state.update({"current_page": "project_create"}),
                 use_container_width=True)
        
        st.button("プロジェクト一覧", 
                 on_click=lambda: st.session_state.update({"current_page": "projects"}),
                 use_container_width=True)
    
    # フィーチャーセクション
    st.markdown("<div class='section-header'>主要機能</div>", unsafe_allow_html=True)
    
    # 3カラムのフィーチャーカード
    feat1, feat2, feat3 = st.columns(3)
    
    with feat1:
        st.markdown("#### 風向風速推定")
        st.markdown("""
        GPSデータからセーリングボートの動きを分析し、
        風向と風速を高精度に推定します。
        """)
        
    with feat2:
        st.markdown("#### 戦略判断の分析")
        st.markdown("""
        タック・ジャイブなどの重要な戦略的判断ポイントを
        特定し、その質とタイミングを評価します。
        """)
        
    with feat3:
        st.markdown("#### データ可視化")
        st.markdown("""
        マップ上の軌跡表示、風のベクトル表示、
        統計グラフなどで分析結果を直感的に理解できます。
        """)
    
    # フッター
    st.markdown("---")
    st.markdown("セーリング戦略分析システム - 開発中のベータ版")

if __name__ == "__main__":
    render_page()
