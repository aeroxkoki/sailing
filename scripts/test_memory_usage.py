#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory usage test script for the sailing strategy analyzer.
This script profiles memory usage during data processing and wind estimation.

Usage:
    python3 -m memory_profiler scripts/test_memory_usage.py

Requirements:
    pip install memory-profiler
"""

import os
import sys
import gc
import time
import pandas as pd
import numpy as np
from memory_profiler import profile

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from sailing_data_processor.core import DataProcessor
from sailing_data_processor.wind_estimator import WindEstimator
from sailing_data_processor.data_model.container import SailingDataContainer

# Define sample data path
SAMPLE_DATA_PATH = os.path.join(project_root, 'resources', 'sample_data', 'sample_gps_track.csv')


@profile
def test_data_processing():
    """Test memory usage during data processing."""
    print("Testing DataProcessor memory usage...")
    
    # Load sample data
    if not os.path.exists(SAMPLE_DATA_PATH):
        print(f"Sample data not found at {SAMPLE_DATA_PATH}")
        return
    
    # Create data processor
    processor = DataProcessor()
    
    # Process data
    print("Loading and processing data...")
    container = processor.process_file(SAMPLE_DATA_PATH)
    
    # Print some stats
    print(f"Processed {len(container.data)} data points")
    
    # Force garbage collection
    del container
    gc.collect()
    
    print("DataProcessor memory test completed")


@profile
def test_wind_estimation():
    """Test memory usage during wind estimation."""
    print("Testing WindEstimator memory usage...")
    
    # Load sample data
    if not os.path.exists(SAMPLE_DATA_PATH):
        print(f"Sample data not found at {SAMPLE_DATA_PATH}")
        return
    
    # Create data processor and process data
    processor = DataProcessor()
    container = processor.process_file(SAMPLE_DATA_PATH)
    
    # Create wind estimator
    estimator = WindEstimator()
    
    # Estimate wind
    print("Estimating wind...")
    wind_data = estimator.estimate_wind(container)
    
    # Print some stats
    print(f"Estimated wind for {len(wind_data)} data points")
    
    # Force garbage collection
    del container
    del wind_data
    gc.collect()
    
    print("WindEstimator memory test completed")


@profile
def test_large_dataset_simulation():
    """Simulate processing a large dataset by creating and processing chunks."""
    print("Testing large dataset simulation...")
    
    # Create a large sample dataset in memory
    print("Creating large sample dataset...")
    
    # Base data
    if os.path.exists(SAMPLE_DATA_PATH):
        base_data = pd.read_csv(SAMPLE_DATA_PATH)
        # Make sure we have required columns
        if not all(col in base_data.columns for col in ['latitude', 'longitude', 'speed', 'timestamp']):
            # Create dummy data if sample doesn't have required columns
            base_data = pd.DataFrame({
                'latitude': np.random.uniform(34.0, 35.0, 1000),
                'longitude': np.random.uniform(135.0, 136.0, 1000),
                'speed': np.random.uniform(0, 10, 1000),
                'timestamp': pd.date_range(start='2023-01-01', periods=1000, freq='10S'),
            })
    else:
        # Create dummy data if sample doesn't exist
        base_data = pd.DataFrame({
            'latitude': np.random.uniform(34.0, 35.0, 1000),
            'longitude': np.random.uniform(135.0, 136.0, 1000),
            'speed': np.random.uniform(0, 10, 1000),
            'timestamp': pd.date_range(start='2023-01-01', periods=1000, freq='10S'),
        })
    
    # Create data processor and wind estimator
    processor = DataProcessor()
    estimator = WindEstimator()
    
    # Process data in chunks to simulate large dataset
    chunk_size = 1000
    num_chunks = 10
    
    for i in range(num_chunks):
        print(f"Processing chunk {i+1}/{num_chunks}...")
        
        # Create chunk with slight variations
        chunk = base_data.copy()
        chunk['latitude'] += np.random.normal(0, 0.001, len(chunk))
        chunk['longitude'] += np.random.normal(0, 0.001, len(chunk))
        chunk['speed'] += np.random.normal(0, 0.5, len(chunk))
        if isinstance(chunk['timestamp'].iloc[0], str):
            chunk['timestamp'] = pd.date_range(
                start=pd.Timestamp(chunk['timestamp'].iloc[0]) + pd.Timedelta(minutes=i*10),
                periods=len(chunk),
                freq='10S'
            )
        else:
            chunk['timestamp'] = pd.date_range(
                start=chunk['timestamp'].iloc[0] + pd.Timedelta(minutes=i*10),
                periods=len(chunk),
                freq='10S'
            )
        
        # Process chunk
        temp_file = f"/tmp/temp_chunk_{i}.csv"
        chunk.to_csv(temp_file, index=False)
        
        container = processor.process_file(temp_file)
        wind_data = estimator.estimate_wind(container)
        
        # Print some stats
        print(f"  Processed {len(container.data)} points, estimated wind for {len(wind_data)} points")
        
        # Clean up
        del container
        del wind_data
        gc.collect()
        
        # Remove temp file
        os.remove(temp_file)
        
        # Small pause to allow memory to be released
        time.sleep(1)
    
    print("Large dataset simulation completed")


if __name__ == "__main__":
    print("=== Memory Usage Testing ===")
    print("Running memory tests for Sailing Strategy Analyzer components...")
    
    # Run tests
    test_data_processing()
    test_wind_estimation()
    test_large_dataset_simulation()
    
    print("All memory tests completed!")
