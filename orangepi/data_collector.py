#!/usr/bin/env python3
"""
Ultrasonic Data Collector for Orange Pi 5

This script communicates with the Arduino to collect ultrasonic sensor data
and stores it as time series data.
"""

import serial
import time
import csv
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import threading
import queue


class UltrasonicDataCollector:
    """Manages data collection from Arduino-connected ultrasonic sensors."""
    
    def __init__(self, config_path: str = "../config.yaml"):
        """Initialize the data collector with configuration."""
        self.config = self._load_config(config_path)
        self.serial_conn: Optional[serial.Serial] = None
        self.is_running = False
        self.data_buffer = []
        self.data_queue = queue.Queue()
        
        # Create output directory if it doesn't exist
        output_dir = Path(self.config['data']['output_directory'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def connect(self) -> bool:
        """Establish serial connection with Arduino."""
        try:
            self.serial_conn = serial.Serial(
                port=self.config['arduino']['port'],
                baudrate=self.config['arduino']['baudrate'],
                timeout=self.config['arduino']['timeout']
            )
            
            # Wait for Arduino to initialize
            time.sleep(2)
            
            # Read initialization messages
            while self.serial_conn.in_waiting:
                line = self.serial_conn.readline().decode('utf-8').strip()
                print(f"Arduino: {line}")
                
            print("Connected to Arduino successfully")
            return True
            
        except serial.SerialException as e:
            print(f"Failed to connect to Arduino: {e}")
            return False
    
    def disconnect(self):
        """Close serial connection."""
        if self.serial_conn and self.serial_conn.is_open:
            self.send_command("STOP")
            self.serial_conn.close()
            print("Disconnected from Arduino")
    
    def send_command(self, command: str) -> Optional[str]:
        """Send command to Arduino and wait for acknowledgment."""
        if not self.serial_conn or not self.serial_conn.is_open:
            print("Error: Not connected to Arduino")
            return None
        
        self.serial_conn.write(f"{command}\n".encode('utf-8'))
        
        # Wait for response
        response = self.serial_conn.readline().decode('utf-8').strip()
        print(f"Arduino response: {response}")
        return response
    
    def start_collection(self, samples_per_trigger: Optional[int] = None):
        """Start data collection from sensors."""
        if samples_per_trigger is None:
            samples_per_trigger = self.config['sensors']['samples_per_trigger']
        
        response = self.send_command(f"START:{samples_per_trigger}")
        
        if response and "ACK:STARTED" in response:
            self.is_running = True
            
            # Start data reading thread
            self.read_thread = threading.Thread(target=self._read_data_loop, daemon=True)
            self.read_thread.start()
            
            # Start data writing thread
            self.write_thread = threading.Thread(target=self._write_data_loop, daemon=True)
            self.write_thread.start()
            
            print(f"Started data collection with {samples_per_trigger} samples per trigger")
            return True
        else:
            print("Failed to start data collection")
            return False
    
    def stop_collection(self):
        """Stop data collection."""
        self.is_running = False
        self.send_command("STOP")
        
        # Flush remaining data
        self._flush_buffer()
        
        print("Stopped data collection")
    
    def _read_data_loop(self):
        """Continuously read data from Arduino (runs in separate thread)."""
        while self.is_running:
            try:
                if self.serial_conn and self.serial_conn.in_waiting:
                    line = self.serial_conn.readline().decode('utf-8').strip()
                    
                    if line.startswith('S,'):
                        # Parse sensor data: S,timestamp,sensor1,sensor2,...
                        self._parse_sensor_data(line)
                    elif line:
                        # Print non-data messages
                        print(f"Arduino: {line}")
                        
            except Exception as e:
                print(f"Error reading data: {e}")
                
            time.sleep(0.01)  # Small delay to prevent CPU spinning
    
    def _parse_sensor_data(self, line: str):
        """Parse sensor data line and add to queue."""
        try:
            parts = line.split(',')
            if len(parts) < 3:
                return
            
            timestamp_ms = int(parts[1])
            all_values = [int(v) for v in parts[2:]]
            
            # Parse readings: sensor1_r1, sensor1_r2, ..., sensor2_r1, sensor2_r2, ...
            num_sensors = self.config['sensors']['count']
            readings_per_trigger = self.config['sensors'].get('readings_per_trigger', 10)
            
            # Reshape data into per-sensor readings
            sensor_readings = []
            for i in range(num_sensors):
                start_idx = i * readings_per_trigger
                end_idx = start_idx + readings_per_trigger
                sensor_readings.append(all_values[start_idx:end_idx])
            
            # Create data entry
            data_entry = {
                'system_timestamp': datetime.now().isoformat(),
                'arduino_timestamp_ms': timestamp_ms,
                'sensor_readings': sensor_readings  # List of lists: [[s1_r1, s1_r2, ...], [s2_r1, s2_r2, ...]]
            }
            
            self.data_queue.put(data_entry)
            
        except Exception as e:
            print(f"Error parsing sensor data: {e}")
    
    def _write_data_loop(self):
        """Continuously write data from queue to file (runs in separate thread)."""
        while self.is_running or not self.data_queue.empty():
            try:
                # Get data with timeout
                data_entry = self.data_queue.get(timeout=0.5)
                self.data_buffer.append(data_entry)
                
                # Write buffer if it reaches specified size
                if len(self.data_buffer) >= self.config['data']['buffer_size']:
                    self._flush_buffer()
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error writing data: {e}")
    
    def _flush_buffer(self):
        """Write buffered data to file."""
        if not self.data_buffer:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(self.config['data']['output_directory'])
        
        if self.config['data']['file_format'] == 'csv':
            self._write_csv(output_dir / f"sensor_data_{timestamp}.csv")
        else:
            self._write_json(output_dir / f"sensor_data_{timestamp}.json")
        
        print(f"Wrote {len(self.data_buffer)} records to file")
        self.data_buffer = []
    
    def _write_csv(self, filepath: Path):
        """Write data buffer to CSV file."""
        file_exists = filepath.exists()
        
        with open(filepath, 'a', newline='') as f:
            if not self.data_buffer:
                return
            
            # Determine number of sensors and readings from first entry
            num_sensors = len(self.data_buffer[0]['sensor_readings'])
            readings_per_trigger = len(self.data_buffer[0]['sensor_readings'][0])
            
            fieldnames = ['system_timestamp', 'arduino_timestamp_ms']
            for i in range(num_sensors):
                for j in range(readings_per_trigger):
                    fieldnames.append(f'sensor_{i+1}_reading_{j+1}')
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            for entry in self.data_buffer:
                row = {
                    'system_timestamp': entry['system_timestamp'],
                    'arduino_timestamp_ms': entry['arduino_timestamp_ms']
                }
                for i, sensor_data in enumerate(entry['sensor_readings']):
                    for j, reading in enumerate(sensor_data):
                        row[f'sensor_{i+1}_reading_{j+1}'] = reading
                
                writer.writerow(row)
    
    def _write_json(self, filepath: Path):
        """Write data buffer to JSON file."""
        existing_data = []
        
        if filepath.exists():
            with open(filepath, 'r') as f:
                existing_data = json.load(f)
        
        existing_data.extend(self.data_buffer)
        
        with open(filepath, 'w') as f:
            json.dump(existing_data, f, indent=2)
    
    @staticmethod
    def _adc_to_distance(adc_value: int) -> float:
        """
        Convert ADC value to distance in cm.
        
        MB1300 outputs (Vcc/1024) per cm
        For 5V: ~4.9mV/cm, which gives approximately 1 ADC unit per cm
        ADC value directly approximates distance in cm
        """
        return adc_value  # ADC value ≈ distance in cm for MB1300 at 5V
    
    def update_config(self, samples_per_trigger: int):
        """Update the number of samples per trigger."""
        response = self.send_command(f"CONFIG:{samples_per_trigger}")
        if response and "ACK:CONFIG_UPDATED" in response:
            self.config['sensors']['samples_per_trigger'] = samples_per_trigger
            print(f"Updated samples per trigger to {samples_per_trigger}")
            return True
        return False


def main():
    """Main entry point for data collection."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ultrasonic Data Collector')
    parser.add_argument('-c', '--config', default='../config.yaml',
                      help='Path to configuration file')
    parser.add_argument('-s', '--samples', type=int,
                      help='Number of samples per trigger (overrides config)')
    parser.add_argument('-d', '--duration', type=int,
                      help='Collection duration in seconds (0 for infinite)')
    
    args = parser.parse_args()
    
    # Create collector
    collector = UltrasonicDataCollector(args.config)
    
    # Connect to Arduino
    if not collector.connect():
        print("Exiting due to connection failure")
        return
    
    try:
        # Start collection
        collector.start_collection(args.samples)
        
        # Run for specified duration or until interrupted
        if args.duration and args.duration > 0:
            print(f"Collecting data for {args.duration} seconds...")
            time.sleep(args.duration)
        else:
            print("Collecting data... Press Ctrl+C to stop")
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nStopping data collection...")
    finally:
        collector.stop_collection()
        collector.disconnect()


if __name__ == '__main__':
    main()
