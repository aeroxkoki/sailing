"""
セーリング戦略分析システム - タイムラインコントロールコンポーネント

トラッキングデータの時間調整のためのコントロールを提供します。
"""

import streamlit as st
import pandas as pd
import datetime

def create_timeline_control(track_data, callback=None, show_key_points=True):
    """
    拡張トラックデータ時間調整コントロールを作成
    
    Parameters:
    -----------
    track_data : list or pandas.DataFrame
        GPSトラックデータ
    callback : function, optional
        スライダー値が変更された時に呼び出される関数
    show_key_points : bool
        戦略ポイントなどの重要ポイントをタイムラインに表示するか
        
    Returns:
    --------
    int
        現在選択されている時間インデックス
    """
    # 拡張スタイルの適用
    st.markdown("""
    <style>
    .timeline-container {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin: 0;
    }
    
    .timeline-controls {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
    }
    
    .timeline-button {
        background-color: #1565C0;
        color: white;
        border: none;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        margin-right: 8px;
    }
    
    .timeline-info {
        margin-left: 12px;
        flex-grow: 1;
        font-size: 14px;
    }
    
    .timeline-speed {
        margin-left: auto;
    }
    
    .timeline-track {
        position: relative;
        height: 10px;
        margin-top: 8px;
    }
    
    .timeline-marker {
        position: absolute;
        width: 8px;
        height: 8px;
        background-color: #ff5722;
        border-radius: 50%;
        top: -4px;
        transform: translateX(-50%);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # データの準備
    if isinstance(track_data, pd.DataFrame):
        # DataFrameの場合
        data_length = len(track_data)
        
        # 時間情報の取得
        if 'timestamp' in track_data.columns:
            timestamps = track_data['timestamp'].tolist()
        else:
            # タイムスタンプがない場合は仮のタイムスタンプを生成
            start_time = datetime.datetime.now().replace(hour=12, minute=0, second=0)
            timestamps = [start_time + datetime.timedelta(seconds=i*5) for i in range(data_length)]
    else:
        # リストの場合
        data_length = len(track_data)
        
        # 時間情報の取得
        if data_length > 0 and 'timestamp' in track_data[0]:
            timestamps = [item['timestamp'] for item in track_data]
        else:
            # タイムスタンプがない場合は仮のタイムスタンプを生成
            start_time = datetime.datetime.now().replace(hour=12, minute=0, second=0)
            timestamps = [start_time + datetime.timedelta(seconds=i*5) for i in range(data_length)]
    
    # タイムライン用のセッション状態
    if 'timeline_index' not in st.session_state:
        st.session_state.timeline_index = 0
    
    if 'timeline_playing' not in st.session_state:
        st.session_state.timeline_playing = False
    
    if 'timeline_speed' not in st.session_state:
        st.session_state.timeline_speed = 1.0
    
    # インデックスが範囲内かチェック
    st.session_state.timeline_index = min(max(0, st.session_state.timeline_index), data_length - 1)
    
    # コントロールレイアウト
    # Streamlit 1.31.0との互換性を確保するため、リストではなくタプルを使用
    col1, col2 = st.columns((1, 7))
    
    # 現在の時間表示
    if isinstance(timestamps[st.session_state.timeline_index], datetime.datetime):
        current_time = timestamps[st.session_state.timeline_index].strftime('%H:%M:%S')
    else:
        current_time = str(timestamps[st.session_state.timeline_index])
    
    with col1:
        st.markdown(f'<div style="font-size: 20px; font-weight: bold;">{current_time}</div>', unsafe_allow_html=True)
    
    # 再生コントロールと速度選択
    with col2:
        # Streamlit 1.31.0の互換性問題対応: 個別のコンポーネントに分割
        play_col = st.container()
        prev_col = st.container()
        next_col = st.container()
        slider_col = st.container()
        speed_col = st.container()
        
        # レイアウト調整用のスタイル
        st.markdown("""
        <style>
        .control-container {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .button-container {
            width: 15%;
            float: left;
            display: inline-block;
        }
        .slider-container {
            width: 55%;
            float: left;
            display: inline-block;
            margin-left: 10px;
            margin-right: 10px;
        }
        .speed-container {
            width: 15%;
            float: left;
            display: inline-block;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # コントロールを横並びにするためのコンテナ
        st.markdown('<div class="control-container">', unsafe_allow_html=True)
        
        # 再生/一時停止ボタン
        st.markdown('<div class="button-container">', unsafe_allow_html=True)
        play_icon = "⏸️" if st.session_state.timeline_playing else "▶️"
        if st.button(play_icon, key="timeline_play_button"):
            st.session_state.timeline_playing = not st.session_state.timeline_playing
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 前へボタン
        st.markdown('<div class="button-container">', unsafe_allow_html=True)
        if st.button("⏪", key="timeline_prev_button"):
            st.session_state.timeline_index = max(0, st.session_state.timeline_index - 1)
            if callback:
                callback(st.session_state.timeline_index)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 次へボタン
        st.markdown('<div class="button-container">', unsafe_allow_html=True)
        if st.button("⏩", key="timeline_next_button"):
            st.session_state.timeline_index = min(data_length - 1, st.session_state.timeline_index + 1)
            if callback:
                callback(st.session_state.timeline_index)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # タイムラインスライダー
        st.markdown('<div class="slider-container">', unsafe_allow_html=True)
        new_index = st.slider(
            "タイムライン",
            0, data_length - 1, 
            st.session_state.timeline_index,
            label_visibility="collapsed",
            key="timeline_slider"
        )
        
        if new_index != st.session_state.timeline_index:
            st.session_state.timeline_index = new_index
            if callback:
                callback(st.session_state.timeline_index)
        
        # もし重要ポイントを表示する場合
        if show_key_points:
            # サンプルの重要ポイント（実際の実装では計算する）
            key_points = [
                {'index': int(data_length * 0.2), 'type': 'tack', 'color': '#ff5722'},
                {'index': int(data_length * 0.5), 'type': 'windshift', 'color': '#2196f3'},
                {'index': int(data_length * 0.7), 'type': 'layline', 'color': '#4caf50'}
            ]
            
            # マーカーHTMLを生成
            markers_html = ""
            for point in key_points:
                position = (point['index'] / (data_length - 1)) * 100
                markers_html += f"""
                <div class="timeline-marker" style="left: {position}%; background-color: {point['color']};"
                     title="{point['type']}"></div>
                """
            
            # マーカーを表示
            st.markdown(f"""
            <div class="timeline-track">
                {markers_html}
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 再生速度選択（よりコンパクトに）
        st.markdown('<div class="speed-container">', unsafe_allow_html=True)
        speed_options = {"1x": 1.0, "2x": 2.0}
        selected_speed = st.selectbox(
            "速度",
            list(speed_options.keys()),
            index=list(speed_options.values()).index(st.session_state.timeline_speed if st.session_state.timeline_speed in speed_options.values() else 1.0),
            label_visibility="collapsed",
            key="timeline_speed_select"
        )
        st.session_state.timeline_speed = speed_options[selected_speed]
        st.markdown('</div>', unsafe_allow_html=True)
        
        # コンテナ終了
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 自動再生制御（Javascriptを使用）
    if st.session_state.timeline_playing:
        auto_play_js = f"""
        <script>
            function nextFrame() {{
                if (window.playing) {{
                    const slider = document.querySelector('div[data-testid="stSlider"] input');
                    if (slider) {{
                        let value = parseInt(slider.value);
                        if (value < {data_length - 1}) {{
                            value += 1;
                            slider.value = value;
                            
                            // スライダー値の変更イベントをトリガー
                            const event = new Event('change', {{ 'bubbles': true }});
                            slider.dispatchEvent(event);
                        }} else {{
                            window.playing = false;
                        }}
                    }}
                }}
                
                // 再生速度に応じて次フレームをスケジュール
                setTimeout(nextFrame, {1000 / st.session_state.timeline_speed});
            }}
            
            window.playing = true;
            nextFrame();
        </script>
        """
        st.markdown(auto_play_js, unsafe_allow_html=True)
    
    return st.session_state.timeline_index
