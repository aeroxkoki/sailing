"""
テスト用サンプルデータ生成スクリプト
"""

import os
import csv
import math
import random
from datetime import datetime, timedelta

def create_sample_csv():
    """テスト用CSVデータを生成"""
    # 出力ファイルパス
    output_dir = os.path.dirname(__file__)
    output_file = os.path.join(output_dir, "sample.csv")
    
    # パラメータ
    start_time = datetime.now() - timedelta(hours=2)  # 2時間前から開始
    duration_minutes = 60  # 1時間のデータ
    interval_seconds = 5  # 5秒間隔
    start_lat = 35.0  # 東京湾エリア
    start_lon = 139.7
    
    # 風向風速パラメータ
    wind_direction = 270  # 西風
    wind_speed = 10  # 10ノット
    
    # 書き込み開始
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # ヘッダー
        writer.writerow(["timestamp", "latitude", "longitude", "speed", "course"])
        
        # データポイント生成
        num_points = int(duration_minutes * 60 / interval_seconds)
        
        for i in range(num_points):
            # 時間計算
            point_time = start_time + timedelta(seconds=i * interval_seconds)
            timestamp = point_time.isoformat()
            
            # 緯度経度の計算（円運動に近い動き + ノイズ）
            angle = i * 6 / num_points  # 円運動の角度
            radius = 0.01  # 約1kmの半径
            
            lat = start_lat + radius * math.sin(angle) + random.uniform(-0.0001, 0.0001)
            lon = start_lon + radius * math.cos(angle) + random.uniform(-0.0001, 0.0001)
            
            # 速度と方位
            # 風に対する相対角度で速度が変わる（風上は遅く、風下は速い）
            boat_direction = (angle * 180 / math.pi + 90) % 360
            relative_wind_angle = abs((boat_direction - wind_direction + 180) % 360 - 180)
            
            # 風上: 相対角度0度、風下: 相対角度180度
            # 風上で4ノット、風下で6ノット、風横で5ノットを目安に
            if relative_wind_angle < 60:  # 風上
                speed = 4.0 + random.uniform(-0.5, 0.5)
            elif relative_wind_angle > 120:  # 風下
                speed = 6.0 + random.uniform(-0.5, 0.5)
            else:  # 風横
                speed = 5.0 + random.uniform(-0.5, 0.5)
            
            # タックを入れる（約10分ごとに方向転換）
            if i > 0 and i % (10 * 60 / interval_seconds) < 5:
                # タック中は速度低下
                speed = speed * 0.7
                # 方向は急激に変化
                boat_direction = (boat_direction + 100) % 360
            
            # データポイントを追加
            writer.writerow([timestamp, lat, lon, speed, boat_direction])
    
    print(f"サンプルCSVファイルを作成しました: {output_file}")

def create_sample_gpx():
    """テスト用GPXデータを生成"""
    # 出力ファイルパス
    output_dir = os.path.dirname(__file__)
    output_file = os.path.join(output_dir, "sample.gpx")
    
    # パラメータ
    start_time = datetime.now() - timedelta(hours=2)  # 2時間前から開始
    duration_minutes = 60  # 1時間のデータ
    interval_seconds = 5  # 5秒間隔
    start_lat = 35.0  # 東京湾エリア
    start_lon = 139.7
    
    # GPXヘッダーとトラックセクション
    gpx_header = f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Sailing Strategy Analyzer Test Data"
 xmlns="http://www.topografix.com/GPX/1/1"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
<trk>
<name>Sample Sailing Track</name>
<trkseg>
"""
    
    gpx_footer = """</trkseg>
</trk>
</gpx>"""
    
    # データポイント生成
    num_points = int(duration_minutes * 60 / interval_seconds)
    track_points = []
    
    for i in range(num_points):
        # 時間計算
        point_time = start_time + timedelta(seconds=i * interval_seconds)
        timestamp = point_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # 緯度経度の計算（円運動に近い動き + ノイズ）
        angle = i * 6 / num_points  # 円運動の角度
        radius = 0.01  # 約1kmの半径
        
        lat = start_lat + radius * math.sin(angle) + random.uniform(-0.0001, 0.0001)
        lon = start_lon + radius * math.cos(angle) + random.uniform(-0.0001, 0.0001)
        
        # GPXポイント
        track_point = f"""<trkpt lat="{lat}" lon="{lon}">
  <time>{timestamp}</time>
  <extensions>
    <speed>{4.0 + random.uniform(-0.5, 1.5)}</speed>
    <course>{(angle * 180 / math.pi + 90) % 360}</course>
  </extensions>
</trkpt>
"""
        track_points.append(track_point)
    
    # GPXファイル作成
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(gpx_header)
        for point in track_points:
            f.write(point)
        f.write(gpx_footer)
    
    print(f"サンプルGPXファイルを作成しました: {output_file}")

def main():
    """メイン実行関数"""
    create_sample_csv()
    create_sample_gpx()

if __name__ == "__main__":
    main()