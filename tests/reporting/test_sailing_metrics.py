# -*- coding: utf-8 -*-
"""
Test module for sailing_metrics.py
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from sailing_data_processor.reporting.data_processing.metrics import (
    SailingMetricsCalculator,
    VMGCalculator,
    ManeuverEfficiencyCalculator,
    LegAnalysisCalculator,
    SpeedMetricsCalculator,
    WindAngleCalculator,
    MetricsUtils
)

class TestSailingMetrics:
    """Test class for sailing metrics"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing"""
        # Sample data for a sailing track
        data = {
            'timestamp': [
                datetime(2025, 4, 1, 12, 0, 0) + timedelta(seconds=i*10) 
                for i in range(20)
            ],
            'latitude': [35.1 + i*0.001 for i in range(20)],
            'longitude': [139.5 + i*0.001 for i in range(20)],
            'speed': [5.0 + i*0.1 for i in range(20)],
            'direction': [45.0 if i < 10 else 135.0 for i in range(20)],  # Direction change at index 10
            'wind_direction': [90.0 for i in range(20)],  # Constant wind direction
            'wind_speed': [10.0 for i in range(20)],  # Constant wind speed
            'leg': [1 if i < 10 else 2 for i in range(20)]  # Two legs
        }
        return pd.DataFrame(data)

    def test_metrics_calculator_initialization(self):
        """Test initialization of the SailingMetricsCalculator"""
        # Test with default parameters
        calculator = SailingMetricsCalculator()
        assert calculator.params['metrics'] == ['vmg', 'target_vmg', 'tacking_efficiency']
        assert calculator.params['speed_column'] == 'speed'
        assert calculator.params['direction_column'] == 'direction'
        assert calculator.params['wind_direction_column'] == 'wind_direction'
        
        # Test with custom parameters
        custom_params = {
            'metrics': ['vmg', 'target_vmg'],
            'speed_column': 'velocity',
            'direction_column': 'heading',
            'wind_direction_column': 'wind_dir',
            'target_position': [35.2, 139.6]
        }
        calculator = SailingMetricsCalculator(custom_params)
        assert calculator.params['metrics'] == ['vmg', 'target_vmg']
        assert calculator.params['speed_column'] == 'velocity'
        assert calculator.params['direction_column'] == 'heading'
        assert calculator.params['wind_direction_column'] == 'wind_dir'
        assert calculator.params['target_position'] == [35.2, 139.6]

    def test_vmg_calculation(self, sample_data):
        """Test VMG calculation"""
        # Initialize VMG calculator with standard params
        params = {
            'speed_column': 'speed',
            'direction_column': 'direction',
            'wind_direction_column': 'wind_direction',
            'wind_speed_column': 'wind_speed'
        }
        vmg_calc = VMGCalculator(params)
        
        # Calculate wind VMG
        result_df = vmg_calc.calculate_wind_vmg(sample_data)
        
        # Check that wind_angle column was created
        assert 'wind_angle' in result_df.columns
        
        # Check that VMG columns were created
        assert 'vmg_upwind' in result_df.columns
        assert 'vmg_downwind' in result_df.columns
        assert 'vmg' in result_df.columns
        
        # Check sailing type classification
        assert 'sailing_type' in result_df.columns
        # First 10 rows should be close to 45 degrees from wind
        assert all(result_df.loc[:9, 'sailing_type'] == 'reaching')
        # Last 10 rows should be close to 45 degrees from wind from the other side
        assert all(result_df.loc[10:, 'sailing_type'] == 'reaching')

    def test_target_vmg_calculation(self, sample_data):
        """Test target VMG calculation"""
        # Initialize VMG calculator with target position
        params = {
            'speed_column': 'speed',
            'direction_column': 'direction',
            'position_columns': ['latitude', 'longitude'],
            'target_position': [35.2, 139.6], # Target is northeast of track
            'time_column': 'timestamp'
        }
        vmg_calc = VMGCalculator(params)
        
        # Calculate target VMG
        result_df = vmg_calc.calculate_target_vmg(sample_data)
        
        # Check that target columns were created
        assert 'target_bearing' in result_df.columns
        assert 'target_angle' in result_df.columns
        assert 'target_vmg' in result_df.columns
        assert 'target_distance' in result_df.columns
        
        # Check estimated arrival time calculation
        assert 'estimated_arrival_time' in result_df.columns

    def test_maneuver_detection(self, sample_data):
        """Test maneuver detection"""
        # Initialize Maneuver calculator
        params = {
            'speed_column': 'speed',
            'direction_column': 'direction',
            'wind_direction_column': 'wind_direction',
            'time_column': 'timestamp',
            'tacking_threshold': 45  # Degrees of direction change to consider a tack
        }
        maneuver_calc = ManeuverEfficiencyCalculator(params)
        
        # Calculate tacking efficiency
        result_df = maneuver_calc.calculate_tacking_efficiency(sample_data)
        
        # Check that direction_diff was calculated
        assert 'direction_diff' in result_df.columns
        
        # Check that tack/jibe detection columns were created
        assert 'is_tack_or_jibe' in result_df.columns
        assert 'is_tacking' in result_df.columns
        assert 'is_jibing' in result_df.columns
        
        # There should be a maneuver at index 10
        assert result_df.loc[10, 'is_tack_or_jibe'] == True
        
        # Check maneuver efficiency calculation
        assert 'maneuver_efficiency' in result_df.columns

    def test_leg_analysis(self, sample_data):
        """Test leg analysis"""
        # Initialize Leg calculator
        params = {
            'speed_column': 'speed',
            'direction_column': 'direction',
            'wind_direction_column': 'wind_direction',
            'wind_speed_column': 'wind_speed',
            'time_column': 'timestamp',
            'leg_column': 'leg'
        }
        leg_calc = LegAnalysisCalculator(params)
        
        # Calculate leg analysis
        result_df = leg_calc.calculate_leg_analysis(sample_data)
        
        # Check that leg-specific columns were created
        assert 'leg_duration' in result_df.columns
        assert 'leg_avg_speed' in result_df.columns
        
        # Ensure there are two different leg values
        unique_legs = result_df['leg'].unique()
        assert len(unique_legs) == 2
        
        # Check that each leg has different stats
        leg1_avg_speed = result_df.loc[result_df['leg'] == 1, 'leg_avg_speed'].iloc[0]
        leg2_avg_speed = result_df.loc[result_df['leg'] == 2, 'leg_avg_speed'].iloc[0]
        assert leg1_avg_speed != leg2_avg_speed

    def test_utils_bearing_calculation(self):
        """Test bearing calculation utility"""
        # Tokyo coordinates
        tokyo_lat, tokyo_lon = 35.6762, 139.6503
        
        # Osaka coordinates (southwest of Tokyo)
        osaka_lat, osaka_lon = 34.6937, 135.5023
        
        # Calculate bearing from Tokyo to Osaka
        bearing = MetricsUtils.calculate_bearing(
            tokyo_lat, tokyo_lon, osaka_lat, osaka_lon
        )
        
        # The bearing should be approximately southwest (around 240-250 degrees)
        assert 240 <= bearing <= 260
        
        # Test the opposite direction (Osaka to Tokyo)
        reverse_bearing = MetricsUtils.calculate_bearing(
            osaka_lat, osaka_lon, tokyo_lat, tokyo_lon
        )
        
        # The reverse bearing should be approximately northeast (around 60-70 degrees)
        assert 60 <= reverse_bearing <= 80

    def test_utils_distance_calculation(self):
        """Test distance calculation utility"""
        # Tokyo coordinates
        tokyo_lat, tokyo_lon = 35.6762, 139.6503
        
        # Osaka coordinates (about 400km from Tokyo)
        osaka_lat, osaka_lon = 34.6937, 135.5023
        
        # Calculate distance from Tokyo to Osaka
        distance = MetricsUtils.calculate_distance(
            tokyo_lat, tokyo_lon, osaka_lat, osaka_lon
        )
        
        # Distance should be around 400km (with some margin)
        assert 390000 <= distance <= 410000  # In meters
