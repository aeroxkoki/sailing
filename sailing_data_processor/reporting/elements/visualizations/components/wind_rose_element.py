, 0.1)"
            }
        }
        
        # 時間フィルタリングの表示
        time_filter_enabled = self.get_property("time_filter_enabled", False)
        time_start = self.get_property("time_start", None)
        time_end = self.get_property("time_end", None)
        
        if time_filter_enabled and (time_start or time_end):
            # フィルター情報をタイトルに追加
            title_text = options.get("plugins", {}).get("title", {}).get("text", self.title)
            
            # タイトルが存在しなければ作成、存在すれば更新
            if "plugins" not in options:
                options["plugins"] = {}
            if "title" not in options["plugins"]:
                options["plugins"]["title"] = {
                    "display": True,
                    "text": title_text,
                    "font": {
                        "size": 16
                    }
                }
                    
            # サブタイトルの追加
            filter_text = "期間フィルター適用:"
            if time_start:
                from_str = time_start.split("T")[0] if "T" in time_start else time_start
                filter_text += f" 開始: {from_str}"
            if time_end:
                to_str = time_end.split("T")[0] if "T" in time_end else time_end
                filter_text += f" 終了: {to_str}"
            
            options["plugins"]["title"]["subtitle"] = {
                "display": True,
                "text": filter_text,
                "font": {
                    "size": 12,
                    "style": "italic"
                },
                "color": "rgba(100, 100, 100, 0.8)"
            }
        
        # オプションを結合
        self._merge_options(options, wind_rose_options)
        
        return options
    
    def get_chart_initialization_code(self, config_var: str = "config") -> str:
        """
        風配図初期化用のJavaScriptコードを取得
        
        Parameters
        ----------
        config_var : str, optional
            設定変数名, by default "config"
            
        Returns
        -------
        str
            初期化コード
        """
        return f"""
            // チャートJSのPolarAreaチャートを拡張して風配図を作成
            var ctx = document.getElementById('{self.chart_id}').getContext('2d');
            new Chart(ctx, {config_var});
        """
    
    def _get_colors_for_values(self, values: List[float], color_scale: List[str]) -> List[str]:
        """
        値のリストに対応する色を取得
        
        Parameters
        ----------
        values : List[float]
            値のリスト
        color_scale : List[str]
            カラースケール
            
        Returns
        -------
        List[str]
            値に対応する色のリスト
        """
        if not values or max(values) == 0:
            return [color_scale[0]] * len(values)
        
        max_value = max(values)
        colors = []
        
        for value in values:
            # 値に応じてカラースケールから色を選択
            if max_value == 0:
                index = 0
            else:
                # 値を0-1の範囲に正規化してカラースケールのインデックスを計算
                normalized = value / max_value
                index = min(int(normalized * len(color_scale)), len(color_scale) - 1)
            
            colors.append(color_scale[index])
        
        return colors
    
    def _merge_options(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        オプション辞書を再帰的にマージ
        
        Parameters
        ----------
        target : Dict[str, Any]
            ターゲット辞書
        source : Dict[str, Any]
            ソース辞書
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_options(target[key], value)
            else:
                target[key] = value