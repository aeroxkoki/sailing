        ----------
        data : Any
            エクスポートするデータ
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        bytes
            画像データ
        """
        if not MATPLOTLIB_AVAILABLE:
            self.add_error("チャート生成にはmatplotlibライブラリが必要です。pip install matplotlib を実行してください。")
            return None
        
        if not hasattr(data, 'data') or not PANDAS_AVAILABLE:
            self.add_error("チャート生成にはpandasのDataFrameが必要です。")
            return None
        
        df = data.data
        
        # 図のサイズと解像度の設定
        width = self.options.get("width", 1200) / 100
        height = self.options.get("height", 800) / 100
        dpi = self.options.get("dpi", 300)
        
        # 図の作成
        fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)
        
        # チャートタイプの取得
        chart_type = self.options.get("chart_type", "line")
        
        # タイトルの設定
        if self.options.get("include_title", True):
            title = kwargs.get("title", self.options.get("title", ""))
            
            # データのメタデータからタイトルを設定（タイトルが指定されていない場合）
            if not title and hasattr(data, 'metadata') and isinstance(data.metadata, dict):
                if 'name' in data.metadata:
                    title = f"セーリングデータ: {data.metadata['name']}"
                elif 'date' in data.metadata:
                    title = f"セーリングデータ: {data.metadata['date']}"
            
            # デフォルトタイトル
            if not title:
                title = "セーリングデータ分析チャート"
            
            plt.title(title, fontsize=self.options.get("title_font_size", 16))
        
        # グリッドの設定
        if self.options.get("include_grid", True):
            plt.grid(True, alpha=0.3)
        
        # チャートの作成（チャートタイプに応じた処理）
        chart_success = False
        if chart_type == "line":
            # 線グラフ
            chart_success = create_line_chart(df, ax, self, options=self.options, **kwargs)
        elif chart_type == "bar":
            # 棒グラフ
            chart_success = create_bar_chart(df, ax, self, options=self.options, **kwargs)
        elif chart_type == "scatter":
            # 散布図
            chart_success = create_scatter_chart(df, ax, self, options=self.options, **kwargs)
        elif chart_type == "pie":
            # 円グラフ
            chart_success = create_pie_chart(df, ax, self, options=self.options, **kwargs)
        else:
            self.add_error(f"未対応のチャートタイプ: {chart_type}")
            plt.close(fig)
            return None
        
        if not chart_success:
            plt.close(fig)
            return None
        
        # 凡例の設定
        if self.options.get("include_legend", True):
            plt.legend(fontsize=self.options.get("legend_font_size", 10))
        
        # タイムスタンプの追加
        if self.options.get("include_timestamp", True):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plt.figtext(0.01, 0.01, f"生成日時: {timestamp}", fontsize=8, alpha=0.7)
        
        # 背景の設定
        if self.options.get("transparent", False):
            fig.patch.set_alpha(0)
        else:
            fig.patch.set_facecolor(self.options.get("background_color", "white"))
        
        # レイアウトの調整
        plt.tight_layout()
        
        # 画像形式の設定
        output_format = self.options.get("format", "png")
        
        # 画像の保存（バイトストリームに）
        buffer = io.BytesIO()
        
        if output_format.lower() == "svg":
            plt.savefig(buffer, format="svg", transparent=self.options.get("transparent", False))
        else:
            plt.savefig(buffer, format=output_format, 
                      dpi=dpi, 
                      transparent=self.options.get("transparent", False),
                      bbox_inches="tight")
        
        plt.close(fig)
        
        # バッファから画像データを取得
        buffer.seek(0)
        image_data = buffer.getvalue()
        buffer.close()
        
        return image_data
    
    def _generate_map_image(self, data, **kwargs):
        """
        マップ画像を生成
        
        Parameters
        ----------
        data : Any
            エクスポートするデータ
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        bytes
            画像データ
        """
        if not MATPLOTLIB_AVAILABLE:
            self.add_error("マップ生成にはmatplotlibライブラリが必要です。pip install matplotlib を実行してください。")
            return None
        
        if not hasattr(data, 'data') or not PANDAS_AVAILABLE:
            self.add_error("マップ生成にはpandasのDataFrameが必要です。")
            return None
        
        df = data.data
        
        # 緯度・経度の確認
        if 'latitude' not in df.columns or 'longitude' not in df.columns:
            self.add_error("マップ生成には緯度(latitude)と経度(longitude)のデータが必要です。")
            return None
        
        # 図のサイズと解像度の設定
        width = self.options.get("width", 1200) / 100
        height = self.options.get("height", 800) / 100
        dpi = self.options.get("dpi", 300)
        
        # 図の作成
        fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)
        
        # マップタイプの取得
        map_type = self.options.get("map_type", "track")
        
        # タイトルの設定
        if self.options.get("include_title", True):
            title = kwargs.get("title", self.options.get("title", ""))
            
            # データのメタデータからタイトルを設定（タイトルが指定されていない場合）
            if not title and hasattr(data, 'metadata') and isinstance(data.metadata, dict):
                if 'name' in data.metadata:
                    title = f"セーリングトラック: {data.metadata['name']}"
                elif 'date' in data.metadata:
                    title = f"セーリングトラック: {data.metadata['date']}"
            
            # デフォルトタイトル
            if not title:
                title = "セーリングトラックマップ"
            
            plt.title(title, fontsize=self.options.get("title_font_size", 16))
        
        # グリッドの設定
        if self.options.get("include_grid", True):
            plt.grid(True, alpha=0.3)
        
        # マップの作成（マップタイプに応じた処理）
        map_success = False
        if map_type == "track":
            # トラックマップ
            map_success = create_track_map(df, ax, self, options=self.options, **kwargs)
        elif map_type == "heatmap":
            # ヒートマップ
            map_success = create_heatmap(df, ax, self, options=self.options, **kwargs)
        else:
            self.add_error(f"未対応のマップタイプ: {map_type}")
            plt.close(fig)
            return None
        
        if not map_success:
            plt.close(fig)
            return None
        
        # 凡例の設定
        if self.options.get("include_legend", True) and kwargs.get("add_legend", True):
            plt.legend(fontsize=self.options.get("legend_font_size", 10))
        
        # タイムスタンプの追加
        if self.options.get("include_timestamp", True):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plt.figtext(0.01, 0.01, f"生成日時: {timestamp}", fontsize=8, alpha=0.7)
        
        # 背景の設定
        if self.options.get("transparent", False):
            fig.patch.set_alpha(0)
        else:
            fig.patch.set_facecolor(self.options.get("background_color", "white"))
        
        # レイアウトの調整
        plt.tight_layout()
        
        # 画像形式の設定
        output_format = self.options.get("format", "png")
        
        # 画像の保存（バイトストリームに）
        buffer = io.BytesIO()
        
        if output_format.lower() == "svg":
            plt.savefig(buffer, format="svg", transparent=self.options.get("transparent", False))
        else:
            plt.savefig(buffer, format=output_format, 
                      dpi=dpi, 
                      transparent=self.options.get("transparent", False),
                      bbox_inches="tight")
        
        plt.close(fig)
        
        # バッファから画像データを取得
        buffer.seek(0)
        image_data = buffer.getvalue()
        buffer.close()
        
        return image_data
    
    def _generate_combined_image(self, data, **kwargs):
        """
        複合画像を生成（チャートとマップの組み合わせ）
        
        Parameters
        ----------
        data : Any
            エクスポートするデータ
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        bytes
            画像データ
        """
        if not MATPLOTLIB_AVAILABLE:
            self.add_error("複合画像生成にはmatplotlibライブラリが必要です。pip install matplotlib を実行してください。")
            return None
        
        if not hasattr(data, 'data') or not PANDAS_AVAILABLE:
            self.add_error("複合画像生成にはpandasのDataFrameが必要です。")
            return None
        
        df = data.data
        
        # 緯度・経度の確認
        if 'latitude' not in df.columns or 'longitude' not in df.columns:
            self.add_error("マップ部分の生成には緯度(latitude)と経度(longitude)のデータが必要です。")
            return None
        
        # 図のサイズと解像度の設定
        width = self.options.get("width", 1200) / 100
        height = self.options.get("height", 800) / 100
        dpi = self.options.get("dpi", 300)
        
        # サブプロットの構成
        layout = kwargs.get("layout", "2x1")  # デフォルトは2行1列
        
        if layout == "2x1":
            # 2行1列のレイアウト
            fig, axs = plt.subplots(2, 1, figsize=(width, height), dpi=dpi)
            
            # チャート（上段）
            chart_type = kwargs.get("chart_type", self.options.get("chart_type", "line"))
            success1 = False
            if chart_type == "line":
                success1 = create_line_chart(df, axs[0], self, options=self.options, **kwargs)
            elif chart_type == "bar":
                success1 = create_bar_chart(df, axs[0], self, options=self.options, **kwargs)
            else:
                success1 = create_line_chart(df, axs[0], self, options=self.options, **kwargs)  # デフォルトは線グラフ
            
            # マップ（下段）
            map_type = kwargs.get("map_type", self.options.get("map_type", "track"))
            success2 = False
            if map_type == "track":
                success2 = create_track_map(df, axs[1], self, options=self.options, add_legend=False, **kwargs)
            elif map_type == "heatmap":
                success2 = create_heatmap(df, axs[1], self, options=self.options, **kwargs)
            else:
                success2 = create_track_map(df, axs[1], self, options=self.options, add_legend=False, **kwargs)  # デフォルトはトラック
            
            if not (success1 and success2):
                plt.close(fig)
                return None
            
        elif layout == "1x2":
            # 1行2列のレイアウト
            fig, axs = plt.subplots(1, 2, figsize=(width, height), dpi=dpi)
            
            # マップ（左）
            map_type = kwargs.get("map_type", self.options.get("map_type", "track"))
            success1 = False
            if map_type == "track":
                success1 = create_track_map(df, axs[0], self, options=self.options, add_legend=False, **kwargs)
            elif map_type == "heatmap":
                success1 = create_heatmap(df, axs[0], self, options=self.options, **kwargs)
            else:
                success1 = create_track_map(df, axs[0], self, options=self.options, add_legend=False, **kwargs)
            
            # チャート（右）
            chart_type = kwargs.get("chart_type", self.options.get("chart_type", "line"))
            success2 = False
            if chart_type == "line":
                success2 = create_line_chart(df, axs[1], self, options=self.options, **kwargs)
            elif chart_type == "bar":
                success2 = create_bar_chart(df, axs[1], self, options=self.options, **kwargs)
            else:
                success2 = create_line_chart(df, axs[1], self, options=self.options, **kwargs)
            
            if not (success1 and success2):
                plt.close(fig)
                return None
            
        else:
            # 1行1列のレイアウト（グリッド）
            fig = plt.figure(figsize=(width, height), dpi=dpi)
            
            # グリッド定義
            gs = fig.add_gridspec(2, 2)
            
            # マップ（左上）
            ax1 = fig.add_subplot(gs[0, 0])
            success1 = create_track_map(df, ax1, self, options=self.options, add_legend=False, **kwargs)
            
            # 速度チャート（右上）
            ax2 = fig.add_subplot(gs[0, 1])
            success2 = create_line_chart(df, ax2, self, options=self.options, y_columns=["speed"] if "speed" in df.columns else None, **kwargs)
            
            # 風向チャート（左下）
            success3 = True
            if 'wind_direction' in df.columns:
                ax3 = fig.add_subplot(gs[1, 0])
                success3 = create_pie_chart(df, ax3, self, options=self.options, **kwargs)
            
            # 風速チャート（右下）
            success4 = True
            if 'wind_speed' in df.columns:
                ax4 = fig.add_subplot(gs[1, 1])
                success4 = create_line_chart(df, ax4, self, options=self.options, y_columns=["wind_speed"], **kwargs)
                
            if not (success1 and success2 and success3 and success4):
                plt.close(fig)
                return None
        
        # タイトルの設定
        if self.options.get("include_title", True):
            title = kwargs.get("title", self.options.get("title", ""))
            
            # データのメタデータからタイトルを設定（タイトルが指定されていない場合）
            if not title and hasattr(data, 'metadata') and isinstance(data.metadata, dict):
                if 'name' in data.metadata:
                    title = f"セーリングデータ分析: {data.metadata['name']}"
                elif 'date' in data.metadata:
                    title = f"セーリングデータ分析: {data.metadata['date']}"
            
            # デフォルトタイトル
            if not title:
                title = "セーリングデータ総合分析"
            
            fig.suptitle(title, fontsize=self.options.get("title_font_size", 16))
        
        # タイムスタンプの追加
        if self.options.get("include_timestamp", True):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plt.figtext(0.01, 0.01, f"生成日時: {timestamp}", fontsize=8, alpha=0.7)
        
        # 背景の設定
        if self.options.get("transparent", False):
            fig.patch.set_alpha(0)
        else:
            fig.patch.set_facecolor(self.options.get("background_color", "white"))
        
        # レイアウトの調整
        plt.tight_layout()
        if self.options.get("include_title", True):
            plt.subplots_adjust(top=0.9)  # タイトル用のスペース
        
        # 画像形式の設定
        output_format = self.options.get("format", "png")
        
        # 画像の保存（バイトストリームに）
        buffer = io.BytesIO()
        
        if output_format.lower() == "svg":
            plt.savefig(buffer, format="svg", transparent=self.options.get("transparent", False))
        else:
            plt.savefig(buffer, format=output_format, 
                      dpi=dpi, 
                      transparent=self.options.get("transparent", False),
                      bbox_inches="tight")
        
        plt.close(fig)
        
        # バッファから画像データを取得
        buffer.seek(0)
        image_data = buffer.getvalue()
        buffer.close()
        
        return image_data
    
    def validate_options(self):
        """
        オプションの検証
        
        Returns
        -------
        bool
            検証結果
        """
        # フォーマットの検証
        output_format = self.options.get("format", "png")
        if output_format.lower() not in ["png", "jpeg", "jpg", "svg", "pdf"]:
            self.add_warning(f"未対応の画像形式: {output_format}, 'png'を使用します。")
            self.options["format"] = "png"
        
        # コンテンツタイプの検証
        content_type = self.options.get("content_type", "chart")
        if content_type not in ["chart", "map", "combined"]:
            self.add_warning(f"未対応のコンテンツタイプ: {content_type}, 'chart'を使用します。")
            self.options["content_type"] = "chart"
        
        # チャートタイプの検証
        chart_type = self.options.get("chart_type", "line")
        if chart_type not in ["line", "bar", "scatter", "pie"]:
            self.add_warning(f"未対応のチャートタイプ: {chart_type}, 'line'を使用します。")
            self.options["chart_type"] = "line"
        
        # マップタイプの検証
        map_type = self.options.get("map_type", "track")
        if map_type not in ["track", "heatmap"]:
            self.add_warning(f"未対応のマップタイプ: {map_type}, 'track'を使用します。")
            self.options["map_type"] = "track"
        
        # スタイルの検証
        if MATPLOTLIB_AVAILABLE:
            style = self.options.get("style", "default")
            available_styles = plt.style.available
            if style \!= "default" and style not in available_styles:
                self.add_warning(f"未対応のスタイル: {style}, 'default'を使用します。")
                self.options["style"] = "default"
        
        return True
    
    def get_supported_formats(self):
        """
        サポートするフォーマットのリストを取得
        
        Returns
        -------
        List[str]
            サポートするフォーマットのリスト
        """
        return ["image", "png", "jpeg", "svg", "chart", "map"]
