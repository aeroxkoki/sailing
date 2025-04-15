"""
セーリング戦略分析システム - 艇マーカーコンポーネント

進行方向を考慮したセーリングボートのマーカーを提供します。
"""

import folium

def create_boat_icon(course):
    """
    進行方向に合わせた艇のアイコンを作成
    
    Parameters:
    -----------
    course : float
        進行方向（度、0-360）
    
    Returns:
    --------
    folium.DivIcon
        艇を表示するアイコン
    """
    # 方向に合わせて回転したSVGを生成
    boat_svg = f'''
    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
        <g transform="translate(16, 16) rotate({90-course})">
            <path d="M 8,0 L 2,-4 L -8,-4 L -8,4 L 2,4 Z" fill="#FF5722" stroke="#000" />
            <path d="M 0,0 L 8,0 L 0,-12 Z" fill="#FFFFFF" stroke="#000" stroke-width="0.5" />
        </g>
    </svg>
    '''
    
    # folium.DivIconクラスを使用
    return folium.features.DivIcon(
        icon_size=(32, 32),
        icon_anchor=(16, 16),
        html=boat_svg
    )

def add_boat_to_map(m, position, course, tooltip=None):
    """
    マップに艇マーカーを追加
    
    Parameters:
    -----------
    m : folium.Map
        Foliumマップオブジェクト
    position : tuple
        艇の位置 (緯度, 経度)
    course : float
        進行方向（度、0-360）
    tooltip : str, optional
        ツールチップテキスト
    
    Returns:
    --------
    folium.Marker
        追加されたマーカーオブジェクト
    """
    boat_icon = create_boat_icon(course)
    
    marker = folium.Marker(
        location=position,
        icon=boat_icon,
        tooltip=tooltip
    )
    
    marker.add_to(m)
    return marker

def update_boat_position(map_obj, position, course, time_index=None, track_data=None):
    """
    艇の位置を更新し、進行済みトラックを強調表示
    
    Parameters:
    -----------
    map_obj : folium.Map
        Foliumマップオブジェクト
    position : tuple
        新しい艇の位置 (緯度, 経度)
    course : float
        進行方向（度、0-360）
    time_index : int, optional
        現在の時間インデックス
    track_data : list, optional
        トラック全体のデータ
    
    Returns:
    --------
    folium.Map
        更新されたマップオブジェクト
    """
    # 既存のマーカーとトラックを削除
    for key in list(map_obj._children.keys()):
        if key.startswith('boat_marker') or key.startswith('progress_track'):
            del map_obj._children[key]
    
    # 新しい艇マーカーを追加
    tooltip = f"速度: {track_data[time_index]['speed']:.1f} kt<br>コース: {course:.0f}°" if track_data else None
    boat_marker = add_boat_to_map(map_obj, position, course, tooltip)
    boat_marker._name = f"boat_marker_{time_index}"
    
    # トラックデータがあれば進行済みの部分を強調表示
    if track_data and time_index is not None:
        progress_track = track_data[:time_index+1]
        progress_coordinates = [[p['lat'], p['lon']] for p in progress_track]
        
        progress_line = folium.PolyLine(
            progress_coordinates,
            color='#FF5722',
            weight=3,
            opacity=1.0
        )
        progress_line._name = f"progress_track_{time_index}"
        progress_line.add_to(map_obj)
    
    return map_obj
