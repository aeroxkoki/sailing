                                
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
                            }}
                            
                            // 風下マークのレイライン
                            if (leewardMark) {{
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
                            }}
                            
                            overlays["レイライン"] = laylinesLayer;
                            laylinesLayer.addTo(map);
                        }}
                        
                        // 戦略ポイントの表示
                        if (courseConfig.strategy_points && courseConfig.strategy_points.length > 0) {{
                            courseConfig.strategy_points.forEach(function(point) {{
                                // ポイントタイプの設定
                                var iconConfig = mapConfig.point_icons[point.type] || mapConfig.point_icons.default;
                                var iconColor = point.color || iconConfig.color || 'blue';
                                var iconName = point.icon || iconConfig.icon || 'info-circle';
                                
                                // ポイントアイコンの作成
                                var pointIcon = L.divIcon({{
                                    html: '<div class="course-mark-icon" style="background-color: ' + iconColor + ';"><i class="fas fa-' + iconName + '"></i></div>',
                                    className: 'course-mark-icon-wrapper',
                                    iconSize: [32, 32],
                                    iconAnchor: [16, 16]
                                }});
                                
                                // マーカーの作成
                                var marker = L.marker([point.lat, point.lng], {{
                                    icon: pointIcon,
                                    title: point.name || point.description || 'Strategy Point'
                                }}).addTo(strategyLayer);
                                
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
                            }});
                            
                            overlays["戦略ポイント"] = strategyLayer;
                            strategyLayer.addTo(map);
                        }}
                        
                        // 最適ルートの表示
                        if (courseConfig.optimal_route && courseConfig.optimal_route.points && courseConfig.optimal_route.points.length > 0) {{
                            var routePoints = [];
                            
                            courseConfig.optimal_route.points.forEach(function(point) {{
                                routePoints.push([point.lat, point.lng]);
                            }});
                            
                            // ルートライン
                            var routeLine = L.polyline(routePoints, {{
                                color: 'rgba(0, 128, 0, 0.8)',
                                weight: 3,
                                opacity: 0.8,
                                lineJoin: 'round',
                                className: 'optimal-route'
                            }}).addTo(routeLayer);
                            
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
                        }}
                        
                        // リスクエリアの表示
                        if (courseConfig.risk_areas && courseConfig.risk_areas.length > 0) {{
                            courseConfig.risk_areas.forEach(function(area) {{
                                // ポリゴンの座標点
                                var polygonPoints = [];
                                
                                area.polygon.forEach(function(point) {{
                                    polygonPoints.push([point.lat, point.lng]);
                                }});
                                
                                // リスクタイプに応じたスタイル
                                var areaStyle = {{
                                    color: 'rgba(255, 165, 0, 0.8)',
                                    weight: 1,
                                    fillColor: 'rgba(255, 165, 0, 0.3)',
                                    fillOpacity: 0.3,
                                    className: 'risk-area risk-area-caution'
                                }};
                                
                                if (area.type === 'danger') {{
                                    areaStyle.color = 'rgba(255, 0, 0, 0.8)';
                                    areaStyle.fillColor = 'rgba(255, 0, 0, 0.3)';
                                    areaStyle.className = 'risk-area risk-area-danger';
                                }} else if (area.type === 'information') {{
                                    areaStyle.color = 'rgba(0, 0, 255, 0.6)';
                                    areaStyle.fillColor = 'rgba(0, 0, 255, 0.2)';
                                    areaStyle.className = 'risk-area risk-area-information';
                                }}
                                
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
                            }});
                            
                            overlays["リスクエリア"] = riskLayer;
                            riskLayer.addTo(map);
                        }}
                        
                        // レイヤーコントロールを追加
                        L.control.layers(null, overlays).addTo(map);
                        
                        // 表示範囲の決定
                        var bounds;
                        
                        // マークがある場合はマークから範囲を決定
                        if (courseConfig.marks && courseConfig.marks.length > 0) {{
                            var points = [];
                            
                            courseConfig.marks.forEach(function(mark) {{
                                points.push([mark.lat, mark.lng]);
                            }});
                            
                            // スタート/フィニッシュラインの座標も追加
                            if (courseConfig.start_line && courseConfig.start_line.pin && courseConfig.start_line.boat) {{
                                points.push([courseConfig.start_line.pin.lat, courseConfig.start_line.pin.lng]);
                                points.push([courseConfig.start_line.boat.lat, courseConfig.start_line.boat.lng]);
                            }}
                            
                            if (courseConfig.finish_line && courseConfig.finish_line.pin && courseConfig.finish_line.boat) {{
                                points.push([courseConfig.finish_line.pin.lat, courseConfig.finish_line.pin.lng]);
                                points.push([courseConfig.finish_line.boat.lat, courseConfig.finish_line.boat.lng]);
                            }}
                            
                            bounds = L.latLngBounds(points);
                        }}
                        // マークがなく、トラックデータがある場合はトラックから範囲を決定
                        else if (trackPoints.length > 0) {{
                            bounds = L.latLngBounds(trackPoints);
                        }}
                        
                        // 自動的に表示範囲を調整
                        if (mapConfig.center_auto && bounds) {{
                            map.fitBounds(bounds, {{
                                padding: [50, 50]  // 余白
                            }});
                        }} else {{
                            map.setView(mapConfig.center, mapConfig.zoom_level);
                        }}
                        
                        // グローバル変数にマップを保存
                        window['{self.map_id}_map'] = map;
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content
