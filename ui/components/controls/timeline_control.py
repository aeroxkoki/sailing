"""
セーリング戦略分析システム - タイムラインコントロールコンポーネント

トラッキングデータの時間調整のためのコントロールを提供します。
"""

import streamlit as st
import pandas as pd
import datetime

def create_timeline_control(track_data, callback=None):
    """
    トラックデータの時間調整コントロールを作成
    
    Parameters:
    -----------
    track_data : list or pandas.DataFrame
        GPSトラックデータ
    callback : function, optional
        スライダー値が変更された時に呼び出される関数
    
    Returns:
    --------
    int
        現在選択されている時間インデックス
    """
    # スタイルの適用
    st.markdown("""
    <style>
    .timeline-container {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin-top: 15px;
    }
    
    .timeline-controls {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }
    
    .timeline-button {
        background-color: #1565C0;
        color: white;
        border: none;
        border-radius: 50%;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        margin-right: 10px;
    }
    
    .timeline-info {
        margin-left: 15px;
        flex-grow: 1;
    }
    
    .timeline-speed {
        margin-left: auto;
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
        # Streamlit 1.31.0との互換性を確保するため、リストではなくタプルを使用
        cols = st.columns((1, 1, 1, 5, 2))
        
        # 再生/一時停止ボタン
        play_icon = "⏸️" if st.session_state.timeline_playing else "▶️"
        if cols[0].button(play_icon, key="timeline_play_button"):
            st.session_state.timeline_playing = not st.session_state.timeline_playing
        
        # 前へボタン
        if cols[1].button("⏪", key="timeline_prev_button"):
            st.session_state.timeline_index = max(0, st.session_state.timeline_index - 1)
            if callback:
                callback(st.session_state.timeline_index)
        
        # 次へボタン
        if cols[2].button("⏩", key="timeline_next_button"):
            st.session_state.timeline_index = min(data_length - 1, st.session_state.timeline_index + 1)
            if callback:
                callback(st.session_state.timeline_index)
        
        # タイムラインスライダー
        new_index = cols[3].slider(
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
        
        # 再生速度選択
        speed_options = {
            "0.5x": 0.5,
            "1x": 1.0, 
            "2x": 2.0,
            "5x": 5.0
        }
        
        selected_speed = cols[4].selectbox(
            "再生速度",
            list(speed_options.keys()),
            index=list(speed_options.values()).index(st.session_state.timeline_speed),
            label_visibility="collapsed",
            key="timeline_speed_select"
        )
        
        st.session_state.timeline_speed = speed_options[selected_speed]
    
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
