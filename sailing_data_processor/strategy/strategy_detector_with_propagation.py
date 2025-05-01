"""
StrategyDetectorWithPropagation

This class extends the base strategy detector with wind propagation capabilities.
"""

import numpy as np
import math
import warnings
import logging
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
from functools import lru_cache

# Import base classes
from sailing_data_processor.strategy.detector import StrategyDetector
from sailing_data_processor.strategy.points import StrategyPoint, WindShiftPoint, TackPoint, LaylinePoint

# Set up logger
logger = logging.getLogger(__name__)

class StrategyDetectorWithPropagation(StrategyDetector):
    """
    Strategy Detector with Wind Propagation capabilities
    
    Extends StrategyDetector with wind propagation and prediction
    to enable more advanced strategic analysis.
    """
    
    def __init__(self, vmg_calculator=None, wind_fusion_system=None):
        """
        Initialize the detector
        
        Parameters:
        -----------
        vmg_calculator : OptimalVMGCalculator, optional
            VMG calculation tool
        wind_fusion_system : WindFieldFusionSystem, optional
            Wind prediction system
        """
        # Call parent constructor
        super().__init__(vmg_calculator)
        
        # Store wind fusion system
        self.wind_fusion_system = wind_fusion_system
        
        # Propagation configuration
        self.propagation_config = {
            'wind_shift_prediction_horizon': 1800,  # Prediction horizon in seconds
            'prediction_time_step': 300,           # Time step for predictions
            'wind_shift_confidence_threshold': 0.7, # Minimum confidence for predictions
            'min_propagation_distance': 1000,      # Minimum distance for propagation
            'prediction_confidence_decay': 0.1,    # Decay factor for prediction confidence
            'use_historical_data': True            # Whether to use historical data
        }
    
    def detect_wind_shifts_with_propagation(self, course_data: Dict[str, Any], 
                                         wind_field: Dict[str, Any]) -> List[WindShiftPoint]:
        """
        Detect wind shifts with propagation model
        
        Parameters:
        -----------
        course_data : Dict[str, Any]
            Course data
        wind_field : Dict[str, Any]
            Wind field data
            
        Returns:
        --------
        List[WindShiftPoint]
            Detected wind shift points
        """
        if not wind_field or 'wind_direction' not in wind_field:
            return []
        
        # Initialize predicted wind shifts
        predicted_shifts = []
        
        if self.wind_fusion_system and hasattr(self.wind_fusion_system, 'predict_wind_field'):
            try:
                # Get reference time
                reference_time = None
                if 'time' in wind_field:
                    reference_time = wind_field['time']
                elif 'start_time' in course_data:
                    reference_time = course_data['start_time']
                
                if reference_time:
                    # Get prediction parameters
                    horizon = self.propagation_config['wind_shift_prediction_horizon']
                    time_step = self.propagation_config['prediction_time_step']
                    
                    # Predict wind shifts for future time points
                    for t in range(time_step, horizon + 1, time_step):
                        target_time = reference_time + timedelta(seconds=t)
                        
                        # Predict wind field
                        predicted_field = self.wind_fusion_system.predict_wind_field(
                            target_time=target_time,
                            current_wind_field=wind_field
                        )
                        
                        if predicted_field:
                            # Detect wind shifts in the predicted field
                            leg_shifts = self._detect_wind_shifts_in_legs(
                                course_data, predicted_field, target_time
                            )
                            
                            # Apply confidence decay based on prediction time
                            for shift in leg_shifts:
                                decay_factor = 1.0 - (t / horizon) * self.propagation_config['prediction_confidence_decay']
                                shift.shift_probability *= decay_factor
                            
                            predicted_shifts.extend(leg_shifts)
            
            except Exception as e:
                logger.error(f"Wind prediction error: {e}")
        
        # Detect wind shifts in current data
        current_shifts = super().detect_wind_shifts(course_data, wind_field)
        
        # Combine current and predicted shifts
        all_shifts = current_shifts + predicted_shifts
        
        # Filter duplicate wind shift points
        filtered_shifts = self._filter_duplicate_shift_points(all_shifts)
        
        # Apply confidence threshold
        threshold = self.propagation_config['wind_shift_confidence_threshold']
        final_shifts = [shift for shift in filtered_shifts 
                      if shift.shift_probability >= threshold]
        
        return final_shifts
    
    def _detect_wind_shifts_in_legs(self, course_data: Dict[str, Any], 
                                 wind_field: Dict[str, Any],
                                 target_time: datetime) -> List[WindShiftPoint]:
        """
        Detect wind shifts in course legs
        
        Parameters:
        -----------
        course_data : Dict[str, Any]
            Course data
        wind_field : Dict[str, Any]
            Wind field data
        target_time : datetime
            Target time for detection
            
        Returns:
        --------
        List[WindShiftPoint]
            Detected wind shift points
        """
        # Check if legs data exists
        if 'legs' not in course_data:
            return []
        
        shift_points = []
        
        # Process each leg
        for leg in course_data['legs']:
            # Skip legs without path data
            if 'path' not in leg or 'path_points' not in leg['path']:
                continue
            
            path_points = leg['path']['path_points']
            
            # Skip legs with insufficient points
            if len(path_points) < 2:
                continue
            
            # Track previous wind data
            prev_wind = None
            
            # Process each point in the path
            for i, point in enumerate(path_points):
                # Skip points without position data
                if 'lat' not in point or 'lon' not in point:
                    continue
                
                lat, lon = point['lat'], point['lon']
                
                # Get wind at position
                wind = self._get_wind_at_position(lat, lon, target_time, wind_field)
                
                # Skip if wind data not available
                if not wind:
                    continue
                
                # Compare with previous point to detect shifts
                if prev_wind:
                    # Calculate direction difference
                    dir_diff = self._angle_difference(
                        wind['direction'], prev_wind['direction']
                    )
                    
                    # Check if shift exceeds minimum threshold
                    min_shift = self.config['min_wind_shift_angle']
                    if abs(dir_diff) >= min_shift:
                        # Calculate midpoint between current and previous position
                        midlat = (lat + path_points[i-1]['lat']) / 2
                        midlon = (lon + path_points[i-1]['lon']) / 2
                        
                        # Get minimum confidence of the two wind measurements
                        confidence = min(
                            wind.get('confidence', 0.8),
                            prev_wind.get('confidence', 0.8)
                        )
                        
                        # Get maximum variability of the two wind measurements
                        variability = max(
                            wind.get('variability', 0.2),
                            prev_wind.get('variability', 0.2)
                        )
                        
                        # Create wind shift point
                        shift_point = WindShiftPoint(
                            position=(midlat, midlon),
                            time_estimate=target_time
                        )
                        
                        # Set shift properties
                        shift_point.shift_angle = dir_diff
                        shift_point.before_direction = prev_wind['direction']
                        shift_point.after_direction = wind['direction']
                        shift_point.wind_speed = (prev_wind['speed'] + wind['speed']) / 2
                        
                        # Calculate probability
                        raw_probability = confidence * (1.0 - variability)
                        
                        # Adjust probability based on shift magnitude
                        # Larger shifts are given higher weight
                        angle_weight = min(1.0, abs(dir_diff) / 45.0)
                        shift_point.shift_probability = raw_probability * (0.5 + 0.5 * angle_weight)
                        
                        # Calculate strategic score
                        strategic_score, note = self._calculate_strategic_score(
                            "wind_shift", "", "",
                            (midlat, midlon), target_time, wind_field
                        )
                        
                        shift_point.strategic_score = strategic_score
                        shift_point.note = note
                        
                        # Add to results
                        shift_points.append(shift_point)
                
                # Store current wind for next iteration
                prev_wind = wind
        
        return shift_points
    
    def _filter_duplicate_shift_points(self, shift_points: List[WindShiftPoint]) -> List[WindShiftPoint]:
        """
        Filter duplicate wind shift points
        
        Parameters:
        -----------
        shift_points : List[WindShiftPoint]
            List of wind shift points
            
        Returns:
        --------
        List[WindShiftPoint]
            Filtered list of unique shift points
        """
        if len(shift_points) <= 1:
            return shift_points
        
        filtered_points = []
        sorted_points = sorted(shift_points, 
                              key=lambda p: self._normalize_to_timestamp(p.time_estimate))
        
        for point in sorted_points:
            is_duplicate = False
            
            for existing in filtered_points:
                # Check if position is within 300m
                position_close = self._calculate_distance(
                    point.position[0], point.position[1],
                    existing.position[0], existing.position[1]
                ) < 300
                
                # Check if time is within 5 minutes
                time_diff = self._get_time_difference_seconds(
                    point.time_estimate, existing.time_estimate
                )
                time_close = time_diff < 300
                
                # Check if wind shift angles are similar (within 15 degrees)
                angle_similar = abs(self._angle_difference(
                    point.shift_angle, existing.shift_angle
                )) < 15
                
                # Consider as duplicate if all conditions met
                if position_close and time_close and angle_similar:
                    # Keep point with higher probability
                    if point.shift_probability > existing.shift_probability:
                        # Replace existing point with current one
                        filtered_points.remove(existing)
                        filtered_points.append(point)
                    
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_points.append(point)
        
        return filtered_points
    
    def _normalize_to_timestamp(self, t) -> float:
        """
        様々な時間表現から統一したUNIXタイムスタンプを作成
        
        Parameters:
        -----------
        t : any
            様々な時間表現(datetime, timedelta, int, float等)
            
        Returns:
        --------
        float
            UNIXタイムスタンプ形式の値
        """
        if isinstance(t, datetime):
            # datetimeをUNIXタイムスタンプに変換
            return t.timestamp()
        elif isinstance(t, timedelta):
            # timedeltaを秒に変換
            return t.total_seconds()
        elif isinstance(t, (int, float)):
            # 数値はそのままfloatで返す
            return float(t)
        elif isinstance(t, dict):
            # 辞書型の場合
            if 'timestamp' in t:
                # timestampキーを持つ辞書の場合
                return float(t['timestamp'])
            else:
                # timestampキーがない辞書の場合はエラー防止のため無限大を返す
                return float('inf')
        elif isinstance(t, str):
            try:
                # 数値文字列の場合は数値に変換
                return float(t)
            except ValueError:
                try:
                    # ISO形式の日時文字列
                    dt = datetime.fromisoformat(t.replace('Z', '+00:00'))
                    return dt.timestamp()
                except ValueError:
                    # 変換できない場合は無限大
                    return float('inf')
        else:
            # その他の型は文字列に変換してから数値化
            try:
                return float(str(t))
            except ValueError:
                # 変換できない場合は無限大（対応する順序）
                return float('inf')
    
    def _get_time_difference_seconds(self, time1, time2) -> float:
        """
        Calculate time difference in seconds
        
        Parameters:
        -----------
        time1, time2 : any
            Time values in various formats (datetime, timedelta, int, float, etc)
            
        Returns:
        --------
        float
            Time difference in seconds, or infinity if calculation fails
        """
        # Try to calculate time difference
        try:
            ts1 = self._normalize_to_timestamp(time1)
            ts2 = self._normalize_to_timestamp(time2)
            
            # Return infinity if either time couldn't be normalized
            if ts1 == float('inf') or ts2 == float('inf'):
                return float('inf')
                
            return abs(ts1 - ts2)
        except Exception as e:
            logger.error(f"Time difference calculation error: {e}")
            # Return infinity on error
            return float('inf')
    
    def detect_optimal_tacks(self, course_data: Dict[str, Any], 
                          wind_field: Dict[str, Any]) -> List[TackPoint]:
        """
        Detect optimal tack points
        
        Parameters:
        -----------
        course_data : Dict[str, Any]
            Course data
        wind_field : Dict[str, Any]
            Wind field data
            
        Returns:
        --------
        List[TackPoint]
            Detected optimal tack points
        """
        # Check if VMG calculator is available
        if not self.vmg_calculator:
            logger.warning("VMGCalculator not available, optimal tack detection skipped")
            return []
        
        # Use base implementation for now, will be enhanced later
        return super().detect_optimal_tacks(course_data, wind_field)
    
    def detect_laylines(self, course_data: Dict[str, Any], 
                      wind_field: Dict[str, Any]) -> List[LaylinePoint]:
        """
        Detect layline points
        
        Parameters:
        -----------
        course_data : Dict[str, Any]
            Course data
        wind_field : Dict[str, Any]
            Wind field data
            
        Returns:
        --------
        List[LaylinePoint]
            Detected layline points
        """
        # Check if VMG calculator is available
        if not self.vmg_calculator:
            logger.warning("VMGCalculator not available, layline detection skipped")
            return []
        
        # Use base implementation for now, will be enhanced later
        return super().detect_laylines(course_data, wind_field)
    
    def _determine_tack_type(self, bearing: float, wind_direction: float) -> str:
        """
        Determine tack type
        
        Parameters:
        -----------
        bearing : float
            Boat heading in degrees
        wind_direction : float
            Wind direction in degrees (meteorological convention)
            
        Returns:
        --------
        str
            Tack type ('port' or 'starboard')
        """
        # Calculate relative angle to wind
        relative_angle = self._angle_difference(bearing, wind_direction)
        
        # Determine tack type based on angle
        return 'port' if relative_angle < 0 else 'starboard'
    
    def _calculate_strategic_score(self, maneuver_type: str, 
                                 before_tack_type: str, 
                                 after_tack_type: str,
                                 position: Tuple[float, float], 
                                 time_point, 
                                 wind_field: Dict[str, Any]) -> Tuple[float, str]:
        """
        Calculate strategic score for a maneuver
        
        Parameters:
        -----------
        maneuver_type : str
            Type of maneuver ('tack', 'gybe', 'wind_shift', etc)
        before_tack_type : str
            Tack type before maneuver ('port' or 'starboard')
        after_tack_type : str
            Tack type after maneuver ('port' or 'starboard')
        position : Tuple[float, float]
            Position of maneuver (latitude, longitude)
        time_point : any
            Time of maneuver
        wind_field : Dict[str, Any]
            Wind field data
            
        Returns:
        --------
        Tuple[float, str]
            (Strategic score (0-1), explanation note)
        """
        score = 0.5  # Default score
        note = "Standard maneuver"
        
        # Get wind at position
        wind = self._get_wind_at_position(position[0], position[1], time_point, wind_field)
        
        if not wind:
            return score, note
        
        # Evaluate based on maneuver type
        if maneuver_type == 'tack':
            # Get wind variability
            wind_shift_probability = wind.get('variability', 0.2)
            
            # Evaluate tack
            if before_tack_type != after_tack_type:
                # Check if tack is in response to wind shift
                if wind_shift_probability > 0.6:
                    # Good tack in response to variable winds
                    score = 0.8
                    note = "Responsive tack to changing wind"
                elif wind.get('confidence', 0.5) < 0.4:
                    # Tack in uncertain wind conditions
                    score = 0.3
                    note = "Tack in uncertain wind conditions"
                else:
                    # Standard tack
                    score = 0.5
                    note = "Standard tack"
            
        elif maneuver_type == 'wind_shift':
            # Evaluate wind shift
            shift_angle = abs(self._angle_difference(
                wind.get('direction', 0), 
                wind.get('before_direction', wind.get('direction', 0))
            ))
            
            if shift_angle > 20:
                # Major wind shift
                score = 0.9
                note = "Major wind shift detected"
            elif shift_angle > 10:
                # Moderate wind shift
                score = 0.7
                note = "Moderate wind shift"
            else:
                # Minor wind shift
                score = 0.5
                note = "Minor wind shift"
            
            # Check for speed changes
            if 'before_speed' in wind and 'speed' in wind:
                speed_change = abs(wind['speed'] - wind['before_speed'])
                if speed_change > 5:
                    score += 0.1
                    note += " with significant speed change"
        
        # Add more complex evaluation in future versions
        if 'lat_grid' in wind_field and 'lon_grid' in wind_field:
            # Placeholder for future enhancements
            pass
        
        return min(1.0, score), note
    
    def _filter_duplicate_tack_points(self, tack_points: List[TackPoint]) -> List[TackPoint]:
        """
        Filter duplicate tack points
        
        Parameters:
        -----------
        tack_points : List[TackPoint]
            List of tack points
            
        Returns:
        --------
        List[TackPoint]
            Filtered list of unique tack points
        """
        # Similar to _filter_duplicate_shift_points
        if len(tack_points) <= 1:
            return tack_points
        
        filtered_points = []
        for point in tack_points:
            is_duplicate = False
            
            for existing in filtered_points:
                # Check if position is close
                position_close = self._calculate_distance(
                    point.position[0], point.position[1],
                    existing.position[0], existing.position[1]
                ) < 200  # Smaller distance for tacks
                
                # Check if VMG gain is similar
                vmg_similar = abs(point.vmg_gain - existing.vmg_gain) < 0.05
                
                if position_close and vmg_similar:
                    # Keep point with higher VMG gain
                    if point.vmg_gain > existing.vmg_gain:
                        filtered_points.remove(existing)
                        filtered_points.append(point)
                    
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_points.append(point)
        
        return filtered_points
    
    def _filter_duplicate_laylines(self, layline_points: List[LaylinePoint]) -> List[LaylinePoint]:
        """
        Filter duplicate layline points
        
        Parameters:
        -----------
        layline_points : List[LaylinePoint]
            List of layline points
            
        Returns:
        --------
        List[LaylinePoint]
            Filtered list of unique layline points
        """
        # Similar to _filter_duplicate_shift_points
        if len(layline_points) <= 1:
            return layline_points
        
        filtered_points = []
        for point in layline_points:
            is_duplicate = False
            
            for existing in filtered_points:
                # Check if for same mark
                same_mark = point.mark_id == existing.mark_id
                
                # Check if position is close
                position_close = self._calculate_distance(
                    point.position[0], point.position[1],
                    existing.position[0], existing.position[1]
                ) < 300
                
                if same_mark and position_close:
                    # Keep point with higher confidence
                    if point.confidence > existing.confidence:
                        filtered_points.remove(existing)
                        filtered_points.append(point)
                    
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_points.append(point)
        
        return filtered_points
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points
        
        Parameters:
        -----------
        lat1, lon1 : float
            Coordinates of first point
        lat2, lon2 : float
            Coordinates of second point
            
        Returns:
        --------
        float
            Distance in meters
        """
        # Earth radius in meters
        R = 6371000
        
        # Convert coordinates to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Calculate differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine formula
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance