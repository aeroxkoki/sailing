/**
 * Course Elements Script for Sailing Strategy Analyzer
 * 
 * このスクリプトはセーリングコースの要素（マーク、スタートライン、レイライン等）を
 * 地図上に表示する機能を提供します。
 */

(function() {
    // マップの初期化
    var map = L.map(mapId, {
        zoomControl: true,
        attributionControl: true
    });
    
    // ベースマップのタイル選択
    var tileLayer;
    
    switch (mapConfig.map_type) {
        case 'satellite':
            tileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
            });
            break;
        case 'terrain':
            tileLayer = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
                attribution: 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)'
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
    var trackPoints = [];
    var latKey = 'lat';
    var lngKey = 'lng';
    
    // データ形式をチェック
    if (Array.isArray(courseData)) {
        // 配列形式の場合、座標データの取得
        if (courseData.length > 0 && typeof courseData[0] === 'object') {
            // キー名の確認
            if ('latitude' in courseData[0] && 'longitude' in courseData[0]) {
                latKey = 'latitude';
                lngKey = 'longitude';
            } else if ('lat' in courseData[0] && 'lon' in courseData[0]) {
                lngKey = 'lon';
            }
            
            // 座標ポイントを追加
            for (var i = 0; i < courseData.length; i++) {
                var point = courseData[i];
                if (typeof point === 'object' && point[latKey] && point[lngKey]) {
                    trackPoints.push([point[latKey], point[lngKey]]);
                }
            }
        }
    } else if (typeof courseData === 'object') {
        // オブジェクト形式の場合
        if ('track' in courseData && Array.isArray(courseData.track)) {
            for (var i = 0; i < courseData.track.length; i++) {
                var point = courseData.track[i];
                if (typeof point === 'object' && point[latKey] && point[lngKey]) {
                    trackPoints.push([point[latKey], point[lngKey]]);
                }
            }
        } else if ('points' in courseData && Array.isArray(courseData.points)) {
            for (var i = 0; i < courseData.points.length; i++) {
                var point = courseData.points[i];
                if (typeof point === 'object' && point[latKey] && point[lngKey]) {
                    trackPoints.push([point[latKey], point[lngKey]]);
                }
            }
        }
    }
    
    // レイヤーグループの作成
    var trackLayer = L.layerGroup();
    var markLayer = L.layerGroup();
    var lineLayer = L.layerGroup();
    var laylinesLayer = L.layerGroup();
    var strategyLayer = L.layerGroup();
    var routeLayer = L.layerGroup();
    var riskLayer = L.layerGroup();
    
    // オーバーレイのリスト作成
    var overlays = {};
    
    // トラック表示（GPS航跡の場合）
    if (mapConfig.show_track && trackPoints.length > 0) {
        var trackLine = L.polyline(trackPoints, {
            color: mapConfig.track_color,
            weight: mapConfig.track_width,
            opacity: 0.8,
            lineJoin: 'round'
        }).addTo(trackLayer);
        
        overlays["GPS航跡"] = trackLayer;
        trackLayer.addTo(map);
    }
    
    // マークの表示
    if (courseConfig.marks && courseConfig.marks.length > 0) {
        courseConfig.marks.forEach(function(mark) {
            // アイコン設定を取得
            var iconConfig = mapConfig.point_icons[mark.type] || mapConfig.point_icons.mark || mapConfig.point_icons.default;
            var iconColor = mark.color || iconConfig.color || 'red';
            var iconName = mark.icon || iconConfig.icon || 'map-marker-alt';
            
            // アイコンを作成
            var markIcon = L.divIcon({
                html: '<div class="course-mark-icon" style="background-color: ' + iconColor + ';"><i class="fas fa-' + iconName + '"></i></div>',
                className: 'course-mark-icon-wrapper',
                iconSize: [32, 32],
                iconAnchor: [16, 16]
            });
            
            // マーカーの作成
            var marker = L.marker([mark.lat, mark.lng], {
                icon: markIcon,
                title: mark.name || 'Mark'
            }).addTo(markLayer);
            
            // ポップアップの内容
            var popupContent = '<div class="course-popup">';
            popupContent += '<h4>' + (mark.name || 'Mark') + '</h4>';
            if (mark.description) popupContent += '<p>' + mark.description + '</p>';
            popupContent += '<p><strong>タイプ:</strong> ' + mark.type + '</p>';
            if (mark.rounding_direction) popupContent += '<p><strong>回航方向:</strong> ' + mark.rounding_direction + '</p>';
            popupContent += '</div>';
            
            marker.bindPopup(popupContent);
        });
        
        overlays["コースマーク"] = markLayer;
        markLayer.addTo(map);
    }
    
    // スタートラインの表示
    if (courseConfig.start_line && courseConfig.start_line.pin && courseConfig.start_line.boat) {
        var pinPos = [courseConfig.start_line.pin.lat, courseConfig.start_line.pin.lng];
        var boatPos = [courseConfig.start_line.boat.lat, courseConfig.start_line.boat.lng];
        
        // ラインを作成
        var startLine = L.polyline([pinPos, boatPos], {
            color: 'green',
            weight: 3,
            opacity: 0.8,
            className: 'start-line'
        }).addTo(lineLayer);
        
        // ピン側のマーカー
        var pinIcon = L.divIcon({
            html: '<div class="course-mark-icon" style="background-color: green;"><i class="fas fa-flag"></i></div>',
            className: 'course-mark-icon-wrapper',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });
        
        var pinMarker = L.marker(pinPos, {
            icon: pinIcon,
            title: 'Start Line (Pin End)'
        }).addTo(lineLayer);
        
        // コミッティボート側のマーカー
        var boatIcon = L.divIcon({
            html: '<div class="course-mark-icon" style="background-color: green;"><i class="fas fa-ship"></i></div>',
            className: 'course-mark-icon-wrapper',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });
        
        var boatMarker = L.marker(boatPos, {
            icon: boatIcon,
            title: 'Start Line (Boat End)'
        }).addTo(lineLayer);
        
        // ポップアップ
        var lineLength = L.GeometryUtil.length(startLine);
        
        startLine.bindPopup('<div class="course-popup"><h4>スタートライン</h4>' +
                          '<p><strong>長さ:</strong> ' + lineLength.toFixed(1) + ' m</p>' +
                          '</div>');
    }
    
    // フィニッシュラインの表示
    if (courseConfig.finish_line && courseConfig.finish_line.pin && courseConfig.finish_line.boat) {
        var pinPos = [courseConfig.finish_line.pin.lat, courseConfig.finish_line.pin.lng];
        var boatPos = [courseConfig.finish_line.boat.lat, courseConfig.finish_line.boat.lng];
        
        // フィニッシュライン
        var finishLine = L.polyline([pinPos, boatPos], {
            color: 'blue',
            weight: 3,
            opacity: 0.8,
            className: 'finish-line'
        }).addTo(lineLayer);
        
        // ピン側のマーカー
        var pinIcon = L.divIcon({
            html: '<div class="course-mark-icon" style="background-color: blue;"><i class="fas fa-flag"></i></div>',
            className: 'course-mark-icon-wrapper',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });
        
        var pinMarker = L.marker(pinPos, {
            icon: pinIcon,
            title: 'Finish Line (Pin End)'
        }).addTo(lineLayer);
        
        // コミッティボート側のマーカー
        var boatIcon = L.divIcon({
            html: '<div class="course-mark-icon" style="background-color: blue;"><i class="fas fa-ship"></i></div>',
            className: 'course-mark-icon-wrapper',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });
        
        var boatMarker = L.marker(boatPos, {
            icon: boatIcon,
            title: 'Finish Line (Boat End)'
        }).addTo(lineLayer);
        
        // ポップアップ
        var lineLength = L.GeometryUtil.length(finishLine);
        
        finishLine.bindPopup('<div class="course-popup"><h4>フィニッシュライン</h4>' +
                           '<p><strong>長さ:</strong> ' + lineLength.toFixed(1) + ' m</p>' +
                           '</div>');
        
        overlays["スタート/フィニッシュ"] = lineLayer;
        lineLayer.addTo(map);
    }
    
    // レイラインの表示
    if (courseConfig.show_laylines) {
        var windwardMark = null;
        var leewardMark = null;
        
        // 風上・風下マークを特定
        if (courseConfig.marks && courseConfig.marks.length > 0) {
            courseConfig.marks.forEach(function(mark) {
                if (mark.type === 'windward') {
                    windwardMark = mark;
                } else if (mark.type === 'leeward') {
                    leewardMark = mark;
                }
            });
        }
        
        // レイラインスタイル
        var laylineStyle = {
            color: courseConfig.layline_style.color || 'rgba(255, 0, 0, 0.6)',
            weight: courseConfig.layline_style.weight || 2,
            dashArray: courseConfig.layline_style.dashArray || '5,5',
            opacity: 0.8
        };
        
        // タッキングアングルの半分
        var halfAngle = courseConfig.tacking_angle / 2;
        
        // 風上マークのレイライン
        if (windwardMark) {
            var windwardPos = [windwardMark.lat, windwardMark.lng];
            
            // ラインの長さ（約1km）
            var laylineLength = 0.01;  // 約1kmの経度差
            
            // 左側のレイライン
            var leftAngle = 360 - halfAngle;
            var leftEndLat = windwardMark.lat + Math.sin(leftAngle * Math.PI / 180) * laylineLength;
            var leftEndLng = windwardMark.lng + Math.cos(leftAngle * Math.PI / 180) * laylineLength;
            
            var leftLayline = L.polyline([windwardPos, [leftEndLat, leftEndLng]], laylineStyle).addTo(laylinesLayer);
            
            // 右側のレイライン
            var rightAngle = 180 - halfAngle;
            var rightEndLat = windwardMark.lat + Math.sin(rightAngle * Math.PI / 180) * laylineLength;
            var rightEndLng = windwardMark.lng + Math.cos(rightAngle * Math.PI / 180) * laylineLength;
            
            var rightLayline = L.polyline([windwardPos, [rightEndLat, rightEndLng]], laylineStyle).addTo(laylinesLayer);
            
            // ポップアップ
            leftLayline.bindPopup('<div class="course-popup"><h4>レイライン</h4>' +
                               '<p><strong>角度:</strong> ' + leftAngle + '°</p></div>');
            
            rightLayline.bindPopup('<div class="course-popup"><h4>レイライン</h4>' +
                                '<p><strong>角度:</strong> ' + rightAngle + '°</p></div>');
        }
        
        // 風下マークのレイライン
        if (leewardMark) {
            var leewardPos = [leewardMark.lat, leewardMark.lng];
            
            // ラインの長さ（約1km）
            var laylineLength = 0.01;  // 約1kmの経度差
            
            // 左側のレイライン
            var leftAngle = halfAngle;
            var leftEndLat = leewardMark.lat + Math.sin(leftAngle * Math.PI / 180) * laylineLength;
            var leftEndLng = leewardMark.lng + Math.cos(leftAngle * Math.PI / 180) * laylineLength;
            
            var leftLayline = L.polyline([leewardPos, [leftEndLat, leftEndLng]], laylineStyle).addTo(laylinesLayer);
            
            // 右側のレイライン
            var rightAngle = 360 - halfAngle;
            var rightEndLat = leewardMark.lat + Math.sin(rightAngle * Math.PI / 180) * laylineLength;
            var rightEndLng = leewardMark.lng + Math.cos(rightAngle * Math.PI / 180) * laylineLength;
            
            var rightLayline = L.polyline([leewardPos, [rightEndLat, rightEndLng]], laylineStyle).addTo(laylinesLayer);
            
            // ポップアップ
            leftLayline.bindPopup('<div class="course-popup"><h4>レイライン</h4>' +
                               '<p><strong>角度:</strong> ' + leftAngle + '°</p></div>');
            
            rightLayline.bindPopup('<div class="course-popup"><h4>レイライン</h4>' +
                                '<p><strong>角度:</strong> ' + rightAngle + '°</p></div>');
        }
        
        overlays["レイライン"] = laylinesLayer;
        laylinesLayer.addTo(map);
    }
    
    // 戦略ポイントの表示
    if (courseConfig.strategy_points && courseConfig.strategy_points.length > 0) {
        courseConfig.strategy_points.forEach(function(point) {
            // ポイントタイプの設定
            var iconConfig = mapConfig.point_icons[point.type] || mapConfig.point_icons.default;
            var iconColor = point.color || iconConfig.color || 'blue';
            var iconName = point.icon || iconConfig.icon || 'info-circle';
            
            // ポイントアイコンの作成
            var pointIcon = L.divIcon({
                html: '<div class="course-mark-icon" style="background-color: ' + iconColor + ';"><i class="fas fa-' + iconName + '"></i></div>',
                className: 'course-mark-icon-wrapper',
                iconSize: [32, 32],
                iconAnchor: [16, 16]
            });
            
            // マーカーの作成
            var marker = L.marker([point.lat, point.lng], {
                icon: pointIcon,
                title: point.name || point.description || 'Strategy Point'
            }).addTo(strategyLayer);
            
            // ポップアップの内容
            var pointType = point.type === 'advantage' ? '有利ポイント' : 
                          point.type === 'caution' ? '注意ポイント' : 
                          point.type === 'information' ? '情報ポイント' : 
                          '戦略ポイント';
            
            var popupContent = '<div class="course-popup">';
            if (point.name) popupContent += '<h4>' + point.name + '</h4>';
            popupContent += '<p><strong>タイプ:</strong> ' + pointType + '</p>';
            if (point.description) popupContent += '<p>' + point.description + '</p>';
            popupContent += '</div>';
            
            marker.bindPopup(popupContent);
        });
        
        overlays["戦略ポイント"] = strategyLayer;
        strategyLayer.addTo(map);
    }
    
    // 最適ルートの表示
    if (courseConfig.optimal_route && courseConfig.optimal_route.points && courseConfig.optimal_route.points.length > 0) {
        var routePoints = [];
        
        courseConfig.optimal_route.points.forEach(function(point) {
            routePoints.push([point.lat, point.lng]);
        });
        
        // ルートライン
        var routeLine = L.polyline(routePoints, {
            color: 'rgba(0, 128, 0, 0.8)',
            weight: 3,
            opacity: 0.8,
            lineJoin: 'round',
            className: 'optimal-route'
        }).addTo(routeLayer);
        
        // ルートの説明
        var description = courseConfig.optimal_route.description || '最適ルート';
        var reason = courseConfig.optimal_route.reason || '';
        
        // ポップアップの内容
        var popupContent = '<div class="course-popup">';
        popupContent += '<h4>' + description + '</h4>';
        if (reason) popupContent += '<p>' + reason + '</p>';
        popupContent += '</div>';
        
        routeLine.bindPopup(popupContent);
        
        overlays["最適ルート"] = routeLayer;
        routeLayer.addTo(map);
    }
    
    // リスクエリアの表示
    if (courseConfig.risk_areas && courseConfig.risk_areas.length > 0) {
        courseConfig.risk_areas.forEach(function(area) {
            // ポリゴンの座標点
            var polygonPoints = [];
            
            area.polygon.forEach(function(point) {
                polygonPoints.push([point.lat, point.lng]);
            });
            
            // リスクタイプに応じたスタイル
            var areaStyle = {
                color: 'rgba(255, 165, 0, 0.8)',
                weight: 1,
                fillColor: 'rgba(255, 165, 0, 0.3)',
                fillOpacity: 0.3,
                className: 'risk-area risk-area-caution'
            };
            
            if (area.type === 'danger') {
                areaStyle.color = 'rgba(255, 0, 0, 0.8)';
                areaStyle.fillColor = 'rgba(255, 0, 0, 0.3)';
                areaStyle.className = 'risk-area risk-area-danger';
            } else if (area.type === 'information') {
                areaStyle.color = 'rgba(0, 0, 255, 0.6)';
                areaStyle.fillColor = 'rgba(0, 0, 255, 0.2)';
                areaStyle.className = 'risk-area risk-area-information';
            }
            
            // ポリゴンの作成
            var polygon = L.polygon(polygonPoints, areaStyle).addTo(riskLayer);
            
            // エリアの説明
            var areaType = area.type === 'danger' ? '危険エリア' : 
                         area.type === 'caution' ? '注意エリア' : 
                         area.type === 'information' ? '情報エリア' : 
                         'エリア';
            
            var description = area.description || '';
            
            // ポップアップの内容
            var popupContent = '<div class="course-popup">';
            popupContent += '<h4>' + areaType + '</h4>';
            if (description) popupContent += '<p>' + description + '</p>';
            popupContent += '</div>';
            
            polygon.bindPopup(popupContent);
        });
        
        overlays["リスクエリア"] = riskLayer;
        riskLayer.addTo(map);
    }
    
    // レイヤーコントロールを追加
    L.control.layers(null, overlays).addTo(map);
    
    // 表示範囲の決定
    var bounds;
    
    // マークがある場合はマークから範囲を決定
    if (courseConfig.marks && courseConfig.marks.length > 0) {
        var points = [];
        
        courseConfig.marks.forEach(function(mark) {
            points.push([mark.lat, mark.lng]);
        });
        
        // スタート/フィニッシュラインの座標も追加
        if (courseConfig.start_line && courseConfig.start_line.pin && courseConfig.start_line.boat) {
            points.push([courseConfig.start_line.pin.lat, courseConfig.start_line.pin.lng]);
            points.push([courseConfig.start_line.boat.lat, courseConfig.start_line.boat.lng]);
        }
        
        if (courseConfig.finish_line && courseConfig.finish_line.pin && courseConfig.finish_line.boat) {
            points.push([courseConfig.finish_line.pin.lat, courseConfig.finish_line.pin.lng]);
            points.push([courseConfig.finish_line.boat.lat, courseConfig.finish_line.boat.lng]);
        }
        
        bounds = L.latLngBounds(points);
    }
    // マークがなく、トラックデータがある場合はトラックから範囲を決定
    else if (trackPoints.length > 0) {
        bounds = L.latLngBounds(trackPoints);
    }
    
    // 自動的に表示範囲を調整
    if (mapConfig.center_auto && bounds) {
        map.fitBounds(bounds, {
            padding: [50, 50]  // 余白
        });
    } else {
        map.setView(mapConfig.center, mapConfig.zoom_level);
    }
    
    // グローバル変数にマップを保存
    window[mapId + '_map'] = map;
})();
