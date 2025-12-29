#!/usr/bin/env python3
"""
Ultrasonic Echo Profile Analyzer

Analyzes MB1300 sensor echo profile data captured via PW pin output.
Provides visualization and object detection from acoustic envelope data.

Usage:
    python echo_analyzer.py <data_file.csv>
    python echo_analyzer.py <data_file.csv> --plot-type heatmap
    python echo_analyzer.py <data_file.csv> --sensor 1 --row 10
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
from pathlib import Path
from datetime import datetime


class EchoProfileAnalyzer:
    """Analyze ultrasonic echo profile data from MB1300 sensors."""
    
    def __init__(self, csv_file: str):
        """
        Initialize analyzer with CSV data file.
        
        Args:
            csv_file: Path to CSV file with sensor data
        """
        self.csv_file = Path(csv_file)
        self.df = None
        self.num_readings = 240  # Default, will be detected from data
        self.cm_per_reading = 0.86  # 50µs sampling = ~0.86cm resolution
        
        self._load_data()
    
    def _load_data(self):
        """Load and validate CSV data."""
        try:
            self.df = pd.read_csv(self.csv_file)
            print(f"✓ Loaded {len(self.df)} rows from {self.csv_file.name}")
            
            # Detect number of readings per sensor
            reading_cols = [col for col in self.df.columns if 'reading_' in col]
            if reading_cols:
                self.num_readings = len(reading_cols)
                print(f"✓ Detected {self.num_readings} readings per sensor")
            
            # Convert timestamp to datetime
            self.df['system_timestamp'] = pd.to_datetime(self.df['system_timestamp'])
            
            # Count sensors and trigger events
            num_sensors = len(self.df['sensor_id'].unique())
            num_triggers = len(self.df) // num_sensors
            print(f"✓ Found {num_sensors} sensors, {num_triggers} trigger events")
            
        except Exception as e:
            print(f"✗ Error loading data: {e}")
            raise
    
    def get_sensor_data(self, sensor_id: int, row_idx: int = None) -> np.ndarray:
        """
        Extract readings for a specific sensor and row.
        
        Args:
            sensor_id: Sensor ID (1 or 2)
            row_idx: Row index (if None, returns all rows)
            
        Returns:
            Array of readings (shape: [num_readings] or [num_rows, num_readings])
        """
        cols = [f'reading_{i}' for i in range(1, self.num_readings + 1)]
        
        sensor_df = self.df[self.df['sensor_id'] == sensor_id]
        
        if row_idx is not None:
            return pd.to_numeric(sensor_df.iloc[row_idx][cols], errors='coerce').fillna(0).values
        else:
            return sensor_df[cols].apply(pd.to_numeric, errors='coerce').fillna(0).values
    
    def get_distance_axis(self) -> np.ndarray:
        """Get distance axis in cm for plotting."""
        return np.arange(self.num_readings) * self.cm_per_reading
    
    def plot_echo_profile(self, sensor_id: int, row_idx: int = 0, 
                          ax: plt.Axes = None, show: bool = True):
        """
        Plot echo profile for a single trigger event.
        
        Args:
            sensor_id: Sensor ID (1 or 2)
            row_idx: Which trigger event to plot
            ax: Matplotlib axes (creates new if None)
            show: Whether to display plot immediately
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 6))
        
        readings = self.get_sensor_data(sensor_id, row_idx)
        distances = self.get_distance_axis()
        
        # Plot echo profile
        ax.plot(distances, readings, linewidth=1.5, color='#2E86AB')
        ax.fill_between(distances, readings, alpha=0.3, color='#2E86AB')
        
        ax.set_xlabel('Distance (cm)', fontsize=12)
        ax.set_ylabel('Echo Amplitude (ADC)', fontsize=12)
        ax.set_title(f'Sensor {sensor_id} - Echo Profile (Trigger Event {row_idx})', fontsize=14)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, distances[-1])
        ax.set_ylim(0, 1024)
        
        # Add threshold line
        ax.axhline(y=50, color='red', linestyle='--', alpha=0.5, label='Detection threshold')
        ax.legend()
        
        if show:
            plt.tight_layout()
            plt.show()
    
    def plot_heatmap(self, sensor_id: int, start_row: int = 0, 
                     end_row: int = None, ax: plt.Axes = None, show: bool = True):
        """
        Plot heatmap showing echo profiles over time.
        
        Args:
            sensor_id: Sensor ID (1 or 2)
            start_row: First row to include
            end_row: Last row to include (None = all)
            ax: Matplotlib axes (creates new if None)
            show: Whether to display plot immediately
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(14, 8))
        
        data = self.get_sensor_data(sensor_id)
        
        if end_row is None:
            end_row = len(data)
        
        data_slice = data[start_row:end_row]
        
        im = ax.imshow(data_slice, aspect='auto', cmap='hot', 
                       interpolation='bilinear', origin='lower',
                       vmin=0, vmax=200)  # Limit scale for better contrast
        
        ax.set_xlabel('Distance (cm)', fontsize=12)
        ax.set_ylabel('Trigger Event (time →)', fontsize=12)
        ax.set_title(f'Sensor {sensor_id} - Echo Envelope Heatmap', fontsize=14)
        
        # Add distance markers on x-axis
        xticks = np.arange(0, self.num_readings, 30)
        xticklabels = [f'{int(x * self.cm_per_reading)}' for x in xticks]
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels)
        
        cbar = plt.colorbar(im, ax=ax, label='Echo Amplitude (ADC)')
        
        if show:
            plt.tight_layout()
            plt.show()
    
    def detect_objects(self, sensor_id: int, row_idx: int, 
                       threshold: int = 50, min_width: int = 3) -> list:
        """
        Detect objects from echo profile peaks.
        
        Args:
            sensor_id: Sensor ID (1 or 2)
            row_idx: Which trigger event to analyze
            threshold: Minimum ADC value to consider as object
            min_width: Minimum number of consecutive readings for valid object
            
        Returns:
            List of dicts with object info: [{'distance_cm': float, 'strength': int, 'width_cm': float}, ...]
        """
        readings = self.get_sensor_data(sensor_id, row_idx)
        distances = self.get_distance_axis()
        
        objects = []
        in_object = False
        object_start = 0
        object_peak = 0
        
        for i, value in enumerate(readings):
            if value >= threshold:
                if not in_object:
                    in_object = True
                    object_start = i
                    object_peak = value
                else:
                    object_peak = max(object_peak, value)
            else:
                if in_object:
                    object_width = i - object_start
                    if object_width >= min_width:
                        objects.append({
                            'distance_cm': round(distances[object_start + object_width // 2], 1),
                            'strength': object_peak,
                            'width_cm': round(object_width * self.cm_per_reading, 1)
                        })
                    in_object = False
        
        return objects
    
    def plot_comparison(self, row_idx: int = 0, show: bool = True):
        """
        Plot both sensors side-by-side for comparison.
        
        Args:
            row_idx: Which trigger event to plot
            show: Whether to display plot immediately
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        self.plot_echo_profile(1, row_idx, ax=ax1, show=False)
        self.plot_echo_profile(2, row_idx, ax=ax2, show=False)
        
        fig.suptitle(f'Sensor Comparison - Trigger Event {row_idx}', 
                     fontsize=16, y=1.02)
        
        if show:
            plt.tight_layout()
            plt.show()
    
    def plot_time_series(self, sensor_id: int, distance_cm: float, 
                        window: int = 5, ax: plt.Axes = None, show: bool = True):
        """
        Plot echo amplitude at specific distance over time.
        
        Args:
            sensor_id: Sensor ID (1 or 2)
            distance_cm: Distance to monitor (cm)
            window: Average readings within ±window cm
            ax: Matplotlib axes (creates new if None)
            show: Whether to display plot immediately
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 6))
        
        # Find reading indices for distance range
        reading_idx = int(distance_cm / self.cm_per_reading)
        window_readings = int(window / self.cm_per_reading)
        
        start_idx = max(0, reading_idx - window_readings)
        end_idx = min(self.num_readings, reading_idx + window_readings)
        
        data = self.get_sensor_data(sensor_id)
        
        # Average over window
        values = data[:, start_idx:end_idx].mean(axis=1)
        
        sensor_df = self.df[self.df['sensor_id'] == sensor_id].reset_index(drop=True)
        
        ax.plot(values, linewidth=1.5, marker='o', markersize=4)
        ax.set_xlabel('Trigger Event', fontsize=12)
        ax.set_ylabel('Echo Amplitude (ADC)', fontsize=12)
        ax.set_title(f'Sensor {sensor_id} - Echo at {distance_cm:.0f}cm Over Time', 
                     fontsize=14)
        ax.grid(True, alpha=0.3)
        
        if show:
            plt.tight_layout()
            plt.show()
    
    def plot_distance_vs_time(self, sensor_id: int, threshold: int = 50,
                              ax: plt.Axes = None, show: bool = True):
        """
        Plot detected object distance over time (tracks movement).
        
        Args:
            sensor_id: Sensor ID (1 or 2)
            threshold: Minimum ADC value to consider as object
            ax: Matplotlib axes (creates new if None)
            show: Whether to display plot immediately
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 6))
        
        data = self.get_sensor_data(sensor_id)
        distances = self.get_distance_axis()
        
        detected_distances = []
        detected_strengths = []
        
        # For each trigger event, find the strongest echo
        for row_idx in range(len(data)):
            readings = data[row_idx]
            
            # Find peaks above threshold
            above_threshold = readings >= threshold
            if above_threshold.any():
                # Get distance of strongest echo
                max_idx = np.argmax(readings)
                if readings[max_idx] >= threshold:
                    detected_distances.append(distances[max_idx])
                    detected_strengths.append(readings[max_idx])
                else:
                    detected_distances.append(np.nan)
                    detected_strengths.append(np.nan)
            else:
                detected_distances.append(np.nan)
                detected_strengths.append(np.nan)
        
        # Plot distance over time
        trigger_events = np.arange(len(detected_distances))
        
        # Color by strength
        scatter = ax.scatter(trigger_events, detected_distances, 
                           c=detected_strengths, cmap='hot', 
                           s=50, alpha=0.8, edgecolors='black', linewidth=0.5)
        
        # Connect points with line
        ax.plot(trigger_events, detected_distances, 
               linewidth=1, alpha=0.5, color='gray', linestyle='--')
        
        ax.set_xlabel('Trigger Event (time →)', fontsize=12)
        ax.set_ylabel('Object Distance (cm)', fontsize=12)
        ax.set_title(f'Sensor {sensor_id} - Object Distance vs Time', fontsize=14)
        ax.grid(True, alpha=0.3)
        ax.invert_yaxis()  # Closer objects at top
        
        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax, label='Echo Strength (ADC)')
        
        if show:
            plt.tight_layout()
            plt.show()
    
    def generate_report(self, output_file: str = None):
        """
        Generate summary report of data.
        
        Args:
            output_file: Path to save report (None = print to console)
        """
        report = []
        report.append("=" * 70)
        report.append("ULTRASONIC ECHO PROFILE ANALYSIS REPORT")
        report.append("=" * 70)
        report.append(f"Data File: {self.csv_file}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("DATA SUMMARY")
        report.append("-" * 70)
        num_sensors = len(self.df['sensor_id'].unique())
        num_triggers = len(self.df) // num_sensors
        report.append(f"Total trigger events: {num_triggers}")
        report.append(f"Readings per sensor: {self.num_readings}")
        report.append(f"Spatial resolution: {self.cm_per_reading:.2f} cm/reading")
        report.append(f"Maximum range: {self.num_readings * self.cm_per_reading:.1f} cm")
        report.append("")
        
        for sensor_id in sorted(self.df['sensor_id'].unique()):
            report.append(f"SENSOR {sensor_id} STATISTICS")
            report.append("-" * 70)
            
            data = self.get_sensor_data(sensor_id)
            
            report.append(f"Mean amplitude: {data.mean():.1f} ADC")
            report.append(f"Max amplitude: {data.max()} ADC")
            report.append(f"Min amplitude: {data.min()} ADC")
            report.append(f"Std deviation: {data.std():.1f} ADC")
            
            # Count strong echoes
            strong_echoes = (data > 100).sum()
            report.append(f"Strong echoes (>100 ADC): {strong_echoes:,} samples")
            
            # Detect objects in first trigger
            objects = self.detect_objects(sensor_id, 0, threshold=50)
            report.append(f"Objects detected (first trigger): {len(objects)}")
            if objects:
                for i, obj in enumerate(objects, 1):
                    report.append(f"  Object {i}: {obj['distance_cm']}cm, "
                                f"strength={obj['strength']}, width={obj['width_cm']}cm")
            report.append("")
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"✓ Report saved to {output_file}")
        else:
            print(report_text)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze ultrasonic echo profile data from MB1300 sensors'
    )
    parser.add_argument('data_file', help='CSV file with sensor echo profile data')
    parser.add_argument('--sensor', type=int, choices=[1, 2], default=1,
                       help='Sensor ID to analyze (default: 1)')
    parser.add_argument('--row', type=int, default=0,
                       help='Trigger event index for profile plots (default: 0)')
    parser.add_argument('--start-row', type=int, default=0,
                       help='Start row for heatmap (default: 0)')
    parser.add_argument('--end-row', type=int, default=None,
                       help='End row for heatmap (default: all)')
    parser.add_argument('--plot-type', 
                       choices=['profile', 'heatmap', 'comparison', 'timeseries', 'distance', 'all'],
                       default='all', 
                       help='Type of plot to generate (default: all)')
    parser.add_argument('--distance', type=float, default=50,
                       help='Distance (cm) for time series plot (default: 50)')
    parser.add_argument('--threshold', type=int, default=50,
                       help='Detection threshold for distance tracking (default: 50)')
    parser.add_argument('--report', action='store_true',
                       help='Generate summary report')
    parser.add_argument('--output', help='Output file for report')
    parser.add_argument('--detect', action='store_true',
                       help='Detect and list objects')
    
    args = parser.parse_args()
    
    # Load and analyze data
    analyzer = EchoProfileAnalyzer(args.data_file)
    
    print()  # Blank line for readability
    
    # Generate report if requested
    if args.report:
        analyzer.generate_report(args.output)
        print()
    
    # Detect objects if requested
    if args.detect:
        print(f"Object Detection (Sensor {args.sensor}, Trigger {args.row}):")
        print("-" * 70)
        objects = analyzer.detect_objects(args.sensor, args.row, threshold=50)
        if objects:
            for i, obj in enumerate(objects, 1):
                print(f"  Object {i}: Distance={obj['distance_cm']}cm, "
                      f"Strength={obj['strength']} ADC, Width={obj['width_cm']}cm")
        else:
            print("  No objects detected above threshold")
        print()
    
    # Generate plots
    if args.plot_type in ['profile', 'all']:
        print(f"Generating echo profile for Sensor {args.sensor}, Trigger {args.row}...")
        analyzer.plot_echo_profile(args.sensor, args.row)
    
    if args.plot_type in ['heatmap', 'all']:
        print(f"Generating heatmap for Sensor {args.sensor}...")
        analyzer.plot_heatmap(args.sensor, args.start_row, args.end_row)
    
    if args.plot_type in ['comparison', 'all']:
        print(f"Generating sensor comparison for Trigger {args.row}...")
        analyzer.plot_comparison(args.row)
    
    if args.plot_type == 'timeseries':
        print(f"Generating time series at {args.distance}cm for Sensor {args.sensor}...")
        analyzer.plot_time_series(args.sensor, args.distance)
    
    if args.plot_type in ['distance', 'all']:
        print(f"Generating distance vs time plot for Sensor {args.sensor}...")
        analyzer.plot_distance_vs_time(args.sensor, args.threshold)


if __name__ == '__main__':
    main()
