# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.timeline.playback_control

プレイバック制御クラスを提供するモジュールです。
GPSトラックデータなどのタイムベースデータのプレイバック機能を提供します。
"""

from typing import Dict, List, Any, Optional, Union, Callable
import uuid
from datetime import datetime

from sailing_data_processor.reporting.elements.base_element import BaseElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class PlaybackControl:
    """
    プレイバック制御クラス
    
    GPSトラックデータなどのタイムベースデータのプレイバック機能を提供します。
    """
    
    def __init__(self, element_id=None, name="プレイバック", **kwargs):
        """初期化"""
        self.element_id = element_id or f"playback_{uuid.uuid4().hex[:8]}"
        self.name = name
        
        # 再生状態
        self._playing = False
        self._current_time = 0
        self._start_time = 0
        self._end_time = 100  # デフォルト値、データ設定時に更新
        
        # 再生設定
        self._options = {}
            "playback_speed": kwargs.get("playback_speed", 1.0),
            "loop": kwargs.get("loop", False),
            "show_timeline": kwargs.get("show_timeline", True),
            "show_time_display": kwargs.get("show_time_display", True),
            "show_controls": kwargs.get("show_controls", True),
            "control_size": kwargs.get("control_size", "medium"),  # small, medium, large
            "position": kwargs.get("position", "bottom"),  # top, bottom
            "auto_fit_time_range": kwargs.get("auto_fit_time_range", True)
 "playback_speed": kwargs.get("playback_speed", 1.0),
            "loop": kwargs.get("loop", False),
            "show_timeline": kwargs.get("show_timeline", True),
            "show_time_display": kwargs.get("show_time_display", True),
            "show_controls": kwargs.get("show_controls", True),
            "control_size": kwargs.get("control_size", "medium"),  # small, medium, large
            "position": kwargs.get("position", "bottom"),  # top, bottom
            "auto_fit_time_range": kwargs.get("auto_fit_time_range", True)}
        
        # キーフレーム
        self._keyframes = []
        
        # コールバック
        self._on_time_changed = None
        self._on_play_state_changed = None
    
    def set_time_range(self, start_time, end_time):
        """時間範囲を設定"""
        self._start_time = start_time
        self._end_time = end_time
        self._current_time = start_time
    
    def set_current_time(self, time):
        """現在時刻を設定"""
        self._current_time = max(self._start_time, min(time, self._end_time))
        
        # コールバック呼び出し
        if self._on_time_changed:
            self._on_time_changed(self._current_time)
    
    def play(self):
        """再生開始"""
        self._playing = True
        
        if self._on_play_state_changed:
            self._on_play_state_changed(self._playing)
    
    def pause(self):
        """一時停止"""
        self._playing = False
        
        if self._on_play_state_changed:
            self._on_play_state_changed(self._playing)
    
    def stop(self):
        """停止（先頭に戻る）"""
        self._playing = False
        self._current_time = self._start_time
        
        if self._on_play_state_changed:
            self._on_play_state_changed(self._playing)
        
        if self._on_time_changed:
            self._on_time_changed(self._current_time)
    
    def add_keyframe(self, time, label=None, details=None):
        """キーフレームを追加"""
        self._keyframes.append({
            "time": time,
            "label": label or f"Keyframe len(self._keyframes) + 1}",
            "details": details or {}
        })
        
        # 時間順にソート
        self._keyframes.sort(key=lambda kf: kf["time"])
        
        return self._keyframes[-1]
    
    def remove_keyframe(self, keyframe_id):
        """キーフレームを削除"""
        original_length = len(self._keyframes)
        self._keyframes = [kf for kf in self._keyframes if kf.get("id") != keyframe_id]
        return len(self._keyframes) < original_length
    
    def get_keyframes(self):
        """キーフレーム一覧を取得"""
        return self._keyframes
    
    def jump_to_keyframe(self, index_or_id):
        """キーフレームにジャンプ"""
        if isinstance(index_or_id, int) and 0 <= index_or_id < len(self._keyframes):
            self.set_current_time(self._keyframes[index_or_id]["time"])
            return True
        elif isinstance(index_or_id, str):
            for kf in self._keyframes:
                if kf.get("id") == index_or_id:
                    self.set_current_time(kf["time"])
                    return True
        return False
    
    def set_on_time_changed(self, callback):
        """時間変更コールバックを設定"""
        self._on_time_changed = callback
    
    def set_on_play_state_changed(self, callback):
        """再生状態変更コールバックを設定"""
        self._on_play_state_changed = callback
    
    def get_next_frame_time(self, step=1):
        """次のフレーム時間を取得"""
        next_time = self._current_time + step
        if next_time > self._end_time:
            if self._options["loop"]:
                return self._start_time
            else:
                return self._end_time
        return next_time
    
    def get_prev_frame_time(self, step=1):
        """前のフレーム時間を取得"""
        prev_time = self._current_time - step
        if prev_time < self._start_time:
            if self._options["loop"]:
                return self._end_time
            else:
                return self._start_time
        return prev_time
    
    def next_frame(self, step=1):
        """次のフレームに移動"""
        self.set_current_time(self.get_next_frame_time(step))
    
    def prev_frame(self, step=1):
        """前のフレームに移動"""
        self.set_current_time(self.get_prev_frame_time(step))
    
    def is_playing(self):
        """再生中かどうかを取得"""
        return self._playing
    
    def get_current_time(self):
        """現在時刻を取得"""
        return self._current_time
    
    def get_time_range(self):
        """時間範囲を取得"""
        return (self._start_time, self._end_time)
    
    def get_progress(self):
        """再生の進捗率（0〜1）を取得"""
        if self._start_time == self._end_time:
            return 0
        return (self._current_time - self._start_time) / (self._end_time - self._start_time)
    
    def set_option(self, key, value):
        """オプションを設定"""
        if key in self._options:
            self._options[key] = value
    
    def get_option(self, key, default=None):
        """オプションを取得"""
        return self._options.get(key, default)
    
    def get_options(self):
        """すべてのオプションを取得"""
        return self._options.copy()
    
    def to_dict(self):
        """辞書形式にシリアライズ"""
        return {
            "element_id": self.element_id,
            "name": self.name,
            "current_time": self._current_time,
            "start_time": self._start_time,
            "end_time": self._end_time,
            "playing": self._playing,
            "options": self._options,
            "keyframes": self._keyframes
 "element_id": self.element_id,
            "name": self.name,
            "current_time": self._current_time,
            "start_time": self._start_time,
            "end_time": self._end_time,
            "playing": self._playing,
            "options": self._options,
            "keyframes": self._keyframes}
        return {
            "element_id": self.element_id,
            "name": self.name,
            "current_time": self._current_time,
            "start_time": self._start_time,
            "end_time": self._end_time,
            "playing": self._playing,
            "options": self._options,
            "keyframes": self._keyframes}
 {
            "element_id": self.element_id,
            "name": self.name,
            "current_time": self._current_time,
            "start_time": self._start_time,
            "end_time": self._end_time,
            "playing": self._playing,
            "options": self._options,
            "keyframes": self._keyframes}}
    
    @classmethod
    def from_dict(cls, data):
        """辞書形式からインスタンスを作成"""
        instance = cls(
            element_id=data.get("element_id"),
            name=data.get("name"),
            **data.get("options", {})
        )
        
        instance._current_time = data.get("current_time", 0)
        instance._start_time = data.get("start_time", 0)
        instance._end_time = data.get("end_time", 100)
        instance._playing = data.get("playing", False)
        instance._keyframes = data.get("keyframes", [])
        
        return instance
    
    def render(self, context=None):
        """プレイバックコントロールのHTMLを生成"""
        if context is None:
            context = {}
            
        # ここにHTML生成のコードを記述
        # 実際の実装では、JavaScriptと連携してプレイバックコントロールを表示する
        
        html = f"""
        <div id="{self.element_id}_container" class="playback-control-container">
            <div class="playback-controls">
                <!-- 再生コントロール -->
                <button id="{self.element_id}_prev" class="playback-btn" title="前へ">⏮</button>
                <button id="{self.element_id}_play" class="playback-btn" title="再生/一時停止">▶</button>
                <button id="{self.element_id}_stop" class="playback-btn" title="停止">⏹</button>
                <button id="{self.element_id}_next" class="playback-btn" title="次へ">⏭</button>
                
                <!-- シークバー -->
                <div class="playback-seek-container">
                    <input type="range" id="{self.element_id}_seek" 
                           min="{self._start_time}" max="{self._end_time}" 
                           value="{self._current_time}" class="playback-seek" />
                </div>
                
                <!-- 時間表示 -->
                <div id="{self.element_id}_time" class="playback-time">00:00:00</div>
                
                <!-- 再生速度 -->
                <select id="{self.element_id}_speed" class="playback-speed">
                    <option value="0.1" {"selected" if self._options["playback_speed"] == 0.1 else ""}>0.1x</option>
                    <option value="0.25" {"selected" if self._options["playback_speed"] == 0.25 else ""}>0.25x</option>
                    <option value="0.5" {"selected" if self._options["playback_speed"] == 0.5 else ""}>0.5x</option>
                    <option value="1.0" {"selected" if self._options["playback_speed"] == 1.0 else ""}>1.0x</option>
                    <option value="2.0" {"selected" if self._options["playback_speed"] == 2.0 else ""}>2.0x</option>
                    <option value="5.0" {"selected" if self._options["playback_speed"] == 5.0 else ""}>5.0x</option>
                    <option value="10.0" {"selected" if self._options["playback_speed"] == 10.0 else ""}>10.0x</option>
                </select>
                
                <!-- ループ設定 -->
                <label class="playback-loop">
                    <input type="checkbox" id="{self.element_id}_loop" 
                           {"checked" if self._options["loop"] else ""} />
                    <span>🔁</span>
                </label>
            </div>
            
            <!-- キーフレーム (あれば表示) -->
            {self._render_keyframes() if self._keyframes else ""}
        </div>
        
        <script>
            # プレイバックコントロールのJavaScript実装
            (function() {
                # コントロール要素の取得
                const playButton = document.getElementById("self.element_id}_play");
                const stopButton = document.getElementById("{self.element_id}_stop");
                const prevButton = document.getElementById("{self.element_id}_prev");
                const nextButton = document.getElementById("{self.element_id}_next");
                const seekBar = document.getElementById("{self.element_id}_seek");
                const timeDisplay = document.getElementById("{self.element_id}_time");
                const speedSelect = document.getElementById("{self.element_id}_speed");
                const loopCheckbox = document.getElementById("{self.element_id}_loop");
                
                # 状態変数
                let isPlaying = {str(self._playing).lower()};
                let currentTime = {self._current_time};
                let playbackSpeed = {self._options["playback_speed"]};
                let loopEnabled = {str(self._options["loop"]).lower()};
                }
                }
                }
                }
                let lastUpdateTime = 0;
                }
                }
                let animationFrameId = null;
                
                # 時間表示の更新
                function updateTimeDisplay(time) {
                    const hours = Math.floor(time / 3600);
                    const minutes = Math.floor((time % 3600) / 60);
                    const seconds = Math.floor(time % 60);
                    timeDisplay.textContent = 
                        `$hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                
                # 再生状態の更新
                function updatePlayState(playing) {
                    isPlaying = playing;
                    playButton.innerHTML = playing ? "⏸" : "▶";
                    playButton.title = playing ? "一時停止" : "再生";
                    
                    if (playing) {
                        lastUpdateTime = performance.now();
                        if (!animationFrameId) animationFrameId = requestAnimationFrame(updateAnimation);
                    } else if (animationFrameId) {
                        cancelAnimationFrame(animationFrameId);
                        animationFrameId = null;
                    
                    # カスタムイベントを発火
                    const event = new CustomEvent("playbackStateChange", {
                        detail: {
                            elementId: "self.element_id}",
                            playing: playing
                    });
                    document.dispatchEvent(event);
                
                # シーク位置の更新
                function updateSeekPosition(time) {
                    currentTime = time;
                    seekBar.value = time;
                    updateTimeDisplay(time);
                    
                    # カスタムイベントを発火
                    const event = new CustomEvent("playbackTimeChange", {
                        detail: {
                            elementId: "self.element_id}",
                            time: time
                    });
                    document.dispatchEvent(event);
                
                # アニメーションフレーム更新
                function updateAnimation(timestamp) {
                    const elapsed = (timestamp - lastUpdateTime) / 1000;
                    lastUpdateTime = timestamp;
                    
                    if (isPlaying) {
                        const newTime = currentTime + elapsed * playbackSpeed;
                        
                        if (newTime >= self._end_time}) {
                            if (loopEnabled) {
                                updateSeekPosition(self._start_time});
                            } else {
                                updateSeekPosition(self._end_time});
                                updatePlayState(false);
                        } else {
                            updateSeekPosition(newTime);
                        
                        animationFrameId = requestAnimationFrame(updateAnimation);
                
                # イベントリスナーの設定
                playButton.addEventListener("click", function() updatePlayState(!isPlaying);
                });
                
                stopButton.addEventListener("click", function() {
                    updatePlayState(false);
                    updateSeekPosition(self._start_time});
                });
                
                prevButton.addEventListener("click", function() {
                    const frameStep = 1; # 1秒単位での移動
                    const newTime = Math.max(self._start_time}, currentTime - frameStep);
                    updateSeekPosition(newTime);
                });
                
                nextButton.addEventListener("click", function() {
                    const frameStep = 1; # 1秒単位での移動
                    const newTime = Math.min(self._end_time}, currentTime + frameStep);
                    updateSeekPosition(newTime);
                });
                
                seekBar.addEventListener("input", function() {
                    updateSeekPosition(parseFloat(this.value));
                });
                
                speedSelect.addEventListener("change", function() {
                    playbackSpeed = parseFloat(this.value);
                });
                
                loopCheckbox.addEventListener("change", function() {
                    loopEnabled = this.checked;
                });
                
                # キーフレームのクリックイベント
                document.querySelectorAll(".keyframe-marker").forEach(marker => {
                    marker.addEventListener("click", function() const time = parseFloat(this.dataset.time);
                        updateSeekPosition(time);
                    });
                });
                
                # 初期表示
                updateTimeDisplay(currentTime);
                updatePlayState(isPlaying);
                
                # 外部からアクセスできるようにグローバル変数として保存
                window["{self.element_id}_controller"] = {
                    play: () => updatePlayState(true),
                    pause: () => updatePlayState(false),
                    stop: () => {
                        updatePlayState(false);
                        updateSeekPosition(self._start_time});
                    },
                    setTime: (time) => updateSeekPosition(Math.max({self._start_time}, Math.min({self._end_time}, time))),
                    getTime: () => currentTime,
                    isPlaying: () => isPlaying,
                    setSpeed: (speed) => {
                        playbackSpeed = speed;
                        speedSelect.value = speed;
                    },
                    nextFrame: () => {
                        const frameStep = 1;
                        const newTime = Math.min(self._end_time}, currentTime + frameStep);
                        updateSeekPosition(newTime);
                    },
                    prevFrame: () => {
                        const frameStep = 1;
                        const newTime = Math.max(self._start_time}, currentTime - frameStep);
                        updateSeekPosition(newTime);
                };
            })();
        </script>
        """
        
        return html
    
    def _render_keyframes(self):
        """キーフレーム表示のHTMLを生成"""
        if not self._keyframes:
            return ""
        
        # 時間範囲を取得
        time_range = self._end_time - self._start_time
        if time_range <= 0:
            return ""
        
        # キーフレームマーカーのHTML
        markers_html = ""
        for kf in self._keyframes:
            position = ((kf["time"] - self._start_time) / time_range) * 100
            markers_html += f"""
            <div class="keyframe-marker" data-time="{kf['time']}" style="left: {position}%;" 
                 title="{kf['label']}"></div>
            """
        
        # キーフレームセレクターのHTML
        options_html = "<option value=''>キーフレームを選択</option>"
        for i, kf in enumerate(self._keyframes):
            options_html += f"""
            <option value="{i}">{kf['label']}</option>
            """
        
        html = f"""
        <div class="keyframe-container">
            <div class="keyframe-track">
                {markers_html}
            </div>
            <div class="keyframe-selector">
                <select id="{self.element_id}_keyframes" class="keyframe-select">
                    {options_html}
                </select>
                <button id="{self.element_id}_goto_keyframe" class="keyframe-goto-btn">移動</button>
            </div>
        </div>
        
        <script>
            # キーフレーム選択のイベントリスナー
            document.getElementById("{self.element_id}_goto_keyframe").addEventListener("click", function() {
                const select = document.getElementById("self.element_id}_keyframes");
                const index = select.value;
                if (index !== '') {
                    const controller = window["self.element_id}_controller"];
                    const keyframes = {json.dumps(self._keyframes)};
                    }
                    if (controller && keyframes[index]) {
                        controller.setTime(keyframes[index].time);
            });
        </script>
        """
        
        return html
