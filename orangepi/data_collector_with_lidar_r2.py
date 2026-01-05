#!/usr/bin/env python3
"""
Synchronized Ultrasonic Echo Profiling + RPLIDAR 2D Positioning (Direct Control Version)

Uses direct serial control for RPLIDAR (bypassing rplidar library) for better reliability.

Creates ML training dataset with:
- Features: 240-point echo profiles from ultrasonic sensors
- Labels: (x, y) position ground truth from RPLIDAR

Position data captures only objects in front of the box (nearest to front line)
with coordinates relative to the front edge (Y=0 at front line).

Usage:
    python data_collector_with_lidar_r2.py
    python data_collector_with_lidar_r2.py --duration 120
    python data_collector_with_lidar_r2.py --config custom_config.yaml
"""

import serial
import time
import csv
import yaml
import argparse
from datetime import datetime
from pathlib import Path
import numpy as np
from collections import deque
import threading
import queue
import sys
import struct
import glob
import os


class SynchronizedDataCollector:
    """Collect synchronized ultrasonic echo profiles and RPLIDAR 2D positions using direct control."""
    
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
        
        # Read and discard startup messages
        time.sleep(0.5)
        while self.arduino.in_waiting:
            line = self.arduino.readline().decode('utf-8').strip()
            print(f"  Arduino: {line}")
        
        # Send START command to begin data collection
        print("Sending START command to Arduino...")
        self.arduino.write(b"START:10\n")
        self.arduino.flush()
        time.sleep(0.5)
        
        # Read acknowledgment
        if self.arduino.in_waiting:
            ack = self.arduino.readline().decode('utf-8').strip()
            print(f"  Arduino response: {ack}")
        
        print(f"✓ Arduino connected on {self.config['arduino']['port']}")
        
        # Initialize RPLIDAR with direct serial control
        print("Connecting to RPLIDAR...")
        self.lidar_serial = serial.Serial(
            self.config['lidar']['port'],
            115200,  # RPLIDAR A1M8 standard baudrate
            timeout=1,
            dsrdtr=True
        )
        time.sleep(0.5)
        self._init_lidar()
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
    
    def _init_lidar(self):
        """Initialize RPLIDAR with direct serial commands."""
        # Clear buffers
        self.lidar_serial.reset_input_buffer()
        self.lidar_serial.reset_output_buffer()
        time.sleep(0.5)
        
        # Test communication with GET_INFO
        print("  Testing LIDAR communication...")
        self.lidar_serial.write(b'\xA5\x50')
        time.sleep(0.2)
        descriptor = self.lidar_serial.read(7)
        if len(descriptor) == 7:
            data_len = struct.unpack('<I', descriptor[2:6])[0] & 0x3FFFFFFF
            info_data = self.lidar_serial.read(data_len)
            if len(info_data) >= 20:
                model = info_data[0]
                firmware_minor = info_data[1]
                firmware_major = info_data[2]
                hardware = info_data[3]
                print(f"  ✓ LIDAR: Model={model}, Firmware={firmware_major}.{firmware_minor}, Hardware={hardware}")
            else:
                print("  ✓ LIDAR communication OK")
        else:
            raise Exception("Failed to communicate with LIDAR")
        
        # Send STOP to ensure clean state
        print("  Sending STOP command...")
        self.lidar_serial.write(b'\xA5\x25')
        time.sleep(0.5)
        self.lidar_serial.reset_input_buffer()
        
        # Start motor using DTR (DTR=False makes motor spin on A1M8)
        print("  Starting motor...")
        self.lidar_serial.setDTR(False)  # False makes motor spin on RPLidar A1M8
        time.sleep(3)  # Wait for motor to stabilize
        print("  ✓ Motor ready")
        
        # Clear any startup data
        self.lidar_serial.reset_input_buffer()
        time.sleep(0.2)
    
    def _start_lidar_scan(self):
        """Start LIDAR scan using direct serial commands."""
        print("  Starting LIDAR scan...")
        self.lidar_serial.write(b'\xA5\x20')
        self.lidar_serial.flush()
        time.sleep(0.3)
        
        # Read and verify descriptor
        descriptor = self.lidar_serial.read(7)
        if len(descriptor) != 7:
            raise Exception(f"Scan descriptor incomplete: {len(descriptor)} bytes")
        
        if descriptor[0:2] != b'\xA5\x5A':
            raise Exception(f"Invalid scan descriptor: {descriptor.hex()}")
        
        length_val = struct.unpack('<I', descriptor[2:6])[0]
        response_len = length_val & 0x3FFFFFFF
        
        if response_len != 5:
            raise Exception(f"Unexpected scan response length: {response_len}")
        
        print("  ✓ LIDAR scan active!")
    
    def _stop_lidar(self):
        """Stop LIDAR and motor."""
        try:
            # Stop scan
            self.lidar_serial.write(b'\xA5\x25')
            time.sleep(0.2)
            
            # Stop motor
            self.lidar_serial.setDTR(False)
            self.lidar_serial.setRTS(False)
            time.sleep(0.2)
            
            self.lidar_serial.close()
            print("✓ RPLIDAR stopped")
        except Exception as e:
            print(f"Error stopping LIDAR: {e}")
    
    def collect_ultrasonic_data(self):
        """Thread: Collect ultrasonic echo profile data with timestamps."""
        print("Starting ultrasonic data collection thread...")
        
        debug_count = 0
        max_debug = 10
        
        while self.running:
            try:
                if self.arduino.in_waiting:
                    line = self.arduino.readline().decode('utf-8').strip()
                    
                    # Debug: show first few lines
                    if debug_count < max_debug:
                        print(f"[DEBUG] Arduino: {line[:100] if len(line) > 100 else line}")
                        debug_count += 1
                    
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
                            
                            if debug_count < max_debug:
                                print(f"[DEBUG] Valid sample received: {len(parts)} parts")
                        else:
                            if debug_count < max_debug:
                                print(f"[DEBUG] Invalid format: {len(parts)} parts (expected 243+)")
                    else:
                        if debug_count < max_debug and line:
                            print(f"[DEBUG] Non-data line: '{line[:50]}'")
                else:
                    time.sleep(0.01)  # Small delay when no data
                            
            except Exception as e:
                if self.running:
                    print(f"Ultrasonic error: {e}")
                    
        print("Ultrasonic collection thread stopped")
    
    def collect_lidar_data(self):
        """Thread: Collect RPLIDAR 2D scan data with timestamps using direct serial."""
        print("Starting RPLIDAR data collection thread...")
        
        try:
            # Start scanning
            self._start_lidar_scan()
            
            current_scan = []
            
            while self.running:
                try:
                    # Read one measurement (5 bytes)
                    data = self.lidar_serial.read(5)
                    
                    if len(data) != 5:
                        continue
                    
                    # Parse measurement
                    byte0 = data[0]
                    start_flag = (byte0 & 0x01) != 0
                    quality = (byte0 >> 2) & 0x3F
                    
                    angle_raw = struct.unpack('<H', data[1:3])[0]
                    angle = (angle_raw >> 1) / 64.0
                    
                    distance_raw = struct.unpack('<H', data[3:5])[0]
                    distance = distance_raw / 4.0  # mm
                    
                    if start_flag and len(current_scan) > 0:
                        # Complete scan collected
                        timestamp = time.time()
                        
                        # Convert scan to (x, y) positions
                        positions = self._process_lidar_scan(current_scan)
                        
                        if len(positions) > 0:
                            self.lidar_queue.put({
                                'timestamp': timestamp,
                                'positions': positions,
                                'num_points': len(current_scan)
                            })
                            self.stats['lidar_scans'] += 1
                        
                        current_scan = []
                    
                    current_scan.append((quality, angle, distance))
                    
                except Exception as e:
                    if self.running:
                        print(f"LIDAR read error: {e}")
                        
        except Exception as e:
            if self.running:
                print(f"LIDAR error: {e}")
                import traceback
                traceback.print_exc()
                
        print("LIDAR collection thread stopped")
    
    def _process_lidar_scan(self, scan):
        """
        Convert RPLIDAR scan to (x, y) coordinates, filtering for objects in front of box.
        Returns coordinates relative to front line (Y=0 at front line).
        
        Args:
            scan: RPLIDAR scan data [(quality, angle, distance), ...]
            
        Returns:
            List of (x, y, quality, distance) tuples in cm, relative to front line
        """
        # Get front line Y position from config (distance from RPLIDAR to front edge)
        front_line_y = self.config['sensor_positions']['front_line_y']
        
        positions = []
        for quality, angle, distance in scan:
            if quality > 0 and distance > 0:
                # Convert polar to cartesian (RPLIDAR-centered coordinates)
                angle_rad = np.radians(angle)
                x_rplidar = (distance / 10) * np.cos(angle_rad)  # mm to cm
                y_rplidar = (distance / 10) * np.sin(angle_rad)
                
                # Only include points in front of the box (Y > front_line_y)
                if y_rplidar > front_line_y:
                    # Transform to front-line-relative coordinates
                    # X stays the same, Y becomes distance from front line
                    x = x_rplidar
                    y = y_rplidar - front_line_y  # Distance in front of the line
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
        Find the nearest LIDAR point to the front line (minimum Y value).
        
        Since positions are already filtered to objects in front and coordinates
        are relative to the front line, we simply find the point with minimum Y.
        
        Args:
            sensor_id: Sensor ID (1, 2, ...) - not used in this simplified version
            positions: List of (x, y, quality, distance) tuples (front-line relative)
            
        Returns:
            (x, y, quality, distance) of nearest point to front line, or None
        """
        if not positions:
            return None
        
        # Return point with minimum Y (nearest to front line)
        nearest = min(positions, key=lambda p: p[1])  # p[1] is Y coordinate
        return nearest
    
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
        print(f"Starting synchronized data collection (Direct Control)")
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
        
        # Send STOP command to Arduino
        try:
            self.arduino.write(b"STOP\n")
            self.arduino.flush()
            time.sleep(0.2)
        except:
            pass
        
        # Wait for threads to finish
        if self.ultrasonic_thread:
            self.ultrasonic_thread.join(timeout=2)
        if self.lidar_thread:
            self.lidar_thread.join(timeout=2)
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        
        # Cleanup hardware
        self._stop_lidar()
        
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


def verify_ports(config):
    """Verify that configured ports exist and are accessible."""
    print("\n=== Port Verification ===")
    
    # Check Arduino port
    arduino_port = config['arduino']['port']
    print(f"Arduino port: {arduino_port}")
    if os.path.exists(arduino_port):
        if os.access(arduino_port, os.R_OK | os.W_OK):
            print("  ✓ Port exists and is accessible")
        else:
            print("  ✗ Port exists but no read/write permission")
            print(f"  Fix: sudo usermod -a -G dialout $USER (then logout/login)")
            print(f"  Or: sudo chmod 666 {arduino_port}")
            return False
    else:
        print(f"  ✗ Port does not exist")
        print(f"  Available ports: {', '.join(glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*'))}")
        return False
    
    # Check LIDAR port
    lidar_port = config['lidar']['port']
    print(f"\nLiDAR port: {lidar_port}")
    if os.path.exists(lidar_port):
        if os.access(lidar_port, os.R_OK | os.W_OK):
            print("  ✓ Port exists and is accessible")
        else:
            print("  ✗ Port exists but no read/write permission")
            print(f"  Fix: sudo usermod -a -G dialout $USER (then logout/login)")
            print(f"  Or: sudo chmod 666 {lidar_port}")
            return False
    else:
        print(f"  ✗ Port does not exist")
        print(f"  Available ports: {', '.join(glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*'))}")
        return False
    
    print("=" * 60)
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Synchronized ultrasonic echo profiling + RPLIDAR positioning (Direct Control)'
    )
    parser.add_argument('-c', '--config', default='../config.yaml',
                       help='Path to configuration file')
    parser.add_argument('-d', '--duration', type=int, default=60,
                       help='Collection duration in seconds (0 for infinite, default: 60)')
    parser.add_argument('--skip-port-check', action='store_true',
                       help='Skip port verification (not recommended)')
    
    args = parser.parse_args()
    
    try:
        # Load config first
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
        
        # Verify ports unless skipped
        if not args.skip_port_check:
            if not verify_ports(config):
                print("\n✗ Port verification failed. Fix port issues and try again.")
                print("Or run with --skip-port-check to bypass this check.")
                sys.exit(1)
        
        collector = SynchronizedDataCollector(args.config)
        collector.start_collection(duration=args.duration)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check USB connections (Arduino and RPLidar)")
        print("2. Verify ports: ls /dev/ttyUSB* /dev/ttyACM*")
        print("3. Check permissions: ls -l /dev/ttyUSB0 /dev/ttyACM0")
        print("4. Add to dialout group: sudo usermod -a -G dialout $USER")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
