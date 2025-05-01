/**
 * Wind Field Script for Sailing Strategy Analyzer
 * 
 * このスクリプトは風向風速場の表示を行うJavaScriptです。
 * 風向風速データの視覚化、風の場の分析、風向シフトなどの表示機能を提供します。
 */

// ページ読み込み時に初期化
window.addEventListener('load', function() {
    // マップの初期化
    const map = L.map(mapId);
    
    // ベースマップのタイル選択
    let tileLayer;
    
    switch (mapConfig.map_type) {
        case 'satellite':
            tileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
            });
            break;
        case 'nautical':
            tileLayer = L.tileLayer('https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png', {
                attribution: 'Map data: &copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors'
            });
            break;
        default:  // 'osm'
            tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            });
    }
    
    // ベースマップをマップに追加
    tileLayer.addTo(map);
    
    // 座標データの情報を取得
    const trackPoints = [];
    let uGrid = null;
    let vGrid = null;
    let gridBounds = null;
    const timeValues = [];
    const windShifts = [];
    const windTrends = [];
    const terrainEffects = [];
    
    let latKey = 'lat';
    let lngKey = 'lng';
    const timeKey = mapConfig.time_key || 'timestamp';
    
    // 風データを処理する関数
    function processWindData(source) {
        const result = {
            uGrid: null,
            vGrid: null,
            gridBounds: null,
            times: []
        };
        
        if (!source) return result;
        
        // U成分とV成分のキー名を決定
        let uComponentKey = 'u-wind';
        let vComponentKey = 'v-wind';
        
        if ('u_component' in source) {
            uComponentKey = 'u_component';
            vComponentKey = 'v_component';
        }
        
        // 速度のスケーリング
        const scale = mapConfig.wind_speed_scale || 0.01;
        
        // グリッドの設定
        let latMin, latMax, lonMin, lonMax;
        let nx, ny;
        
        if ('lat_min' in source && 'lat_max' in source && 'lon_min' in source && 'lon_max' in source) {
            latMin = source.lat_min;
            latMax = source.lat_max;
            lonMin = source.lon_min;
            lonMax = source.lon_max;
        } else {
            // デフォルト値（マップの中心から±0.1度）
            latMin = mapConfig.center[0] - 0.1;
            latMax = mapConfig.center[0] + 0.1;
            lonMin = mapConfig.center[1] - 0.1;
            lonMax = mapConfig.center[1] + 0.1;
        }
        
        if ('nx' in source && 'ny' in source) {
            nx = source.nx;
            ny = source.ny;
        } else if (uComponentKey in source && Array.isArray(source[uComponentKey])) {
            nx = source[uComponentKey].length;
            ny = source[uComponentKey][0] ? source[uComponentKey][0].length : 0;
        } else {
            nx = 10;
            ny = 10;
        }
        
        // グリッド境界を設定
        result.gridBounds = [[latMin, lonMin], [latMax, lonMax]];
        
        // 風速データがある場合に処理
        if (uComponentKey in source && vComponentKey in source) {
            // 速度のスケーリングと変換
            result.uGrid = [];
            result.vGrid = [];
            
            for (let i = 0; i < source[uComponentKey].length; i++) {
                const uRow = [];
                const vRow = [];
                
                for (let j = 0; j < source[uComponentKey][i].length; j++) {
                    uRow.push(source[uComponentKey][i][j] * scale);
                    vRow.push(source[vComponentKey][i][j] * scale);
                }
                
                result.uGrid.push(uRow);
                result.vGrid.push(vRow);
            }
            
            // 時間情報がある場合に処理
            if ('times' in source && Array.isArray(source.times)) {
                result.times = source.times;
            }
        }
        
        return result;
    }
    
    // 風向シフトを抽出する関数
    function extractWindShifts(source) {
        const shifts = [];
        
        if (!source || !('wind_shifts' in source) || !Array.isArray(source.wind_shifts)) {
            return shifts;
        }
        
        source.wind_shifts.forEach(function(shift) {
            if (shift.lat && shift.lng) {
                shifts.push({
                    position: [shift.lat, shift.lng],
                    time: shift.time || null,
                    before_direction: shift.before_direction || 0,
                    after_direction: shift.after_direction || 0,
                    magnitude: shift.magnitude || 0,
                    type: shift.type || 'shift'
                });
            }
        });
        
        return shifts;
    }
    
    // 風のトレンドを抽出する関数
    function extractWindTrends(source) {
        const trends = [];
        
        if (!source || !('wind_trends' in source)) {
            return trends;
        }
        
        if ('wind_trends' in source && Array.isArray(source.wind_trends)) {
            source.wind_trends.forEach(function(trend) {
                if (trend.points && Array.isArray(trend.points)) {
                    const points = [];
                    
                    trend.points.forEach(function(point) {
                        if (point.lat && point.lng) {
                            points.push([point.lat, point.lng]);
                        }
                    });
                    
                    if (points.length > 1) {
                        trends.push({
                            points: points,
                            type: trend.type || 'trend',
                            value: trend.value || 0
                        });
                    }
                }
            });
        }
        
        return trends;
    }
    
    // 地形効果を抽出する関数
    function extractTerrainEffects(source) {
        const effects = [];
        
        if (!source || !('effects' in source) || !Array.isArray(source.effects)) {
            return effects;
        }
        
        source.effects.forEach(function(effect) {
            if (effect.polygon && Array.isArray(effect.polygon)) {
                const points = [];
                
                effect.polygon.forEach(function(point) {
                    if (point.lat && point.lng) {
                        points.push([point.lat, point.lng]);
                    }
                });
                
                if (points.length > 2) {
                    effects.push({
                        polygon: points,
                        type: effect.type || 'acceleration',
                        intensity: effect.intensity || 1
                    });
                }
            }
        });
        
        return effects;
    }
    
    // 軌跡データの処理
    if (Array.isArray(windData)) {
        // 配列形式のデータ処理
        if (windData.length > 0 && typeof windData[0] === 'object') {
            // キー名の確認
            if ('latitude' in windData[0] && 'longitude' in windData[0]) {
                latKey = 'latitude';
                lngKey = 'longitude';
            } else if ('lat' in windData[0] && 'lon' in windData[0]) {
                lngKey = 'lon';
            }
            
            // 軌跡ポイント追加
            for (let i = 0; i < windData.length; i++) {
                const point = windData[i];
                if (typeof point === 'object' && point[latKey] && point[lngKey]) {
                    trackPoints.push([point[latKey], point[lngKey]]);
                    
                    // 時間次元のデータ追加
                    if (mapConfig.show_time_dimension && timeKey in point) {
                        const time = point[timeKey];
                        if (typeof time === 'string') {
                            timeValues.push(new Date(time));
                        } else if (typeof time === 'number') {
                            // Unix時間の場合はミリ秒に変換
                            timeValues.push(new Date(time * 1000));
                        }
                    }
                }
            }
        }
    } else if (typeof windData === 'object') {
        // オブジェクト形式のデータ処理
        if ('track' in windData && Array.isArray(windData.track)) {
            for (let i = 0; i < windData.track.length; i++) {
                const point = windData.track[i];
                if (typeof point === 'object' && point[latKey] && point[lngKey]) {
                    trackPoints.push([point[latKey], point[lngKey]]);
                    
                    // 時間次元のデータ追加
                    if (mapConfig.show_time_dimension && timeKey in point) {
                        const time = point[timeKey];
                        if (typeof time === 'string') {
                            timeValues.push(new Date(time));
                        } else if (typeof time === 'number') {
                            // Unix時間の場合はミリ秒に変換
                            timeValues.push(new Date(time * 1000));
                        }
                    }
                }
            }
        }
        
        // 風データの処理
        const windGridData = processWindData(windData);
        uGrid = windGridData.uGrid;
        vGrid = windGridData.vGrid;
        gridBounds = windGridData.gridBounds;
        
        // 風向シフトの処理
        if (mapConfig.show_wind_shifts) {
            windShifts.push(...extractWindShifts(windData));
        }
        
        // 風のトレンドの処理
        if (mapConfig.show_wind_trends) {
            windTrends.push(...extractWindTrends(windData));
        }
    }
    
    // 地形効果の処理
    if (mapConfig.show_terrain_effects && terrainData) {
        terrainEffects.push(...extractTerrainEffects(terrainData));
    }
    
    // マップレイヤーの初期化
    const baseLayer = L.layerGroup().addTo(map);
    const trackLayer = L.layerGroup();
    const windLayer = L.layerGroup();
    const forecastLayer = L.layerGroup();
    const shiftsLayer = L.layerGroup();
    const trendsLayer = L.layerGroup();
    const terrainLayer = L.layerGroup();
    
    // オーバーレイのリスト作成
    const overlays = {};
    
    // 軌跡レイヤー（GPS航跡がある場合）
    if (mapConfig.show_track && trackPoints.length > 0) {
        const trackLine = L.polyline(trackPoints, {
            color: mapConfig.track_color,
            weight: mapConfig.track_width,
            opacity: 0.8,
            lineJoin: 'round'
        }).addTo(trackLayer);
        
        overlays["GPS航跡"] = trackLayer;
        trackLayer.addTo(map);
    }
    
    // 風速場描画
    if (uGrid && vGrid && gridBounds) {
        // D3.jsを使用した風ベクトル描画
        function drawWindVectors(uGrid, vGrid, bounds, targetLayer, options) {
            const defaultOptions = {
                density: mapConfig.vector_density || 50,
                scale: mapConfig.arrow_scale || 1.0,
                color: 'rgba(0, 0, 128, 0.7)',
                width: 1.5
            };
            
            // オプションのマージ
            const opts = Object.assign({}, defaultOptions, options || {});
            
            // 境界の取得
            const latMin = bounds[0][0];
            const lonMin = bounds[0][1];
            const latMax = bounds[1][0];
            const lonMax = bounds[1][1];
            
            // グリッドの次元
            const nx = uGrid.length;
            const ny = uGrid[0].length;
            
            // 密度に応じたステップ
            const xStep = Math.max(1, Math.floor(nx / Math.sqrt(opts.density)));
            const yStep = Math.max(1, Math.floor(ny / Math.sqrt(opts.density)));
            
            // グリッドの間隔
            const latStep = (latMax - latMin) / (nx - 1);
            const lonStep = (lonMax - lonMin) / (ny - 1);
            
            // 風ベクトルの描画
            for (let i = 0; i < nx; i += xStep) {
                for (let j = 0; j < ny; j += yStep) {
                    const lat = latMin + i * latStep;
                    const lon = lonMin + j * lonStep;
                    const u = uGrid[i][j];
                    const v = vGrid[i][j];
                    
                    // 風速が小さすぎる場合はスキップ
                    if (Math.abs(u) < 1e-6 && Math.abs(v) < 1e-6) continue;
                    
                    // 風向と風速の計算
                    const speed = Math.sqrt(u * u + v * v);
                    let direction = Math.atan2(v, u) * 180 / Math.PI;
                    
                    // 風向を気象学的な方向に変換
                    direction = 90 - direction;
                    if (direction < 0) direction += 360;
                    
                    // 風速に応じたアローサイズ
                    const arrowSize = 20 * opts.scale * Math.min(1, speed / (mapConfig.max_velocity * 0.1 || 1));
                    
                    // 矢印アイコンの作成
                    const arrowIcon = L.divIcon({
                        html: '<svg width="' + (arrowSize * 2) + '" height="' + (arrowSize * 2) + '" ' +
                             'viewBox="-10 -10 20 20" class="wind-arrow">' +
                             '<path d="M0,-8 L0,8 M0,-8 L-4,-4 M0,-8 L4,-4" ' +
                             'stroke="' + opts.color + '" stroke-width="' + opts.width + '" />' +
                             '</svg>',
                        className: 'wind-vector-icon',
                        iconSize: [arrowSize * 2, arrowSize * 2],
                        iconAnchor: [arrowSize, arrowSize]
                    });
                    
                    const marker = L.marker([lat, lon], {
                        icon: arrowIcon,
                        rotationAngle: direction,
                        rotationOrigin: 'center center'
                    }).addTo(targetLayer);
                    
                    // ポップアップ情報
                    marker.bindPopup(
                        '<div><strong>風向:</strong> ' + Math.round(direction) + '°</div>' +
                        '<div><strong>風速:</strong> ' + speed.toFixed(1) + ' ' + mapConfig.velocity_units + '</div>'
                    );
                }
            }
        }
        
        // 実測風の描画
        drawWindVectors(uGrid, vGrid, gridBounds, windLayer, {
            color: 'rgba(0, 0, 128, 0.8)'
        });
        
        overlays["風"] = windLayer;
        windLayer.addTo(map);
        
        // 予測風の処理（設定がある場合）
        if (mapConfig.compare_forecast && forecastData) {
            const forecastGridData = processWindData(forecastData);
            
            if (forecastGridData.uGrid && forecastGridData.vGrid && forecastGridData.gridBounds) {
                drawWindVectors(forecastGridData.uGrid, forecastGridData.vGrid, forecastGridData.gridBounds, forecastLayer, {
                    color: 'rgba(0, 128, 0, 0.8)'
                });
                
                overlays["予測風"] = forecastLayer;
                forecastLayer.addTo(map);
            }
        }
        
        // 風向シフトの表示
        if (mapConfig.show_wind_shifts && windShifts.length > 0) {
            windShifts.forEach(function(shift) {
                // シフトマーカーの作成
                const shiftMarker = L.circleMarker(shift.position, {
                    radius: 8,
                    color: 'purple',
                    weight: 2,
                    fillColor: 'white',
                    fillOpacity: 0.7,
                    className: 'wind-shift-marker'
                }).addTo(shiftsLayer);
                
                // ポップアップ情報
                let popupContent = '<div><strong>風向シフト</strong></div>';
                if (shift.time) popupContent += '<div><strong>時刻:</strong> ' + new Date(shift.time).toLocaleString() + '</div>';
                popupContent += '<div><strong>変化前:</strong> ' + Math.round(shift.before_direction) + '°</div>';
                popupContent += '<div><strong>変化後:</strong> ' + Math.round(shift.after_direction) + '°</div>';
                popupContent += '<div><strong>変化量:</strong> ' + Math.round(shift.magnitude) + '°</div>';
                
                shiftMarker.bindPopup(popupContent);
            });
            
            overlays["風向シフト"] = shiftsLayer;
            shiftsLayer.addTo(map);
        }
        
        // 風のトレンドの表示
        if (mapConfig.show_wind_trends && windTrends.length > 0) {
            windTrends.forEach(function(trend) {
                // トレンドラインの作成
                const trendLine = L.polyline(trend.points, {
                    color: 'rgba(255, 165, 0, 0.8)',
                    weight: 2,
                    dashArray: '4',
                    className: 'wind-trend-line'
                }).addTo(trendsLayer);
                
                // ポップアップ情報
                const trendType = trend.type === 'increasing' ? '風速増加' : 
                               trend.type === 'decreasing' ? '風速減少' : 
                               trend.type === 'shift_left' ? '左への風向変化' : 
                               trend.type === 'shift_right' ? '右への風向変化' : '風のトレンド';
                
                let popupContent = '<div><strong>' + trendType + '</strong></div>';
                popupContent += '<div><strong>変化量:</strong> ' + trend.value + '</div>';
                
                trendLine.bindPopup(popupContent);
            });
            
            overlays["風のトレンド"] = trendsLayer;
            trendsLayer.addTo(map);
        }
        
        // 地形効果の表示
        if (mapConfig.show_terrain_effects && terrainEffects.length > 0) {
            terrainEffects.forEach(function(effect) {
                // 地形効果ポリゴンの作成
                const effectPolygon = L.polygon(effect.polygon, {
                    color: 'rgba(255, 0, 0, 0.5)',
                    weight: 1,
                    fillColor: 'rgba(255, 0, 0, 0.2)',
                    fillOpacity: 0.2 * effect.intensity,
                    className: 'terrain-effect-area'
                }).addTo(terrainLayer);
                
                // ポップアップ情報
                const effectType = effect.type === 'acceleration' ? '風速加速' : 
                                effect.type === 'deceleration' ? '風速減速' : 
                                effect.type === 'turbulence' ? '乱流' : '地形効果';
                
                let popupContent = '<div><strong>' + effectType + '</strong></div>';
                popupContent += '<div><strong>強度:</strong> ' + effect.intensity.toFixed(1) + '</div>';
                
                effectPolygon.bindPopup(popupContent);
            });
            
            overlays["地形効果"] = terrainLayer;
            terrainLayer.addTo(map);
        }
        
        // レイヤーコントロールを追加
        L.control.layers(null, overlays).addTo(map);
        
        // 凡例の作成
        const legend = L.control({position: 'bottomright'});
        
        legend.onAdd = function(map) {
            const div = L.DomUtil.create('div', 'wind-field-legend');
            
            const minVel = mapConfig.min_velocity;
            const maxVel = mapConfig.max_velocity;
            const unit = mapConfig.velocity_units;
            
            div.innerHTML = '<div class="legend-title">風速 (' + unit + ')</div>' +
                           '<div class="legend-scale">' +
                           '<div class="legend-scale-segment" style="background: rgb(0, 0, 255);"></div>' +
                           '<div class="legend-scale-segment" style="background: rgb(0, 255, 255);"></div>' +
                           '<div class="legend-scale-segment" style="background: rgb(0, 255, 0);"></div>' +
                           '<div class="legend-scale-segment" style="background: rgb(255, 255, 0);"></div>' +
                           '<div class="legend-scale-segment" style="background: rgb(255, 0, 0);"></div>' +
                           '</div>' +
                           '<div class="legend-labels">' +
                           '<div>' + minVel + '</div>' +
                           '<div>' + Math.round((minVel + maxVel) / 2) + '</div>' +
                           '<div>' + maxVel + '</div>' +
                           '</div>';
            
            return div;
        };
        
        legend.addTo(map);
        
        // 表示範囲の決定
        let bounds;
        if (trackPoints.length > 0) {
            bounds = L.latLngBounds(trackPoints);
        } else {
            bounds = L.latLngBounds([
                [gridBounds[0][0], gridBounds[0][1]],
                [gridBounds[1][0], gridBounds[1][1]]
            ]);
        }
        
        // 時間次元の設定（設定がある場合）
        if (mapConfig.show_time_dimension && timeValues.length > 0) {
            // 時間次元の設定
            const timeDimension = new L.TimeDimension({
                times: timeValues,
                currentTime: timeValues[0].getTime()
            });
            
            map.timeDimension = timeDimension;
            
            // 時間次元コントロールの追加
            const tdControl = new L.Control.TimeDimension({
                player: {
                    buffer: 1,
                    minBufferReady: 1,
                    loop: mapConfig.animation_loop,
                    transitionTime: mapConfig.animation_duration
                }
            });
            
            map.addControl(tdControl);
        }
        
        // 自動的に表示範囲を調整
        if (mapConfig.center_auto && bounds) {
            map.fitBounds(bounds);
        } else {
            map.setView(mapConfig.center, mapConfig.zoom_level);
        }
    } else {
        // 風データが見つからない場合
        const message = document.createElement('div');
        message.className = 'report-map-message';
        message.innerHTML = '<p>風向風速データの形式が不正または見つかりません</p>';
        
        const mapContainer = document.getElementById(mapId);
        mapContainer.appendChild(message);
        
        // デフォルト表示設定
        map.setView(mapConfig.center, mapConfig.zoom_level);
    }
    
    // グローバル変数にマップを保存
    window[mapId + '_map'] = map;
});
