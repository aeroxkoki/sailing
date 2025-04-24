#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
����n�թ��������������

Sn�����o��������n�թ���,�W
iM�n��LD~Y
"""

import os
import sys
import time
import gc
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import psutil
import json
import argparse
import matplotlib.pyplot as plt

# sailing_data_processor ����xnѹ���
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sailing_data_processor.wind_estimator import WindEstimator
from sailing_data_processor.core import SailingDataProcessor

def get_memory_usage():
    """�(n���(ϒ֗ (MB)"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def generate_sample_data(num_points=10000, noise_level=0.2):
    """ƹ�(n����GPS����"""
    print(f"��������- ({num_points}ݤ��)...")
    
    # ��Mnq�~	
    start_lat = 35.6230
    start_lon = 139.7724
    
    # �,�jL�J�n'Mj���O	
    timestamps = []
    latitudes = []
    longitudes = []
    speeds = []
    courses = []
    
    start_time = datetime.now()
    
    for i in range(num_points):
        # B�LN1ғ�	
        current_time = start_time + timedelta(seconds=i)
        
        # ����O	
        angle = (i / num_points) * 2 * np.pi
        radius = 0.01  # 1km�n�
        
        # Τ���H�
        noise_factor = noise_level * np.random.random()
        
        lat = start_lat + radius * np.sin(angle) + (noise_factor * 0.001 * np.random.randn())
        lon = start_lon + radius * np.cos(angle) + (noise_factor * 0.001 * np.random.randn())
        
        # �
�n!��	Ւ��	
        base_speed = 5.0 + 2.0 * np.sin(angle * 2)  # �	�37���	
        speed = base_speed + (noise_factor * 0.5 * np.random.randn())  # Τ���
        
        # ���2L�	- �h
���Y�4n�ڹ90�Z�Y	
        base_course = (np.degrees(angle) + 90) % 360
        course = base_course + (noise_factor * 5 * np.random.randn())  # Τ���
        course = course % 360  # 0-360n��kc�
        
        timestamps.append(current_time)
        latitudes.append(lat)
        longitudes.append(lon)
        speeds.append(max(0.1, speed))  # �n��2b
        courses.append(course)
    
    # �ï/���ݤ�Ȓ��20�@	
    tack_indices = np.linspace(0, num_points-1, 20, dtype=int)
    for idx in tack_indices:
        if idx > 0 and idx < num_points - 1:
            # ����%�k	H�90�	
            course_change = 90 if np.random.random() > 0.5 else -90
            courses[idx] = (courses[idx-1] + course_change) % 360
            # �ï-o�L=a��
            speeds[idx] = speeds[idx] * 0.7
    
    # DataFramek	�
    df = pd.DataFrame({
        'timestamp': timestamps,
        'latitude': latitudes,
        'longitude': longitudes,
        'speed': speeds,
        'course': courses,
        'boat_id': 'test_boat'
    })
    
    return df

def benchmark_wind_estimation(df, boat_types=None, iterations=3):
    """����n�թ���������"""
    if boat_types is None:
        boat_types = ['default', 'laser', '49er', '470']
    
    print(f"\n--- ��������n������ ({len(df)}ݤ��) ---")
    
    # P��<
Y���
    results = {
        'size': len(df),
        'iterations': iterations,
        'by_boat_type': {}
    }
    
    total_times = []
    total_memory = []
    
    for boat_type in boat_types:
        print(f"\n## G.: {boat_type}")
        
        type_times = []
        type_memory = []
        
        for i in range(iterations):
            print(f"������� {i+1}/{iterations}")
            
            # ���(ϒ
            gc.collect()
            initial_memory = get_memory_usage()
            
            # WindEstimator���\h���
            start_time = time.time()
            estimator = WindEstimator(boat_type=boat_type)
            wind_data = estimator.estimate_wind_from_single_boat(
                gps_data=df,
                min_tack_angle=30.0,
                boat_type=boat_type,
                use_bayesian=True
            )
            end_time = time.time()
            
            # LNB��2
            elapsed = end_time - start_time
            type_times.append(elapsed)
            print(f"  �B�: {elapsed:.3f}�")
            
            # ���(ϒ2
            current_memory = get_memory_usage()
            memory_increase = current_memory - initial_memory
            type_memory.append(memory_increase)
            print(f"  ��ꗠ�: {memory_increase:.2f}MB")
            
            # P�nq�1��
            if wind_data is not None:
                print(f"  ��P�: {len(wind_data)}L, �<�: {estimator.estimated_wind['confidence']:.2f}")
            
            # ����>
            del estimator
            del wind_data
            gc.collect()
        
        # G.ThnP���X
        results['by_boat_type'][boat_type] = {
            'avg_time': sum(type_times) / len(type_times),
            'min_time': min(type_times),
            'max_time': max(type_times),
            'avg_memory': sum(type_memory) / len(type_memory)
        }
        
        # hSn�(
        total_times.extend(type_times)
        total_memory.extend(type_memory)
        
        print(f"sG�B� ({boat_type}): {results['by_boat_type'][boat_type]['avg_time']:.3f}�")
    
    # hSnsG
    results['overall'] = {
        'avg_time': sum(total_times) / len(total_times),
        'avg_memory': sum(total_memory) / len(total_memory)
    }
    
    print(f"\nhSsG�B�: {results['overall']['avg_time']:.3f}�")
    print(f"hSsG��ꗠ�: {results['overall']['avg_memory']:.2f}MB")
    
    return results

def benchmark_wind_field_fusion(df, grid_sizes=None, iterations=3):
    """�n4n�թ���������"""
    if grid_sizes is None:
        grid_sizes = [10, 20, 30]
    
    print(f"\n--- �n4����n������ ({len(df)}ݤ��) ---")
    
    # P��<
Y���
    results = {
        'size': len(df),
        'iterations': iterations,
        'by_grid_size': {}
    }
    
    # SailingDataProcessor�(Wf�����L
    processor = SailingDataProcessor()
    processor.boat_data['test_boat'] = df.copy()
    wind_estimates = processor.estimate_wind_from_boat('test_boat')
    
    if wind_estimates is None:
        print("���k1WW~W_�n4�����������W~Y")
        return None
    
    for grid_size in grid_sizes:
        print(f"\n## ���ɵ��: {grid_size}x{grid_size}")
        
        times = []
        memory = []
        
        for i in range(iterations):
            print(f"������� {i+1}/{iterations}")
            
            # ���(ϒ
            gc.collect()
            initial_memory = get_memory_usage()
            
            # �n4
            start_time = time.time()
            wind_field = processor.estimate_wind_field(
                time_point=df['timestamp'].iloc[len(df)//2],  # -�B��(
                grid_resolution=grid_size
            )
            end_time = time.time()
            
            # LNB��2
            elapsed = end_time - start_time
            times.append(elapsed)
            print(f"  �B�: {elapsed:.3f}�")
            
            # ���(ϒ2
            current_memory = get_memory_usage()
            memory_increase = current_memory - initial_memory
            memory.append(memory_increase)
            print(f"  ��ꗠ�: {memory_increase:.2f}MB")
            
            # P��1
            if wind_field is not None:
                print(f"  P�: ����b� {wind_field['lat_grid'].shape}")
            
            # 
�j�ָ��Ȓ�>
            del wind_field
            gc.collect()
        
        # ���ɵ��ThnP���X
        results['by_grid_size'][str(grid_size)] = {
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'avg_memory': sum(memory) / len(memory)
        }
        
        print(f"sG�B� (���� {grid_size}x{grid_size}): {results['by_grid_size'][str(grid_size)]['avg_time']:.3f}�")
    
    # ����>
    del processor
    gc.collect()
    
    return results

def benchmark_with_different_sizes(size_multipliers=(0.2, 0.5, 1.0, 2.0), base_size=5000):
    """pj�������gn������"""
    print("\n--- pj�������gn������ ---")
    
    results = []
    
    for multiplier in size_multipliers:
        size = int(base_size * multiplier)
        print(f"\n=== ������: {size} ݤ�� ===")
        
        # �������
        sample_data = generate_sample_data(num_points=size)
        
        # ���������
        result = benchmark_wind_estimation(sample_data, boat_types=['default'], iterations=2)
        
        # P����
        results.append({
            'size': size,
            'time': result['by_boat_type']['default']['avg_time'],
            'memory': result['by_boat_type']['default']['avg_memory']
        })
        
        # ������
        del sample_data
        gc.collect()
    
    return results

def plot_benchmark_results(size_results, output_file=None):
    """pj����gn������P����"""
    plt.figure(figsize=(12, 5))
    
    # ���ݤ��ph�B�n����
    plt.subplot(1, 2, 1)
    sizes = [r['size'] for r in size_results]
    times = [r['time'] for r in size_results]
    
    plt.plot(sizes, times, 'o-', color='blue')
    plt.xlabel('Data Points')
    plt.ylabel('Processing Time (seconds)')
    plt.title('Wind Estimation Time vs. Data Size')
    plt.grid(True)
    
    # ���ݤ��ph���(�n����
    plt.subplot(1, 2, 2)
    memory = [r['memory'] for r in size_results]
    
    plt.plot(sizes, memory, 'o-', color='green')
    plt.xlabel('Data Points')
    plt.ylabel('Memory Usage (MB)')
    plt.title('Memory Usage vs. Data Size')
    plt.grid(True)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file)
        print(f"��������Ւ�XW~W_: {output_file}")
    
    plt.close()

def save_benchmark_results(results, output_file):
    """������P��JSONա��k�X"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\n������P���XW~W_: {output_file}")

def main():
    """��L�p"""
    parser = argparse.ArgumentParser(description='����n�թ���������')
    parser.add_argument('--output', default='benchmark_results/wind_estimation_benchmark.json',
                      help='P�n��HJSONա��')
    parser.add_argument('--points', type=int, default=5000, help='ƹ����ݤ��p')
    parser.add_argument('--iterations', type=int, default=3, help='p��W�p')
    parser.add_argument('--size-test', action='store_true', 
                      help='pj�������gnƹȒ�L')
    parser.add_argument('--field-fusion', action='store_true',
                      help='�n4n��������L')
    
    args = parser.parse_args()
    
    print("==================================================")
    print("   ���� - �թ���������   ")
    print("==================================================")
    print(f"�LB�: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"�,���ݤ��p: {args.points}")
    print(f"p��W�p: {args.iterations}")
    
    # ��ǣ���n��
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # P��<
Y�ǣ�����
    final_results = {
        'timestamp': datetime.now().isoformat(),
        'data_points': args.points,
        'iterations': args.iterations
    }
    
    # �������
    sample_data = generate_sample_data(num_points=args.points)
    
    # ���n������
    wind_results = benchmark_wind_estimation(sample_data, iterations=args.iterations)
    final_results['wind_estimation'] = wind_results
    
    # �n4n�������׷��	
    if args.field_fusion:
        fusion_results = benchmark_wind_field_fusion(sample_data, iterations=args.iterations)
        if fusion_results:
            final_results['wind_field_fusion'] = fusion_results
    
    # ���%�������׷��	
    if args.size_test:
        print("\n--- ������%�������L ---")
        size_results = benchmark_with_different_sizes(base_size=args.points)
        final_results['size_benchmark'] = size_results
        
        # ���n
        graph_file = os.path.splitext(args.output)[0] + '.png'
        plot_benchmark_results(size_results, graph_file)
    
    # P�n�X
    save_benchmark_results(final_results, args.output)
    
    print("\n--- ������P����� ---")
    print(f"���� ({args.points}ݤ��):")
    print(f"  sG�B�: {wind_results['overall']['avg_time']:.3f}�")
    print(f"  sG���(�: {wind_results['overall']['avg_memory']:.2f}MB")
    
    if args.field_fusion and 'wind_field_fusion' in final_results:
        fusion_result = final_results['wind_field_fusion']['by_grid_size']['20']  # ��j���ɵ��nP�
        print(f"\n�n4 (���� 20x20):")
        print(f"  sG�B�: {fusion_result['avg_time']:.3f}�")
        print(f"  sG���(�: {fusion_result['avg_memory']:.2f}MB")
    
    print("\n==================================================")
    print("   ��������")
    print("==================================================")

if __name__ == "__main__":
    main()
