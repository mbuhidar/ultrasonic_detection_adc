#!/usr/bin/env python3
"""
Real-time Data Viewer for Ultrasonic Sensors

This script provides a simple real-time visualization of sensor data.
Requires matplotlib for plotting.
"""

import serial
import yaml
import time
from collections import deque
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from pathlib import Path


class RealtimeViewer:
    """Real-time visualization of ultrasonic sensor data."""
    
    def __init__(self, config_path: str = "../config.yaml", history_size: int = 100):
        """Initialize the viewer."""
        self.config = self._load_config(config_path)
        self.history_size = history_size
        self.num_sensors = self.config['sensors']['count']
        
        # Data storage for plotting
        self.timestamps = deque(maxlen=history_size)
        self.sensor_data = [deque(maxlen=history_size) for _ in range(self.num_sensors)]
        
        # Serial connection
        self.serial_conn = None
        self.start_time = time.time()
        
    def _load_config(self, config_path: str):
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def connect(self) -> bool:
        """Connect to Arduino."""
        try:
            self.serial_conn = serial.Serial(
                port=self.config['arduino']['port'],
                baudrate=self.config['arduino']['baudrate'],
                timeout=self.config['arduino']['timeout']
            )
            time.sleep(2)
            
            # Clear initialization messages
            while self.serial_conn.in_waiting:
                self.serial_conn.readline()
            
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def start(self):
        """Start data collection and visualization."""
        if not self.connect():
            return
        
        # Send start command
        samples = self.config['sensors']['samples_per_trigger']
        self.serial_conn.write(f"START:{samples}\n".encode('utf-8'))
        
        # Setup plot
        fig, ax = plt.subplots(figsize=(12, 6))
        lines = []
        for i in range(self.num_sensors):
            line, = ax.plot([], [], label=f'Sensor {i+1}', marker='o', markersize=3)
            lines.append(line)
        
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Distance (cm)')
        ax.set_title('Ultrasonic Sensor Real-time Data')
        ax.legend()
        ax.grid(True)
        
        def init():
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 500)
            return lines
        
        def update(frame):
            # Read data from serial
            if self.serial_conn and self.serial_conn.in_waiting:
                line = self.serial_conn.readline().decode('utf-8').strip()
                
                if line.startswith('S,'):
                    try:
                        parts = line.split(',')
                        timestamp = (time.time() - self.start_time)
                        self.timestamps.append(timestamp)
                        
                        for i, value in enumerate(parts[2:]):
                            adc_value = int(value)
                            distance = adc_value  # MB1300: ADC ≈ cm at 5V
                            self.sensor_data[i].append(distance)
                    except Exception as e:
                        pass
            
            # Update plot
            if self.timestamps:
                for i, line in enumerate(lines):
                    line.set_data(list(self.timestamps), list(self.sensor_data[i]))
                
                # Auto-scale x-axis
                if len(self.timestamps) > 0:
                    ax.set_xlim(max(0, self.timestamps[-1] - 10), 
                               self.timestamps[-1] + 1)
                
                # Auto-scale y-axis based on data
                all_data = [val for sensor in self.sensor_data for val in sensor]
                if all_data:
                    min_val = min(all_data)
                    max_val = max(all_data)
                    margin = (max_val - min_val) * 0.1
                    ax.set_ylim(max(0, min_val - margin), max_val + margin)
            
            return lines
        
        ani = animation.FuncAnimation(fig, update, init_func=init,
                                     interval=50, blit=True)
        
        plt.show()
        
        # Cleanup
        if self.serial_conn:
            self.serial_conn.write(b"STOP\n")
            self.serial_conn.close()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Real-time Ultrasonic Sensor Viewer')
    parser.add_argument('-c', '--config', default='../config.yaml',
                      help='Path to configuration file')
    parser.add_argument('-H', '--history', type=int, default=100,
                      help='Number of data points to display')
    
    args = parser.parse_args()
    
    viewer = RealtimeViewer(args.config, args.history)
    
    try:
        viewer.start()
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == '__main__':
    main()
