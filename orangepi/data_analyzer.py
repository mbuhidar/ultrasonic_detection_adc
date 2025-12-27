#!/usr/bin/env python3
"""
Data Analysis Tools for Ultrasonic Sensor Data

Provides utilities for analyzing collected sensor data including:
- Statistical analysis
- Data visualization
- Export to various formats
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Optional
import json


class DataAnalyzer:
    """Analyze collected ultrasonic sensor data."""
    
    def __init__(self, data_file: str):
        """Initialize analyzer with data file."""
        self.data_file = Path(data_file)
        self.df = None
        self._load_data()
    
    def _load_data(self):
        """Load data from file."""
        if self.data_file.suffix == '.csv':
            self.df = pd.read_csv(self.data_file)
        elif self.data_file.suffix == '.json':
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            self.df = pd.json_normalize(data)
        else:
            raise ValueError(f"Unsupported file format: {self.data_file.suffix}")
        
        print(f"Loaded {len(self.df)} records from {self.data_file.name}")
    
    def get_statistics(self) -> dict:
        """Calculate statistics for each sensor."""
        stats = {}
        
        # Find sensor columns
        sensor_cols = [col for col in self.df.columns if 'sensor_' in col and 'distance' in col]
        
        for col in sensor_cols:
            sensor_name = col.replace('_distance_cm', '')
            stats[sensor_name] = {
                'mean': self.df[col].mean(),
                'median': self.df[col].median(),
                'std': self.df[col].std(),
                'min': self.df[col].min(),
                'max': self.df[col].max(),
                'count': self.df[col].count()
            }
        
        return stats
    
    def plot_time_series(self, sensors: Optional[List[int]] = None, 
                         save_path: Optional[str] = None):
        """Plot time series data for specified sensors."""
        sensor_cols = [col for col in self.df.columns 
                      if 'sensor_' in col and 'distance' in col]
        
        if sensors:
            sensor_cols = [col for col in sensor_cols 
                          if any(f'sensor_{s}' in col for s in sensors)]
        
        plt.figure(figsize=(14, 6))
        
        for col in sensor_cols:
            sensor_num = col.split('_')[1]
            plt.plot(self.df.index, self.df[col], 
                    label=f'Sensor {sensor_num}', alpha=0.7)
        
        plt.xlabel('Sample Number')
        plt.ylabel('Distance (cm)')
        plt.title('Ultrasonic Sensor Time Series Data')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved plot to {save_path}")
        else:
            plt.show()
    
    def plot_histogram(self, sensors: Optional[List[int]] = None,
                      bins: int = 50, save_path: Optional[str] = None):
        """Plot histogram of distance measurements."""
        sensor_cols = [col for col in self.df.columns 
                      if 'sensor_' in col and 'distance' in col]
        
        if sensors:
            sensor_cols = [col for col in sensor_cols 
                          if any(f'sensor_{s}' in col for s in sensors)]
        
        fig, axes = plt.subplots(len(sensor_cols), 1, 
                                figsize=(10, 4 * len(sensor_cols)))
        
        if len(sensor_cols) == 1:
            axes = [axes]
        
        for ax, col in zip(axes, sensor_cols):
            sensor_num = col.split('_')[1]
            ax.hist(self.df[col].dropna(), bins=bins, alpha=0.7, edgecolor='black')
            ax.set_xlabel('Distance (cm)')
            ax.set_ylabel('Frequency')
            ax.set_title(f'Sensor {sensor_num} Distance Distribution')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved histogram to {save_path}")
        else:
            plt.show()
    
    def export_summary(self, output_file: str):
        """Export summary statistics to file."""
        stats = self.get_statistics()
        
        output_path = Path(output_file)
        
        if output_path.suffix == '.json':
            with open(output_path, 'w') as f:
                json.dump(stats, f, indent=2)
        elif output_path.suffix == '.csv':
            stats_df = pd.DataFrame(stats).T
            stats_df.to_csv(output_path)
        else:
            # Text format
            with open(output_path, 'w') as f:
                f.write("Ultrasonic Sensor Data Summary\n")
                f.write("=" * 50 + "\n\n")
                for sensor, sensor_stats in stats.items():
                    f.write(f"{sensor.upper()}:\n")
                    for key, value in sensor_stats.items():
                        f.write(f"  {key:10s}: {value:.2f}\n")
                    f.write("\n")
        
        print(f"Exported summary to {output_path}")
    
    def detect_objects(self, threshold_cm: float = 100, 
                      min_duration_samples: int = 3) -> pd.DataFrame:
        """
        Detect objects based on distance threshold.
        
        Returns DataFrame with object detection events.
        """
        sensor_cols = [col for col in self.df.columns 
                      if 'sensor_' in col and 'distance' in col]
        
        detections = []
        
        for col in sensor_cols:
            sensor_num = col.split('_')[1]
            
            # Find samples below threshold
            below_threshold = self.df[col] < threshold_cm
            
            # Find continuous sequences
            detection_start = None
            for idx, (current, value) in enumerate(zip(below_threshold, self.df[col])):
                if current and detection_start is None:
                    detection_start = idx
                elif not current and detection_start is not None:
                    duration = idx - detection_start
                    if duration >= min_duration_samples:
                        detections.append({
                            'sensor': f'sensor_{sensor_num}',
                            'start_sample': detection_start,
                            'end_sample': idx - 1,
                            'duration_samples': duration,
                            'min_distance_cm': self.df[col].iloc[detection_start:idx].min(),
                            'mean_distance_cm': self.df[col].iloc[detection_start:idx].mean()
                        })
                    detection_start = None
        
        return pd.DataFrame(detections)


def main():
    """Main entry point for data analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze Ultrasonic Sensor Data')
    parser.add_argument('data_file', help='Path to data file (CSV or JSON)')
    parser.add_argument('-s', '--stats', action='store_true',
                      help='Display statistics')
    parser.add_argument('-p', '--plot', action='store_true',
                      help='Plot time series')
    parser.add_argument('-H', '--histogram', action='store_true',
                      help='Plot histogram')
    parser.add_argument('-d', '--detect', type=float, metavar='THRESHOLD',
                      help='Detect objects below threshold (cm)')
    parser.add_argument('-o', '--output', help='Output file for results')
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = DataAnalyzer(args.data_file)
    
    # Display statistics
    if args.stats:
        stats = analyzer.get_statistics()
        print("\nStatistics:")
        print("=" * 50)
        for sensor, sensor_stats in stats.items():
            print(f"\n{sensor.upper()}:")
            for key, value in sensor_stats.items():
                print(f"  {key:10s}: {value:.2f}")
    
    # Plot time series
    if args.plot:
        analyzer.plot_time_series(save_path=args.output)
    
    # Plot histogram
    if args.histogram:
        analyzer.plot_histogram(save_path=args.output)
    
    # Detect objects
    if args.detect:
        detections = analyzer.detect_objects(threshold_cm=args.detect)
        print(f"\nDetected {len(detections)} objects:")
        print(detections.to_string())
        
        if args.output:
            detections.to_csv(args.output, index=False)
            print(f"\nSaved detections to {args.output}")


if __name__ == '__main__':
    main()
