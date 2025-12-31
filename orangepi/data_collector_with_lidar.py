#!/usr/bin/env python3
"""
Synchronized Ultrasonic Echo Profiling + RPLIDAR 2D Positioning

Creates ML training dataset with:
- Features: 240-point echo profiles from ultrasonic sensors
- Labels: (x, y) position ground truth from RPLIDAR

Usage:
    python data_collector_with_lidar.py
    python data_collector_with_lidar.py --duration 120
    python data_collector_with_lidar.py --config custom_config.yaml
"""

import serial
import time
import csv
import yaml
import argparse
from datetime import datetime
from pathlib import Path
from rplidar import RPLidar
import numpy as np
from collections import deque
import threading
import queue
import sys


class SynchronizedDataCollector:
    """Collect synchronized ultrasonic echo profiles and RPLIDAR 2D positions."""
    
    def __init__(self, config_path='../config.yaml'):
        """Initialize collector with configuration."""
        self.config = self._load_config(config_path)
        
        # Initialize Arduino (ultrasonics)
        print("Connecting to Arduino...")
        self.arduino = serial.Serial(
            self.config['arduino']['port'],
            self.config['arduino']['baudrate'],
            timeout=self.config['arduino']['timeout']
        )
        time.sleep(2)  # Wait for Arduino reset
        print(f"✓ Arduino connected on {self.config['arduino']['port']}")
        
        # Initialize RPLIDAR
        print("Connecting to RPLIDAR...")
        self.lidar = RPLidar(self.config['lidar']['port'])
        self.lidar.stop()
        self.lidar.start_motor()
        time.sleep(1)
        print(f"✓ RPLIDAR connected on {self.config['lidar']['port']}")
        
        # Synchronized data queues
        self.ultrasonic_queue = queue.Queue(maxsize=200)
        self.lidar_queue = queue.Queue(maxsize=200)
        
        # Sync parameters
        self.sync_window_ms = self.config['sync']['window_ms']
        
        # Control flags
        self.running = False
        self.ultrasonic_thread = None
        self.lidar_thread = None
        self.sync_thread = None
        
        # Statistics
        self.stats = {
            'ultrasonic_samples': 0,
            'lidar_scans': 0,
            'matched_samples': 0,
            'unmatched_ultrasonic': 0,
            'unmatched_lidar': 0
        }
        
        # Output file
        self.output_file = None
        self.csv_writer = None
        
    def _load_config(self, config_path):
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def collect_ultrasonic_data(self):
        """Thread: Collect ultrasonic echo profile data with timestamps."""
        print("Starting ultrasonic data collection thread...")
        
        while self.running:
            try:
                if self.arduino.in_waiting:
                    line = self.arduino.readline().decode('utf-8').strip()
                    
                    if line.startswith('S,'):
                        timestamp = time.time()
                        
                        # Parse ultrasonic data
                        parts = line.split(',')
                        if len(parts) >= 243:  # S, timestamp, 240 readings, sensor_id
                            self.ultrasonic_queue.put({
                                'timestamp': timestamp,
                                'raw_line': line,
                                'parts': parts
                            })
                            self.stats['ultrasonic_samples'] += 1
                            
            except Exception as e:
                if self.running:
                    print(f"Ultrasonic error: {e}")
                    
        print("Ultrasonic collection thread stopped")
    
    def collect_lidar_data(self):
        """Thread: Collect RPLIDAR 2D scan data with timestamps."""
        print("Starting RPLIDAR data collection thread...")
        
        try:
            for scan in self.lidar.iter_scans():
                if not self.running:
                    break
                
                timestamp = time.time()
                
                # Convert scan to (x, y) positions
                positions = self._process_lidar_scan(scan)
                
                if len(positions) > 0:
                    self.lidar_queue.put({
                        'timestamp': timestamp,
                        'positions': positions,
                        'num_points': len(scan)
                    })
                    self.stats['lidar_scans'] += 1
                    
        except Exception as e:
            if self.running:
                print(f"LIDAR error: {e}")
                
        print("LIDAR collection thread stopped")
    
    def _process_lidar_scan(self, scan):
        """
        Convert RPLIDAR scan to (x, y) coordinates.
        
        Args:
            scan: RPLIDAR scan data [(quality, angle, distance), ...]
            
        Returns:
            List of (x, y, quality, distance) tuples in cm
        """
        positions = []
        for quality, angle, distance in scan:
            if quality > 0 and distance > 0:
                # Convert polar to cartesian
                angle_rad = np.radians(angle)
                x = (distance / 10) * np.cos(angle_rad)  # mm to cm
                y = (distance / 10) * np.sin(angle_rad)
                positions.append((x, y, quality, distance / 10))
        return positions
    
    def synchronize_and_save(self):
        """Match ultrasonic and LIDAR data by timestamp and save to CSV."""
        print("Starting synchronization thread...")
        
        ultrasonic_buffer = deque(maxlen=self.config['sync']['buffer_size'])
        lidar_buffer = deque(maxlen=self.config['sync']['buffer_size'])
        
        last_report_time = time.time()
        
        while self.running or not self.ultrasonic_queue.empty() or not self.lidar_queue.empty():
            # Get data from queues
            try:
                us_data = self.ultrasonic_queue.get(timeout=0.1)
                ultrasonic_buffer.append(us_data)
            except queue.Empty:
                pass
            
            try:
                lidar_data = self.lidar_queue.get(timeout=0.1)
                lidar_buffer.append(lidar_data)
            except queue.Empty:
                pass
            
            # Try to match timestamps
            matched_pairs = []
            for us in list(ultrasonic_buffer):
                best_match = None
                best_time_diff = float('inf')
                
                for lidar in list(lidar_buffer):
                    time_diff = abs(us['timestamp'] - lidar['timestamp'])
                    
                    if time_diff < self.sync_window_ms / 1000 and time_diff < best_time_diff:
                        best_time_diff = time_diff
                        best_match = lidar
                
                if best_match:
                    matched_pairs.append((us, best_match))
                    ultrasonic_buffer.remove(us)
                    lidar_buffer.remove(best_match)
            
            # Save matched data
            for us, lidar in matched_pairs:
                self._save_training_sample(us, lidar)
                self.stats['matched_samples'] += 1
            
            # Periodic progress report
            if time.time() - last_report_time > 5.0:
                self._print_progress()
                last_report_time = time.time()
        
        # Final cleanup
        self.stats['unmatched_ultrasonic'] = len(ultrasonic_buffer)
        self.stats['unmatched_lidar'] = len(lidar_buffer)
        
        print("Synchronization thread stopped")
    
    def _save_training_sample(self, ultrasonic, lidar):
        """
        Save one synchronized training sample to CSV.
        
        Args:
            ultrasonic: Dict with ultrasonic echo profile data
            lidar: Dict with RPLIDAR position data
        """
        # Parse ultrasonic data: S,timestamp,r1,r2,...,r240
        parts = ultrasonic['parts']
        arduino_timestamp = int(parts[1])
        
        # Extract echo readings (parts[2] through parts[241] = 240 readings)
        echo_readings = [int(parts[i]) for i in range(2, 242)]
        
        # Determine sensor ID (current Arduino code cycles through sensors)
        # For now, we'll track by counting rows - alternates 1,2,1,2...
        sensor_id = (self.stats['matched_samples'] % self.config['sensors']['count']) + 1
        
        # Get closest object from LIDAR
        positions = lidar['positions']
        if positions:
            # Find object in sensor's field of view
            closest_obj = self._find_relevant_object(sensor_id, positions)
        else:
            closest_obj = None
        
        # Write CSV row
        if self.csv_writer:
            row = [
                ultrasonic['timestamp'],  # system_timestamp
                arduino_timestamp,         # arduino_timestamp_ms
                sensor_id,                 # sensor_id
            ]
            row.extend(echo_readings)  # 240 echo values
            
            # Add LIDAR ground truth
            if closest_obj:
                row.extend([
                    closest_obj[0],  # lidar_x
                    closest_obj[1],  # lidar_y
                    closest_obj[2],  # lidar_quality
                    closest_obj[3],  # lidar_distance
                ])
            else:
                row.extend([None, None, None, None])
            
            row.append(len(positions))  # num_lidar_objects
            
            self.csv_writer.writerow(row)
            self.output_file.flush()  # Ensure data is written
    
    def _find_relevant_object(self, sensor_id, positions):
        """
        Find LIDAR object in sensor's field of view.
        
        Args:
            sensor_id: Sensor ID (1, 2, ...)
            positions: List of (x, y, quality, distance) tuples
            
        Returns:
            (x, y, quality, distance) of closest object in FOV, or None
        """
        # Get sensor configuration
        sensor_key = f'sensor_{sensor_id}'
        if sensor_key not in self.config['sensor_positions']:
            # Default to first detected object
            return min(positions, key=lambda p: p[3]) if positions else None
        
        sensor_config = self.config['sensor_positions'][sensor_key]
        sensor_x = sensor_config['x']
        sensor_y = sensor_config['y']
        sensor_angle = sensor_config['angle']  # degrees
        fov = sensor_config['fov']  # field of view (degrees)
        
        candidates = []
        for x, y, quality, distance in positions:
            # Calculate angle from sensor to object
            dx = x - sensor_x
            dy = y - sensor_y
            angle = np.degrees(np.arctan2(dy, dx))
            
            # Normalize angle difference
            angle_diff = abs((angle - sensor_angle + 180) % 360 - 180)
            
            # Check if in sensor's FOV
            if angle_diff <= fov / 2:
                obj_distance = np.sqrt(dx**2 + dy**2)
                candidates.append((x, y, quality, obj_distance))
        
        # Return closest object in FOV
        if candidates:
            closest = min(candidates, key=lambda c: c[3])
            return closest
        
        return None
    
    def _print_progress(self):
        """Print collection progress statistics."""
        print(f"\n{'='*60}")
        print(f"Collection Progress:")
        print(f"  Ultrasonic samples: {self.stats['ultrasonic_samples']}")
        print(f"  LIDAR scans: {self.stats['lidar_scans']}")
        print(f"  Matched samples: {self.stats['matched_samples']}")
        print(f"  Queue sizes: US={self.ultrasonic_queue.qsize()}, LIDAR={self.lidar_queue.qsize()}")
        if self.stats['ultrasonic_samples'] > 0:
            match_rate = 100 * self.stats['matched_samples'] / self.stats['ultrasonic_samples']
            print(f"  Match rate: {match_rate:.1f}%")
        print(f"{'='*60}")
    
    def _create_output_file(self):
        """Create CSV output file with headers."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'training_data_{timestamp}.csv'
        
        output_dir = Path(self.config['data']['output_directory'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = output_dir / filename
        
        self.output_file = open(filepath, 'w', newline='')
        self.csv_writer = csv.writer(self.output_file)
        
        # Write header
        header = ['system_timestamp', 'arduino_timestamp_ms', 'sensor_id']
        header += [f'echo_r{i}' for i in range(1, 241)]
        header += ['lidar_x', 'lidar_y', 'lidar_quality', 'lidar_distance', 'num_objects']
        self.csv_writer.writerow(header)
        
        print(f"✓ Created output file: {filepath}")
        return filepath
    
    def start_collection(self, duration=60):
        """
        Start synchronized data collection.
        
        Args:
            duration: Collection duration in seconds (0 for infinite)
        """
        print(f"\n{'='*60}")
        print(f"Starting synchronized data collection")
        print(f"Duration: {duration}s" if duration > 0 else "Duration: Infinite (Ctrl+C to stop)")
        print(f"Sync window: {self.sync_window_ms}ms")
        print(f"{'='*60}\n")
        
        # Create output file
        output_path = self._create_output_file()
        
        self.running = True
        
        # Start collection threads
        self.ultrasonic_thread = threading.Thread(target=self.collect_ultrasonic_data, daemon=True)
        self.lidar_thread = threading.Thread(target=self.collect_lidar_data, daemon=True)
        self.sync_thread = threading.Thread(target=self.synchronize_and_save, daemon=True)
        
        self.ultrasonic_thread.start()
        self.lidar_thread.start()
        self.sync_thread.start()
        
        # Wait for specified duration or until interrupted
        try:
            if duration > 0:
                time.sleep(duration)
            else:
                # Infinite collection
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nStopping collection (Ctrl+C pressed)...")
        
        # Stop collection
        self.stop_collection()
        
        # Print final statistics
        print(f"\n{'='*60}")
        print("FINAL STATISTICS:")
        print(f"  Total ultrasonic samples: {self.stats['ultrasonic_samples']}")
        print(f"  Total LIDAR scans: {self.stats['lidar_scans']}")
        print(f"  Matched training samples: {self.stats['matched_samples']}")
        print(f"  Unmatched ultrasonic: {self.stats['unmatched_ultrasonic']}")
        print(f"  Unmatched LIDAR: {self.stats['unmatched_lidar']}")
        if self.stats['ultrasonic_samples'] > 0:
            match_rate = 100 * self.stats['matched_samples'] / self.stats['ultrasonic_samples']
            print(f"  Overall match rate: {match_rate:.1f}%")
        print(f"  Output file: {output_path}")
        print(f"{'='*60}\n")
    
    def stop_collection(self):
        """Stop all collection threads and cleanup."""
        print("Stopping collection threads...")
        self.running = False
        
        # Wait for threads to finish
        if self.ultrasonic_thread:
            self.ultrasonic_thread.join(timeout=2)
        if self.lidar_thread:
            self.lidar_thread.join(timeout=2)
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        
        # Cleanup hardware
        try:
            self.lidar.stop()
            self.lidar.stop_motor()
            self.lidar.disconnect()
            print("✓ RPLIDAR stopped")
        except:
            pass
        
        try:
            self.arduino.close()
            print("✓ Arduino disconnected")
        except:
            pass
        
        # Close output file
        if self.output_file:
            self.output_file.close()
            print("✓ Output file closed")
        
        print("✓ Collection stopped")


def main():
    parser = argparse.ArgumentParser(
        description='Synchronized ultrasonic echo profiling + RPLIDAR positioning for ML training'
    )
    parser.add_argument('-c', '--config', default='../config.yaml',
                       help='Path to configuration file')
    parser.add_argument('-d', '--duration', type=int, default=60,
                       help='Collection duration in seconds (0 for infinite, default: 60)')
    
    args = parser.parse_args()
    
    try:
        collector = SynchronizedDataCollector(args.config)
        collector.start_collection(duration=args.duration)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
