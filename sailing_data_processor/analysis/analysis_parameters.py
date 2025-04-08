"""
分析パラメータ管理システムモジュール

このモジュールは分析パラメータの一元管理機能を提供します。
パラメータのプリセット定義、保存と読み込み、バリデーションなどの
機能を含みます。
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime

# パラメータキーの名前空間を定義
class ParameterNamespace:
    WIND_ESTIMATION = "wind_estimation"
    STRATEGY_DETECTION = "strategy_detection"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    DATA_PROCESSING = "data_processing"
    VISUALIZATION = "visualization"
    GENERAL = "general"

@dataclass
class ParameterDefinition:
    """パラメータの定義"""
    key: str
    name: str
    description: str
    default_value: Any
    value_type: str  # "int", "float", "bool", "str", "list", "dict" など
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    unit: Optional[str] = None
    namespace: str = ParameterNamespace.GENERAL
    category: str = "基本"
    tags: List[str] = field(default_factory=list)
    ui_order: int = 999
    ui_advanced: bool = False
    ui_hidden: bool = False
    
    def validate_value(self, value: Any) -> bool:
        """
        値が定義の制約を満たすか検証
        
        Parameters:
        -----------
        value : Any
            検証する値
            
        Returns:
        --------
        bool
            値が有効な場合True
        """
        # 型チェック
        type_valid = False
        
        if self.value_type == "int":
            type_valid = isinstance(value, int)
        elif self.value_type == "float":
            type_valid = isinstance(value, (int, float))
        elif self.value_type == "bool":
            type_valid = isinstance(value, bool)
        elif self.value_type == "str":
            type_valid = isinstance(value, str)
        elif self.value_type == "list":
            type_valid = isinstance(value, list)
        elif self.value_type == "dict":
            type_valid = isinstance(value, dict)
        else:
            # 未知の型は常に有効と見なす
            return True
        
        if not type_valid:
            return False
        
        # 数値の範囲チェック
        if self.value_type in ["int", "float"]:
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
        
        # 許容値リストのチェック
        if self.allowed_values is not None:
            return value in self.allowed_values
        
        return True

class ParameterPreset:
    """
    パラメータのプリセット
    
    あらかじめ定義されたパラメータの組み合わせを管理します。
    """
    
    def __init__(self, 
                preset_id: str, 
                name: str, 
                description: str, 
                parameters: Dict[str, Any],
                namespace: str = ParameterNamespace.GENERAL,
                tags: List[str] = None):
        """
        初期化
        
        Parameters:
        -----------
        preset_id : str
            プリセットID
        name : str
            プリセット名
        description : str
            プリセットの説明
        parameters : Dict[str, Any]
            パラメータの値辞書 (キー:値)
        namespace : str, optional
            プリセットの名前空間
        tags : List[str], optional
            分類タグ
        """
        self.preset_id = preset_id
        self.name = name
        self.description = description
        self.parameters = parameters
        self.namespace = namespace
        self.tags = tags or []
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        
    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        パラメータを更新
        
        Parameters:
        -----------
        parameters : Dict[str, Any]
            新しいパラメータの値辞書
        """
        self.parameters.update(parameters)
        self.updated_at = datetime.now().isoformat()
        
    def to_dict(self) -> Dict[str, Any]:
        """
        プリセットを辞書形式に変換
        
        Returns:
        --------
        Dict[str, Any]
            プリセットの辞書表現
        """
        return {
            "preset_id": self.preset_id,
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "namespace": self.namespace,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParameterPreset':
        """
        辞書からプリセットを作成
        
        Parameters:
        -----------
        data : Dict[str, Any]
            プリセットの辞書表現
            
        Returns:
        --------
        ParameterPreset
            作成されたプリセットオブジェクト
        """
        preset = cls(
            preset_id=data.get("preset_id", "unknown"),
            name=data.get("name", "未命名プリセット"),
            description=data.get("description", ""),
            parameters=data.get("parameters", {}),
            namespace=data.get("namespace", ParameterNamespace.GENERAL),
            tags=data.get("tags", [])
        )
        
        # タイムスタンプの復元
        preset.created_at = data.get("created_at", preset.created_at)
        preset.updated_at = data.get("updated_at", preset.updated_at)
        
        return preset

class ParametersManager:
    """
    パラメータ管理クラス
    
    分析パラメータの定義、値管理、プリセット管理などの機能を提供します。
    """
    
    def __init__(self, storage_interface=None):
        """
        初期化
        
        Parameters:
        -----------
        storage_interface : StorageInterface, optional
            データ永続化に使用するストレージインターフェース
        """
        self.logger = logging.getLogger(__name__)
        self.parameter_definitions: Dict[str, ParameterDefinition] = {}
        self.current_values: Dict[str, Any] = {}
        self.presets: Dict[str, ParameterPreset] = {}
        self.storage = storage_interface
        self.storage_key_prefix = "parameter_manager_"
        
        # 変更コールバック
        self.on_parameters_changed_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        # デフォルトのパラメータを初期化
        self._initialize_default_parameters()
    
    def _initialize_default_parameters(self) -> None:
        """デフォルトのパラメータ定義を初期化"""
        # 風推定パラメータ
        wind_params = [
            ParameterDefinition(
                key="min_speed_threshold",
                name="最小速度閾値",
                description="風向風速推定における最小速度閾値（ノット）- これ未満の速度は信頼性が低い",
                default_value=2.0,
                value_type="float",
                min_value=0.1,
                max_value=10.0,
                unit="ノット",
                namespace=ParameterNamespace.WIND_ESTIMATION,
                category="基本",
                ui_order=1
            ),
            ParameterDefinition(
                key="upwind_threshold",
                name="風上判定の最大角度",
                description="風向との差がこの値未満なら風上と判定（度）",
                default_value=45.0,
                value_type="float",
                min_value=30.0,
                max_value=60.0,
                unit="度",
                namespace=ParameterNamespace.WIND_ESTIMATION,
                category="判定閾値",
                ui_order=2
            ),
            ParameterDefinition(
                key="downwind_threshold",
                name="風下判定の最小角度",
                description="風向との差がこの値より大きければ風下と判定（度）",
                default_value=120.0,
                value_type="float",
                min_value=90.0,
                max_value=150.0,
                unit="度",
                namespace=ParameterNamespace.WIND_ESTIMATION,
                category="判定閾値",
                ui_order=3
            ),
            ParameterDefinition(
                key="min_tack_angle_change",
                name="タック/ジャイブ検出の最小方位変化",
                description="マニューバー検出のための最小方位変化（度）",
                default_value=60.0,
                value_type="float",
                min_value=30.0,
                max_value=120.0,
                unit="度",
                namespace=ParameterNamespace.WIND_ESTIMATION,
                category="マニューバー検出",
                ui_order=4
            ),
            ParameterDefinition(
                key="wind_smoothing_window",
                name="風向推定の平滑化ウィンドウサイズ",
                description="風向推定時の移動平均ウィンドウサイズ",
                default_value=5,
                value_type="int",
                min_value=1,
                max_value=20,
                namespace=ParameterNamespace.WIND_ESTIMATION,
                category="高度",
                ui_order=10,
                ui_advanced=True
            )
        ]
        
        # 戦略検出パラメータ
        strategy_params = [
            ParameterDefinition(
                key="min_wind_shift_angle",
                name="最小風向シフト角度",
                description="検出する最小の風向変化（度）",
                default_value=5.0,
                value_type="float",
                min_value=1.0,
                max_value=30.0,
                unit="度",
                namespace=ParameterNamespace.STRATEGY_DETECTION,
                category="風向シフト",
                ui_order=1
            ),
            ParameterDefinition(
                key="wind_forecast_interval",
                name="風予測間隔",
                description="風の場予測の時間間隔（秒）",
                default_value=300,
                value_type="int",
                min_value=60,
                max_value=1800,
                unit="秒",
                namespace=ParameterNamespace.STRATEGY_DETECTION,
                category="風予測",
                ui_order=2
            ),
            ParameterDefinition(
                key="tack_search_radius",
                name="タック探索半径",
                description="タック判断ポイント探索の半径（メートル）",
                default_value=500,
                value_type="int",
                min_value=100,
                max_value=2000,
                unit="メートル",
                namespace=ParameterNamespace.STRATEGY_DETECTION,
                category="タック判断",
                ui_order=3
            ),
            ParameterDefinition(
                key="min_vmg_improvement",
                name="最小VMG改善閾値",
                description="タック判断の最小VMG改善比率",
                default_value=0.05,
                value_type="float",
                min_value=0.01,
                max_value=0.2,
                namespace=ParameterNamespace.STRATEGY_DETECTION,
                category="タック判断",
                ui_order=4
            ),
            ParameterDefinition(
                key="layline_safety_margin",
                name="レイライン安全マージン",
                description="レイライン判断の安全マージン（度）",
                default_value=10.0,
                value_type="float",
                min_value=0.0,
                max_value=30.0,
                unit="度",
                namespace=ParameterNamespace.STRATEGY_DETECTION,
                category="レイライン",
                ui_order=5
            )
        ]
        
        # パフォーマンス分析パラメータ
        performance_params = [
            ParameterDefinition(
                key="performance_window_size",
                name="パフォーマンス分析ウィンドウサイズ",
                description="パフォーマンス計算の移動ウィンドウサイズ",
                default_value=10,
                value_type="int",
                min_value=1,
                max_value=50,
                namespace=ParameterNamespace.PERFORMANCE_ANALYSIS,
                category="基本",
                ui_order=1
            ),
            ParameterDefinition(
                key="vmg_reference_enabled",
                name="VMG参照値の有効化",
                description="VMG計算でポーラー曲線参照値と比較するか",
                default_value=True,
                value_type="bool",
                namespace=ParameterNamespace.PERFORMANCE_ANALYSIS,
                category="VMG分析",
                ui_order=2
            ),
            ParameterDefinition(
                key="maneuver_analysis_enabled",
                name="マニューバー分析の有効化",
                description="タック・ジャイブの詳細分析を行うか",
                default_value=True,
                value_type="bool",
                namespace=ParameterNamespace.PERFORMANCE_ANALYSIS,
                category="マニューバー",
                ui_order=3
            )
        ]
        
        # データ処理パラメータ
        data_processing_params = [
            ParameterDefinition(
                key="smoothing_window_size",
                name="平滑化ウィンドウサイズ",
                description="データの平滑化に使用するウィンドウサイズ",
                default_value=3,
                value_type="int",
                min_value=1,
                max_value=20,
                namespace=ParameterNamespace.DATA_PROCESSING,
                category="前処理",
                ui_order=1
            ),
            ParameterDefinition(
                key="outlier_threshold",
                name="外れ値閾値",
                description="外れ値とみなす標準偏差の倍数",
                default_value=3.0,
                value_type="float",
                min_value=1.0,
                max_value=10.0,
                namespace=ParameterNamespace.DATA_PROCESSING,
                category="前処理",
                ui_order=2
            ),
            ParameterDefinition(
                key="min_data_points",
                name="最小データポイント数",
                description="分析に必要な最小データポイント数",
                default_value=10,
                value_type="int",
                min_value=5,
                max_value=100,
                namespace=ParameterNamespace.DATA_PROCESSING,
                category="検証",
                ui_order=3
            )
        ]
        
        # 可視化パラメータ
        visualization_params = [
            ParameterDefinition(
                key="map_tile_provider",
                name="地図タイルプロバイダ",
                description="地図表示に使用するタイルプロバイダ",
                default_value="OpenStreetMap",
                value_type="str",
                allowed_values=["OpenStreetMap", "CartoDB", "Stamen"],
                namespace=ParameterNamespace.VISUALIZATION,
                category="地図",
                ui_order=1
            ),
            ParameterDefinition(
                key="track_line_width",
                name="トラック線の太さ",
                description="航跡線の太さ",
                default_value=2,
                value_type="int",
                min_value=1,
                max_value=10,
                namespace=ParameterNamespace.VISUALIZATION,
                category="スタイル",
                ui_order=2
            ),
            ParameterDefinition(
                key="track_line_color",
                name="トラック線の色",
                description="航跡線の色",
                default_value="#0066CC",
                value_type="str",
                namespace=ParameterNamespace.VISUALIZATION,
                category="スタイル",
                ui_order=3
            ),
            ParameterDefinition(
                key="show_wind_arrows",
                name="風向矢印の表示",
                description="地図上に風向矢印を表示するか",
                default_value=True,
                value_type="bool",
                namespace=ParameterNamespace.VISUALIZATION,
                category="風表示",
                ui_order=4
            )
        ]
        
        # 一般パラメータ
        general_params = [
            ParameterDefinition(
                key="data_sync_interval",
                name="データ同期間隔",
                description="データの自動保存間隔（秒）",
                default_value=60,
                value_type="int",
                min_value=10,
                max_value=3600,
                unit="秒",
                namespace=ParameterNamespace.GENERAL,
                category="システム",
                ui_order=1
            ),
            ParameterDefinition(
                key="debug_mode",
                name="デバッグモード",
                description="詳細なログ出力を有効化",
                default_value=False,
                value_type="bool",
                namespace=ParameterNamespace.GENERAL,
                category="システム",
                ui_order=2
            )
        ]
        
        # すべてのパラメータをマージして定義に追加
        all_params = wind_params + strategy_params + performance_params + data_processing_params + visualization_params + general_params
        for param in all_params:
            self.add_parameter_definition(param)
            
        # デフォルト値を現在の値として設定
        for param in all_params:
            self.current_values[param.key] = param.default_value
        
        # デフォルトプリセットの作成
        self._initialize_default_presets()
    
    def _initialize_default_presets(self) -> None:
        """デフォルトのプリセットを初期化"""
        # 風推定プリセット
        wind_presets = [
            # 標準プリセット
            ParameterPreset(
                preset_id="wind_estimation_standard",
                name="標準風推定",
                description="一般的なセーリング状況に適した風推定設定",
                namespace=ParameterNamespace.WIND_ESTIMATION,
                parameters={
                    "min_speed_threshold": 2.0,
                    "upwind_threshold": 45.0,
                    "downwind_threshold": 120.0,
                    "min_tack_angle_change": 60.0,
                    "wind_smoothing_window": 5
                },
                tags=["標準", "一般"]
            ),
            # 軽風用プリセット
            ParameterPreset(
                preset_id="wind_estimation_light",
                name="軽風条件",
                description="風が弱い状況での風推定に最適化",
                namespace=ParameterNamespace.WIND_ESTIMATION,
                parameters={
                    "min_speed_threshold": 1.0,
                    "upwind_threshold": 50.0,
                    "downwind_threshold": 130.0,
                    "min_tack_angle_change": 70.0,
                    "wind_smoothing_window": 8
                },
                tags=["軽風", "特殊条件"]
            ),
            # 強風用プリセット
            ParameterPreset(
                preset_id="wind_estimation_strong",
                name="強風条件",
                description="風が強い状況での風推定に最適化",
                namespace=ParameterNamespace.WIND_ESTIMATION,
                parameters={
                    "min_speed_threshold": 3.0,
                    "upwind_threshold": 40.0,
                    "downwind_threshold": 110.0,
                    "min_tack_angle_change": 50.0,
                    "wind_smoothing_window": 3
                },
                tags=["強風", "特殊条件"]
            )
        ]
        
        # 戦略検出プリセット
        strategy_presets = [
            # 標準プリセット
            ParameterPreset(
                preset_id="strategy_detection_standard",
                name="標準戦略検出",
                description="一般的なレース状況に適した戦略検出設定",
                namespace=ParameterNamespace.STRATEGY_DETECTION,
                parameters={
                    "min_wind_shift_angle": 5.0,
                    "wind_forecast_interval": 300,
                    "tack_search_radius": 500,
                    "min_vmg_improvement": 0.05,
                    "layline_safety_margin": 10.0
                },
                tags=["標準", "一般"]
            ),
            # 風変化敏感プリセット
            ParameterPreset(
                preset_id="strategy_detection_sensitive",
                name="風変化敏感",
                description="小さな風向変化も検出するための設定",
                namespace=ParameterNamespace.STRATEGY_DETECTION,
                parameters={
                    "min_wind_shift_angle": 3.0,
                    "wind_forecast_interval": 180,
                    "tack_search_radius": 600,
                    "min_vmg_improvement": 0.03,
                    "layline_safety_margin": 15.0
                },
                tags=["敏感", "詳細"]
            )
        ]
        
        # パフォーマンス分析プリセット
        performance_presets = [
            # 標準プリセット
            ParameterPreset(
                preset_id="performance_analysis_standard",
                name="標準パフォーマンス分析",
                description="一般的なトレーニング分析用設定",
                namespace=ParameterNamespace.PERFORMANCE_ANALYSIS,
                parameters={
                    "performance_window_size": 10,
                    "vmg_reference_enabled": True,
                    "maneuver_analysis_enabled": True
                },
                tags=["標準", "トレーニング"]
            ),
            # 詳細分析プリセット
            ParameterPreset(
                preset_id="performance_analysis_detailed",
                name="詳細パフォーマンス分析",
                description="詳細なパフォーマンス分析用設定",
                namespace=ParameterNamespace.PERFORMANCE_ANALYSIS,
                parameters={
                    "performance_window_size": 5,
                    "vmg_reference_enabled": True,
                    "maneuver_analysis_enabled": True
                },
                tags=["詳細", "高度"]
            )
        ]
        
        # すべてのプリセットをマージして管理に追加
        all_presets = wind_presets + strategy_presets + performance_presets
        for preset in all_presets:
            self.add_preset(preset)
    
    def add_parameter_definition(self, definition: ParameterDefinition) -> None:
        """
        パラメータ定義を追加
        
        Parameters:
        -----------
        definition : ParameterDefinition
            追加するパラメータ定義
        """
        if definition.key in self.parameter_definitions:
            self.logger.warning(f"パラメータキー '{definition.key}' は既に存在します。上書きします。")
        
        self.parameter_definitions[definition.key] = definition
        
        # デフォルト値を設定
        if definition.key not in self.current_values:
            self.current_values[definition.key] = definition.default_value
    
    def get_parameter_definition(self, key: str) -> Optional[ParameterDefinition]:
        """
        パラメータ定義を取得
        
        Parameters:
        -----------
        key : str
            パラメータキー
            
        Returns:
        --------
        Optional[ParameterDefinition]
            パラメータ定義（存在しなければNone）
        """
        return self.parameter_definitions.get(key)
    
    def set_parameter(self, key: str, value: Any) -> bool:
        """
        パラメータの値を設定
        
        Parameters:
        -----------
        key : str
            パラメータキー
        value : Any
            パラメータ値
            
        Returns:
        --------
        bool
            設定に成功したかどうか
        """
        # 定義が存在するか確認
        definition = self.parameter_definitions.get(key)
        if definition is None:
            self.logger.warning(f"未定義のパラメータキー '{key}' です。")
            return False
        
        # 値の検証
        if not definition.validate_value(value):
            self.logger.warning(f"パラメータ '{key}' に対して無効な値 '{value}' です。")
            return False
        
        # 値の設定
        old_value = self.current_values.get(key)
        self.current_values[key] = value
        
        # 値が変更された場合にコールバックを呼び出し
        if old_value != value:
            self._notify_parameters_changed({key: value})
        
        return True
    
    def set_parameters(self, parameters: Dict[str, Any]) -> Dict[str, bool]:
        """
        複数のパラメータの値を一度に設定
        
        Parameters:
        -----------
        parameters : Dict[str, Any]
            パラメータキーと値の辞書
            
        Returns:
        --------
        Dict[str, bool]
            パラメータキーごとの設定結果
        """
        results = {}
        changed_params = {}
        
        for key, value in parameters.items():
            result = self.set_parameter(key, value)
            results[key] = result
            
            if result:
                changed_params[key] = value
        
        # 変更があった場合にコールバックを呼び出し
        if changed_params:
            self._notify_parameters_changed(changed_params)
        
        return results
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """
        パラメータの値を取得
        
        Parameters:
        -----------
        key : str
            パラメータキー
        default : Any, optional
            パラメータが存在しない場合のデフォルト値
            
        Returns:
        --------
        Any
            パラメータ値
        """
        return self.current_values.get(key, default)
    
    def get_parameters_by_namespace(self, namespace: str) -> Dict[str, Any]:
        """
        指定名前空間のパラメータ値を取得
        
        Parameters:
        -----------
        namespace : str
            パラメータの名前空間
            
        Returns:
        --------
        Dict[str, Any]
            パラメータキーと値の辞書
        """
        result = {}
        
        for key, definition in self.parameter_definitions.items():
            if definition.namespace == namespace:
                result[key] = self.current_values.get(key, definition.default_value)
        
        return result
    
    def get_all_parameters(self) -> Dict[str, Any]:
        """
        すべてのパラメータ値を取得
        
        Returns:
        --------
        Dict[str, Any]
            パラメータキーと値の辞書
        """
        return self.current_values.copy()
    
    def reset_parameter(self, key: str) -> bool:
        """
        パラメータをデフォルト値にリセット
        
        Parameters:
        -----------
        key : str
            パラメータキー
            
        Returns:
        --------
        bool
            リセットに成功したかどうか
        """
        definition = self.parameter_definitions.get(key)
        if definition is None:
            return False
        
        old_value = self.current_values.get(key)
        self.current_values[key] = definition.default_value
        
        # 値が変更された場合にコールバックを呼び出し
        if old_value != definition.default_value:
            self._notify_parameters_changed({key: definition.default_value})
        
        return True
    
    def reset_all_parameters(self) -> None:
        """すべてのパラメータをデフォルト値にリセット"""
        changed_params = {}
        
        for key, definition in self.parameter_definitions.items():
            old_value = self.current_values.get(key)
            default_value = definition.default_value
            
            self.current_values[key] = default_value
            
            if old_value != default_value:
                changed_params[key] = default_value
        
        # 変更があった場合にコールバックを呼び出し
        if changed_params:
            self._notify_parameters_changed(changed_params)
    
    def reset_namespace_parameters(self, namespace: str) -> None:
        """
        指定名前空間のパラメータをデフォルト値にリセット
        
        Parameters:
        -----------
        namespace : str
            パラメータの名前空間
        """
        changed_params = {}
        
        for key, definition in self.parameter_definitions.items():
            if definition.namespace == namespace:
                old_value = self.current_values.get(key)
                default_value = definition.default_value
                
                self.current_values[key] = default_value
                
                if old_value != default_value:
                    changed_params[key] = default_value
        
        # 変更があった場合にコールバックを呼び出し
        if changed_params:
            self._notify_parameters_changed(changed_params)
    
    def add_preset(self, preset: ParameterPreset) -> None:
        """
        プリセットを追加
        
        Parameters:
        -----------
        preset : ParameterPreset
            追加するプリセット
        """
        if preset.preset_id in self.presets:
            self.logger.warning(f"プリセットID '{preset.preset_id}' は既に存在します。上書きします。")
        
        self.presets[preset.preset_id] = preset
    
    def get_preset(self, preset_id: str) -> Optional[ParameterPreset]:
        """
        プリセットを取得
        
        Parameters:
        -----------
        preset_id : str
            プリセットID
            
        Returns:
        --------
        Optional[ParameterPreset]
            プリセット（存在しなければNone）
        """
        return self.presets.get(preset_id)
    
    def delete_preset(self, preset_id: str) -> bool:
        """
        プリセットを削除
        
        Parameters:
        -----------
        preset_id : str
            プリセットID
            
        Returns:
        --------
        bool
            削除に成功したかどうか
        """
        if preset_id in self.presets:
            del self.presets[preset_id]
            return True
        return False
    
    def get_presets_by_namespace(self, namespace: str) -> List[ParameterPreset]:
        """
        指定名前空間のプリセットを取得
        
        Parameters:
        -----------
        namespace : str
            プリセットの名前空間
            
        Returns:
        --------
        List[ParameterPreset]
            プリセットのリスト
        """
        return [preset for preset in self.presets.values() if preset.namespace == namespace]
    
    def get_all_presets(self) -> List[ParameterPreset]:
        """
        すべてのプリセットを取得
        
        Returns:
        --------
        List[ParameterPreset]
            プリセットのリスト
        """
        return list(self.presets.values())
    
    def apply_preset(self, preset_id: str) -> bool:
        """
        プリセットを適用
        
        Parameters:
        -----------
        preset_id : str
            プリセットID
            
        Returns:
        --------
        bool
            適用に成功したかどうか
        """
        preset = self.presets.get(preset_id)
        if preset is None:
            self.logger.warning(f"プリセットID '{preset_id}' が見つかりません。")
            return False
        
        # プリセットのパラメータを適用
        changed_params = {}
        
        for key, value in preset.parameters.items():
            definition = self.parameter_definitions.get(key)
            if definition is None:
                self.logger.warning(f"未定義のパラメータキー '{key}' がプリセットに含まれています。")
                continue
            
            if not definition.validate_value(value):
                self.logger.warning(f"プリセット内のパラメータ '{key}' に対して無効な値 '{value}' です。")
                continue
            
            old_value = self.current_values.get(key)
            self.current_values[key] = value
            
            if old_value != value:
                changed_params[key] = value
        
        # 変更があった場合にコールバックを呼び出し
        if changed_params:
            self._notify_parameters_changed(changed_params)
        
        return True
    
    def create_preset_from_current(self, preset_id: str, name: str, description: str, 
                               namespace: str = ParameterNamespace.GENERAL,
                               tags: List[str] = None) -> ParameterPreset:
        """
        現在のパラメータ値からプリセットを作成
        
        Parameters:
        -----------
        preset_id : str
            プリセットID
        name : str
            プリセット名
        description : str
            プリセットの説明
        namespace : str, optional
            プリセットの名前空間
        tags : List[str], optional
            分類タグ
            
        Returns:
        --------
        ParameterPreset
            作成されたプリセット
        """
        # 指定名前空間のパラメータを収集
        if namespace != ParameterNamespace.GENERAL:
            params = self.get_parameters_by_namespace(namespace)
        else:
            params = self.get_all_parameters()
        
        # プリセットを作成
        preset = ParameterPreset(
            preset_id=preset_id,
            name=name,
            description=description,
            parameters=params,
            namespace=namespace,
            tags=tags
        )
        
        # プリセットを追加
        self.add_preset(preset)
        
        return preset
    
    def add_parameters_changed_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        パラメータ変更時のコールバックを追加
        
        Parameters:
        -----------
        callback : Callable[[Dict[str, Any]], None]
            変更されたパラメータを受け取るコールバック関数
        """
        if callback not in self.on_parameters_changed_callbacks:
            self.on_parameters_changed_callbacks.append(callback)
    
    def remove_parameters_changed_callback(self, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """
        パラメータ変更時のコールバックを削除
        
        Parameters:
        -----------
        callback : Callable[[Dict[str, Any]], None]
            削除するコールバック関数
            
        Returns:
        --------
        bool
            削除に成功したかどうか
        """
        if callback in self.on_parameters_changed_callbacks:
            self.on_parameters_changed_callbacks.remove(callback)
            return True
        return False
    
    def _notify_parameters_changed(self, changed_params: Dict[str, Any]) -> None:
        """
        パラメータ変更を通知
        
        Parameters:
        -----------
        changed_params : Dict[str, Any]
            変更されたパラメータのキーと値
        """
        for callback in self.on_parameters_changed_callbacks:
            try:
                callback(changed_params)
            except Exception as e:
                self.logger.error(f"パラメータ変更コールバックでエラーが発生しました: {e}")
    
    def save_to_storage(self) -> bool:
        """
        現在のパラメータとプリセットをストレージに保存
        
        Returns:
        --------
        bool
            保存に成功したかどうか
        """
        if self.storage is None:
            self.logger.warning("ストレージインターフェースが設定されていません。")
            return False
        
        try:
            # パラメータ値の保存
            params_key = f"{self.storage_key_prefix}values"
            success1 = self.storage.save(params_key, self.current_values)
            
            # プリセットの保存
            presets_key = f"{self.storage_key_prefix}presets"
            presets_dict = {preset_id: preset.to_dict() for preset_id, preset in self.presets.items()}
            success2 = self.storage.save(presets_key, presets_dict)
            
            return success1 and success2
            
        except Exception as e:
            self.logger.error(f"パラメータの保存中にエラーが発生しました: {e}")
            return False
    
    def load_from_storage(self) -> bool:
        """
        ストレージからパラメータとプリセットを読み込み
        
        Returns:
        --------
        bool
            読み込みに成功したかどうか
        """
        if self.storage is None:
            self.logger.warning("ストレージインターフェースが設定されていません。")
            return False
        
        try:
            # パラメータ値の読み込み
            params_key = f"{self.storage_key_prefix}values"
            stored_values = self.storage.load(params_key)
            
            if stored_values:
                # 有効なパラメータのみ設定
                for key, value in stored_values.items():
                    if key in self.parameter_definitions:
                        definition = self.parameter_definitions[key]
                        if definition.validate_value(value):
                            self.current_values[key] = value
            
            # プリセットの読み込み
            presets_key = f"{self.storage_key_prefix}presets"
            stored_presets = self.storage.load(presets_key)
            
            if stored_presets:
                for preset_id, preset_data in stored_presets.items():
                    preset = ParameterPreset.from_dict(preset_data)
                    self.presets[preset_id] = preset
            
            return True
            
        except Exception as e:
            self.logger.error(f"パラメータの読み込み中にエラーが発生しました: {e}")
            return False
    
    def export_parameters(self, filename: str) -> bool:
        """
        パラメータとプリセットをJSONファイルにエクスポート
        
        Parameters:
        -----------
        filename : str
            エクスポート先のファイル名
            
        Returns:
        --------
        bool
            エクスポートに成功したかどうか
        """
        try:
            export_data = {
                "parameters": self.current_values,
                "presets": {preset_id: preset.to_dict() for preset_id, preset in self.presets.items()},
                "export_time": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"パラメータのエクスポート中にエラーが発生しました: {e}")
            return False
    
    def import_parameters(self, filename: str, import_params: bool = True, import_presets: bool = True) -> bool:
        """
        JSONファイルからパラメータとプリセットをインポート
        
        Parameters:
        -----------
        filename : str
            インポート元のファイル名
        import_params : bool, optional
            パラメータをインポートするかどうか
        import_presets : bool, optional
            プリセットをインポートするかどうか
            
        Returns:
        --------
        bool
            インポートに成功したかどうか
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # パラメータのインポート
            if import_params and "parameters" in import_data:
                for key, value in import_data["parameters"].items():
                    self.set_parameter(key, value)
            
            # プリセットのインポート
            if import_presets and "presets" in import_data:
                for preset_id, preset_data in import_data["presets"].items():
                    preset = ParameterPreset.from_dict(preset_data)
                    self.add_preset(preset)
            
            return True
            
        except Exception as e:
            self.logger.error(f"パラメータのインポート中にエラーが発生しました: {e}")
            return False
    
    def get_parameters_summary(self) -> Dict[str, Any]:
        """
        パラメータ管理の概要情報を取得
        
        Returns:
        --------
        Dict[str, Any]
            概要情報の辞書
        """
        # 名前空間ごとのパラメータ数
        namespace_counts = {}
        for definition in self.parameter_definitions.values():
            namespace = definition.namespace
            namespace_counts[namespace] = namespace_counts.get(namespace, 0) + 1
        
        # 名前空間ごとのプリセット数
        preset_counts = {}
        for preset in self.presets.values():
            namespace = preset.namespace
            preset_counts[namespace] = preset_counts.get(namespace, 0) + 1
        
        return {
            "total_parameters": len(self.parameter_definitions),
            "total_presets": len(self.presets),
            "namespace_parameters": namespace_counts,
            "namespace_presets": preset_counts,
            "modified_parameters": sum(1 for key, value in self.current_values.items() 
                                    if key in self.parameter_definitions and value != self.parameter_definitions[key].default_value)
        }
