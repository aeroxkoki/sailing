"""
ui.demo_post_race モジュール

レース後戦略分析エンジンの機能をデモンストレーションするためのStreamlitアプリケーションです。
戦略評価、重要ポイント分析、改善提案など、レース後分析機能の操作と表示を提供します。
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
import json
import os
import sys

# 親ディレクトリをパスに追加（インポート用）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 内部モジュールのインポート
from sailing_data_processor.analysis.post_race_analyzer import PostRaceAnalyzer
from sailing_data_processor.visualization.strategy_visualization import StrategyVisualizer
from ui.components.analysis.post_race_panel import post_race_analysis_panel

def load_demo_data():
    """デモ用のサンプルデータをロード"""
    # サンプルデータの場所
    data_dir = os.path.join(parent_dir, "simulation_data")
    
    # トラックデータのロード
    try:
        # 最新のシミュレーションファイルを探す
        track_files = [f for f in os.listdir(data_dir) if f.startswith('standard_simulation_') and f.endswith('.csv')]
        if track_files:
            # 最新のファイルを使用
            track_files.sort(reverse=True)
            track_path = os.path.join(data_dir, track_files[0])
            track_data = pd.read_csv(track_path)
            
            # タイムスタンプ列を日時型に変換
            if 'timestamp' in track_data.columns:
                track_data['timestamp'] = pd.to_datetime(track_data['timestamp'])
                
            st.success(f"トラックデータを正常にロードしました: {track_files[0]}")
        else:
            # サンプルデータがない場合はダミーデータを生成
            track_data = generate_dummy_track_data()
            st.warning("サンプルデータが見つからないため、ダミーデータを生成しました。")
    except Exception as e:
        st.error(f"トラックデータのロード中にエラーが発生しました: {str(e)}")
        track_data = generate_dummy_track_data()
    
    # 風データの生成（実際のデータがない場合）
    try:
        # 対応するメタデータファイルを探す
        metadata_files = [f for f in os.listdir(data_dir) if f.startswith('standard_metadata_') and f.endswith('.json')]
        if metadata_files:
            # トラックデータに対応するメタデータを使用
            track_id = track_files[0].replace('standard_simulation_', '').replace('.csv', '')
            metadata_file = f"standard_metadata_{track_id}.json"
            
            if metadata_file in metadata_files:
                metadata_path = os.path.join(data_dir, metadata_file)
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # メタデータから風データを抽出
                if 'wind_data' in metadata:
                    wind_data = create_wind_data_from_metadata(metadata['wind_data'], track_data)
                    st.success(f"風データを正常にロードしました: {metadata_file}")
                else:
                    wind_data = generate_dummy_wind_data(track_data)
                    st.info("メタデータに風情報がないため、ダミー風データを生成しました。")
            else:
                wind_data = generate_dummy_wind_data(track_data)
                st.info("対応するメタデータが見つからないため、ダミー風データを生成しました。")
        else:
            wind_data = generate_dummy_wind_data(track_data)
            st.info("メタデータが見つからないため、ダミー風データを生成しました。")
    except Exception as e:
        st.error(f"風データのロード中にエラーが発生しました: {str(e)}")
        wind_data = generate_dummy_wind_data(track_data)
    
    # コースデータの生成（デモ用）
    try:
        course_data = generate_demo_course_data(track_data)
    except Exception as e:
        st.error(f"コースデータの生成中にエラーが発生しました: {str(e)}")
        course_data = None
    
    return {
        "track_data": track_data,
        "wind_data": wind_data,
        "course_data": course_data,
        "competitor_data": None  # デモでは競合艇データはなし
    }

def generate_dummy_track_data():
    """デモ用のダミートラックデータを生成"""
    # 開始時刻（現在時刻の1時間前）
    start_time = datetime.now() - timedelta(hours=1)
    
    # データポイント数
    n_points = 500
    
    # タイムスタンプの生成（1秒間隔）
    timestamps = [start_time + timedelta(seconds=i) for i in range(n_points)]
    
    # 緯度経度の生成（シンプルな周回コース - 四角形に近い）
    center_lat, center_lon = 35.6, 139.7  # 東京付近
    
    # コースの形状を定義（四角形のコーナー位置）
    corners = [
        (0.008, 0.008),   # 右上
        (0.008, -0.008),  # 右下
        (-0.008, -0.008), # 左下
        (-0.008, 0.008),  # 左上
    ]
    
    # 各辺のポイント数
    points_per_edge = n_points // 4
    
    latitudes = []
    longitudes = []
    
    # 四角形の各辺に沿ってポイントを配置
    for i in range(4):
        start_corner = corners[i]
        end_corner = corners[(i+1) % 4]
        
        for j in range(points_per_edge):
            # 線形補間
            ratio = j / points_per_edge
            dlat = start_corner[0] * (1 - ratio) + end_corner[0] * ratio
            dlon = start_corner[1] * (1 - ratio) + end_corner[1] * ratio
            
            latitudes.append(center_lat + dlat)
            longitudes.append(center_lon + dlon)
    
    # 余りのポイントを最後の辺に追加
    remaining = n_points - len(latitudes)
    for i in range(remaining):
        latitudes.append(center_lat + corners[0][0])
        longitudes.append(center_lon + corners[0][1])
    
    # 速度の生成（5〜8ノット、風向によって変動）
    speeds = []
    headings = []
    
    for i in range(n_points):
        # 現在のエッジを特定
        edge = min(i // points_per_edge, 3)
        
        # エッジごとの方向
        directions = [0, 90, 180, 270]  # 北、東、南、西
        heading = directions[edge]
        
        # 風に対する姿勢によって速度が変わる
        # 風上：遅い、風下：速い
        wind_angle = (heading - 225) % 360  # 風向225度と艇の向きの差
        rel_wind_effect = abs(wind_angle - 180) / 180.0  # 0:真風下、1:真風上
        
        speed = 7.5 - 2.5 * rel_wind_effect + 0.5 * np.random.randn()  # 5〜8ノット + ノイズ
        
        speeds.append(max(4.0, min(9.0, speed)))  # 4〜9ノットに制限
        headings.append(heading)
    
    # VMGの生成（速度の60〜90%）
    vmg = []
    for i in range(n_points):
        wind_angle = (headings[i] - 225) % 360
        vmg_ratio = 0.9 - 0.3 * abs(wind_angle - 180) / 180.0  # 風下で高い、風上で低い
        vmg.append(speeds[i] * vmg_ratio)
    
    # 効率の計算
    efficiency = [v / s if s > 0 else 0.7 for v, s in zip(vmg, speeds)]
    
    # データフレームの作成
    data = {
        'timestamp': timestamps,
        'latitude': latitudes,
        'longitude': longitudes,
        'speed': speeds,
        'vmg': vmg,
        'heading': headings,
        'efficiency': efficiency
    }
    
    return pd.DataFrame(data)

def generate_dummy_wind_data(track_data):
    """デモ用のダミー風データを生成"""
    # トラックデータのタイムスタンプを使用
    if track_data is None or 'timestamp' not in track_data.columns:
        # 開始時刻（現在時刻の1時間前）
        start_time = datetime.now() - timedelta(hours=1)
        # データポイント数
        n_points = 500
        # タイムスタンプの生成（1秒間隔）
        timestamps = [start_time + timedelta(seconds=i) for i in range(n_points)]
    else:
        timestamps = track_data['timestamp'].tolist()
    
    n_points = len(timestamps)
    
    # 風向の生成（徐々に変化する、225度を中心に±20度）
    base_direction = 225
    direction_variation = 20
    time_points = np.linspace(0, 4 * np.pi, n_points)
    
    directions = base_direction + direction_variation * np.sin(time_points)
    
    # 風速の生成（10〜14ノット）
    base_speed = 12
    speed_variation = 2
    speeds = base_speed + speed_variation * np.sin(np.linspace(0, 8 * np.pi, n_points))
    
    # データフレームの作成
    data = {
        'timestamp': timestamps,
        'wind_direction': directions,
        'wind_speed': speeds
    }
    
    return pd.DataFrame(data)

def create_wind_data_from_metadata(wind_metadata, track_data):
    """メタデータから風データを作成"""
    if track_data is None or 'timestamp' not in track_data.columns:
        return generate_dummy_wind_data(None)
    
    timestamps = track_data['timestamp'].tolist()
    
    # 風向と風速の取得
    base_direction = wind_metadata.get('base_direction', 225)
    direction_variation = wind_metadata.get('direction_variation', 20)
    direction_period = wind_metadata.get('direction_period', 4)
    
    base_speed = wind_metadata.get('base_speed', 12)
    speed_variation = wind_metadata.get('speed_variation', 2)
    speed_period = wind_metadata.get('speed_period', 8)
    
    # ポイント数
    n_points = len(timestamps)
    
    # 風向の生成
    time_points_dir = np.linspace(0, direction_period * np.pi, n_points)
    directions = base_direction + direction_variation * np.sin(time_points_dir)
    
    # 風速の生成
    time_points_speed = np.linspace(0, speed_period * np.pi, n_points)
    speeds = base_speed + speed_variation * np.sin(time_points_speed)
    
    # データフレームの作成
    data = {
        'timestamp': timestamps,
        'wind_direction': directions,
        'wind_speed': speeds
    }
    
    return pd.DataFrame(data)

def generate_demo_course_data(track_data):
    """デモ用のコースデータを生成"""
    if track_data is None or track_data.empty:
        return None
    
    # トラックデータから位置の範囲を取得
    min_lat = track_data['latitude'].min()
    max_lat = track_data['latitude'].max()
    min_lon = track_data['longitude'].min()
    max_lon = track_data['longitude'].max()
    
    # 中心位置を計算
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    
    # コースの範囲
    lat_range = max_lat - min_lat
    lon_range = max_lon - min_lon
    
    # マークの配置
    marks = [
        {
            "name": "スタート/フィニッシュ",
            "type": "start",
            "latitude": center_lat - lat_range * 0.4,
            "longitude": center_lon
        },
        {
            "name": "風上マーク",
            "type": "windward",
            "latitude": center_lat + lat_range * 0.4,
            "longitude": center_lon
        },
        {
            "name": "風下左マーク",
            "type": "leeward",
            "latitude": center_lat - lat_range * 0.35,
            "longitude": center_lon - lon_range * 0.15
        },
        {
            "name": "風下右マーク",
            "type": "leeward",
            "latitude": center_lat - lat_range * 0.35,
            "longitude": center_lon + lon_range * 0.15
        }
    ]
    
    # スタートラインの設定
    start_line = {
        "pin": {
            "latitude": center_lat - lat_range * 0.4,
            "longitude": center_lon - lon_range * 0.15
        },
        "committee_boat": {
            "latitude": center_lat - lat_range * 0.4,
            "longitude": center_lon + lon_range * 0.15
        }
    }
    
    # 風況情報
    wind_conditions = {
        "average_direction": 225,
        "direction_range": 40,
        "average_speed": 12,
        "speed_range": 4,
        "shifty": True,
        "gust_factor": 1.2
    }
    
    # コースタイプ
    course_type = "windward_leeward_2"
    
    return {
        "marks": marks,
        "start_line": start_line,
        "wind_conditions": wind_conditions,
        "course_type": course_type,
        "number_of_laps": 2
    }

def handle_callback(changes):
    """コールバック関数"""
    if changes:
        # 変更内容のログなどを行う場合はここに実装
        pass

def main():
    """メイン関数"""
    # アプリケーションの設定
    st.set_page_config(
        page_title="セーリング戦略分析 - レース後分析デモ",
        page_icon="🚢",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # ヘッダー
    st.title("セーリング戦略分析 - レース後分析デモ")
    st.markdown("""
    このデモアプリケーションでは、セーリングレースのGPSトラックデータを分析し、
    戦略評価、重要判断ポイント、改善提案などを提供します。
    右側のタブを使って各分析結果を確認してください。
    """)
    
    # サイドバー
    with st.sidebar:
        st.header("デモ設定")
        
        # データロードオプション
        data_option = st.radio(
            "データソース",
            options=["デモデータ", "アップロードデータ"],
            index=0
        )
        
        # 分析器の設定
        st.subheader("分析器設定")
        
        # セーラープロファイル（簡略版）
        skill_level = st.selectbox(
            "スキルレベル",
            options=["beginner", "intermediate", "advanced", "expert", "professional"],
            format_func=lambda x: {
                "beginner": "初心者", 
                "intermediate": "中級者", 
                "advanced": "上級者",
                "expert": "エキスパート", 
                "professional": "プロフェッショナル"
            }.get(x, x),
            index=2  # 上級者をデフォルトに
        )
        
        experience_years = st.slider("経験年数", 0, 30, 5)
        
        competition_level = st.selectbox(
            "競技レベル",
            options=["recreational", "club", "regional", "national", "international", "olympic"],
            format_func=lambda x: {
                "recreational": "レクリエーション", 
                "club": "クラブ", 
                "regional": "地域",
                "national": "国内", 
                "international": "国際", 
                "olympic": "オリンピック"
            }.get(x, x),
            index=2  # 地域をデフォルトに
        )
        
        # セーラープロファイルの作成
        sailor_profile = {
            "name": "デモセーラー",
            "skill_level": skill_level,
            "experience_years": experience_years,
            "competition_level": competition_level,
            "preferred_boat_class": "470",
            "goals": "レース戦略の理解と技術向上"
        }
        
        # 分析レベル設定
        analysis_level = st.selectbox(
            "分析レベル",
            options=["basic", "intermediate", "advanced", "professional"],
            format_func=lambda x: {
                "basic": "基本", 
                "intermediate": "中級", 
                "advanced": "高度", 
                "professional": "プロフェッショナル"
            }.get(x, x),
            index=2  # 高度をデフォルトに
        )
    
    # アップロードデータかデモデータかに応じてデータをロード
    if data_option == "アップロードデータ":
        data = load_uploaded_data()
    else:
        data = load_demo_data()
    
    # トラックデータがない場合のエラーメッセージ
    if data["track_data"] is None or data["track_data"].empty:
        st.error("有効なトラックデータがありません。デモデータを使用するか、別のデータをアップロードしてください。")
        return
    
    # 分析エンジンの初期化
    post_race_analyzer = PostRaceAnalyzer(sailor_profile, analysis_level=analysis_level)
    
    # メインコンテンツの表示
    if data and data["track_data"] is not None:
        # データのプレビュー（折りたたみ可能）
        with st.expander("データプレビュー", expanded=False):
            st.subheader("GPSトラックデータ")
            st.dataframe(data["track_data"].head())
            
            if data["wind_data"] is not None:
                st.subheader("風データ")
                st.dataframe(data["wind_data"].head())
            
            if data["course_data"] is not None:
                st.subheader("コースデータ")
                st.json(data["course_data"])
        
        # 分析実行ボタン
        if st.button("分析実行"):
            with st.spinner("分析を実行中..."):
                try:
                    # 分析の実行
                    analysis_result = post_race_analyzer.analyze_race(
                        data["track_data"], 
                        data["wind_data"], 
                        data["competitor_data"], 
                        data["course_data"]
                    )
                    
                    # セッションステートに結果を保存
                    st.session_state["analysis_result"] = analysis_result
                    st.success("分析が完了しました！")
                except Exception as e:
                    st.error(f"分析中にエラーが発生しました: {str(e)}")
        
        # レース後分析パネルの表示
        post_race_analysis_panel(
            analyzer=post_race_analyzer,
            data_manager=None,  # デモではデータマネージャは使用しない
            on_change=handle_callback,
            key_prefix="demo"
        )
        
        # 分析情報の詳細説明
        with st.expander("分析機能について", expanded=False):
            st.markdown("""
            ### レース後戦略分析エンジンについて
            
            このデモでは、以下の分析機能を提供しています：
            
            1. **戦略評価**: レース全体の戦略的判断を評価し、強みと弱みを特定します。
            2. **重要判断ポイント**: レース中の戦略的に重要な決断ポイントを検出し、影響度を評価します。
            3. **改善提案**: セーラーのスキルレベルに合わせたパーソナライズされた改善提案を提供します。
            4. **レポート生成**: 分析結果を包括的なレポートとしてエクスポートします。
            
            詳細な分析結果は各タブで確認できます。分析設定タブでは、セーラープロファイル、分析レベル、データ選択などの設定が可能です。
            
            ### 使用方法
            
            1. サイドバーでセーラーのスキルレベルと分析の詳細度を選択
            2. 「分析実行」ボタンをクリックして分析を開始
            3. 各タブでそれぞれの分析結果を確認
            4. 「レポート」タブで結果をレポートとしてエクスポート
            
            このデモは教育および評価目的のみに提供されています。実際のレース分析には、より詳細なデータと適切なコンテキスト情報が必要です。
            """)
    else:
        st.warning("データが正しくロードされていません。")

def load_uploaded_data():
    """ユーザーがアップロードしたファイルからデータをロード"""
    st.subheader("データファイルのアップロード")
    
    # GPSトラックデータのアップロード
    track_file = st.file_uploader("GPSトラックデータ (CSV形式)", type=["csv"])
    wind_file = st.file_uploader("風データ (CSV形式, オプション)", type=["csv"])
    course_file = st.file_uploader("コースデータ (JSON形式, オプション)", type=["json"])
    
    track_data = None
    wind_data = None
    course_data = None
    
    # トラックデータの処理
    if track_file is not None:
        try:
            track_data = pd.read_csv(track_file)
            
            # タイムスタンプ列の確認と変換
            if 'timestamp' in track_data.columns:
                track_data['timestamp'] = pd.to_datetime(track_data['timestamp'])
            
            # 必須カラムのチェック
            required_cols = ['latitude', 'longitude']
            if not all(col in track_data.columns for col in required_cols):
                st.warning(f"トラックデータに必要なカラム {required_cols} が含まれていません。")
            
            st.success("トラックデータを正常にロードしました。")
        except Exception as e:
            st.error(f"トラックデータのロード中にエラーが発生しました: {str(e)}")
            track_data = None
    
    # 風データの処理
    if wind_file is not None:
        try:
            wind_data = pd.read_csv(wind_file)
            
            # タイムスタンプ列の確認と変換
            if 'timestamp' in wind_data.columns:
                wind_data['timestamp'] = pd.to_datetime(wind_data['timestamp'])
            
            # 必須カラムのチェック
            required_cols = ['wind_direction', 'wind_speed']
            if not all(col in wind_data.columns for col in required_cols):
                st.warning(f"風データに必要なカラム {required_cols} が含まれていません。")
                # 風データを補完
                if track_data is not None:
                    wind_data = generate_dummy_wind_data(track_data)
                    st.info("風データを補完しました。")
            else:
                st.success("風データを正常にロードしました。")
        except Exception as e:
            st.error(f"風データのロード中にエラーが発生しました: {str(e)}")
            if track_data is not None:
                wind_data = generate_dummy_wind_data(track_data)
                st.info("風データを補完しました。")
    else:
        # 風データがアップロードされていない場合はダミーデータを生成
        if track_data is not None:
            wind_data = generate_dummy_wind_data(track_data)
            st.info("風データがアップロードされていないため、補完データを生成しました。")
    
    # コースデータの処理
    if course_file is not None:
        try:
            course_data = json.load(course_file)
            
            # コースデータの基本検証
            if 'marks' not in course_data:
                st.warning("コースデータにマーク情報が含まれていません。")
                # コースデータを補完
                if track_data is not None:
                    course_data = generate_demo_course_data(track_data)
                    st.info("コースデータを補完しました。")
            else:
                st.success("コースデータを正常にロードしました。")
        except Exception as e:
            st.error(f"コースデータのロード中にエラーが発生しました: {str(e)}")
            if track_data is not None:
                course_data = generate_demo_course_data(track_data)
                st.info("コースデータを補完しました。")
    else:
        # コースデータがアップロードされていない場合はデモデータを生成
        if track_data is not None:
            course_data = generate_demo_course_data(track_data)
            st.info("コースデータがアップロードされていないため、補完データを生成しました。")
    
    return {
        "track_data": track_data,
        "wind_data": wind_data,
        "course_data": course_data,
        "competitor_data": None  # 競合艇データはアップロード未対応
    }

if __name__ == "__main__":
    main()
