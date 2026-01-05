#!/usr/bin/env python3
"""
Real-time RPLidar Visualization
Displays LiDAR scan data in a 2D polar plot using matplotlib
"""

import serial
import struct
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sys
import time
import glob
import os

# Default port for RPLidar (adjust if needed)
PORT_NAME = '/dev/ttyUSB0'

# Check if we're in SSH session (no DISPLAY)
if os.environ.get('DISPLAY') is None:
    print("No DISPLAY detected - saving to file instead of showing interactive plot")
    matplotlib.use('Agg')
    SAVE_MODE = True
else:
    # Try to use interactive backend
    try:
        matplotlib.use('TkAgg')
        SAVE_MODE = False
    except:
        print("TkAgg not available - saving to file instead")
        matplotlib.use('Agg')
        SAVE_MODE = True

def find_lidar_port():
    """Auto-detect RPLidar port, avoiding Arduino ports."""
    # RPLidar typically uses ttyUSB* (CP210x chip)
    # Arduino typically uses ttyACM* (native USB)
    usb_ports = sorted(glob.glob('/dev/ttyUSB*'))
    acm_ports = sorted(glob.glob('/dev/ttyACM*'))
    
    print("\n=== Port Detection ===")
    if usb_ports:
        print(f"USB ports found: {', '.join(usb_ports)}")
    if acm_ports:
        print(f"ACM ports found (likely Arduino): {', '.join(acm_ports)}")
    
    # Prefer ttyUSB* ports for RPLidar
    if usb_ports:
        port = usb_ports[0]
        print(f"Selected RPLidar port: {port}")
        
        # Check accessibility
        if not os.access(port, os.R_OK | os.W_OK):
            print(f"\n✗ No read/write permission for {port}")
            print("Fix with one of these:")
            print(f"  sudo usermod -a -G dialout $USER  # Permanent (logout required)")
            print(f"  sudo chmod 666 {port}             # Temporary")
            return None
        
        print(f"✓ Port accessible")
        print("=" * 60)
        return port
    
    # If no ttyUSB* ports, warn about ttyACM*
    if acm_ports:
        print("\n⚠ Warning: Only ACM ports found (typically Arduino, not RPLidar)")
        print("RPLidar A1M8 uses CP210x chip and appears as /dev/ttyUSB*")
        print("\nIf you're sure it's the RPLidar, specify port manually:")
        print(f"  python3 visualize.py {acm_ports[0]}")
        return None
    
    print("\n✗ No USB serial ports found!")
    print("\nTroubleshooting:")
    print("1. Check USB cable connection")
    print("2. Run: lsusb (should see CP210x or Silicon Labs)")
    print("3. Run: dmesg | grep tty | tail")
    print("=" * 60)
    return None


class LidarVisualizer:
    def __init__(self, port):
        self.port = port
        self.serial_port = None
        self.fig = None
        self.ax = None
        self.scatter = None
        self.max_frames = 300 if SAVE_MODE else None  # Limit frames when saving
        
    def setup_plot(self):
        """Setup the matplotlib polar plot"""
        self.fig = plt.figure(figsize=(10, 10))
        self.ax = self.fig.add_subplot(111, projection='polar')
        self.ax.set_ylim(0, 6000)  # Set max range to 6000mm (6 meters)
        self.ax.set_title('RPLidar A1M8 - Real-time Scan Visualization', pad=20)
        self.ax.grid(True)
        
        # Initialize empty scatter plot
        self.scatter = self.ax.scatter([], [], s=2, c='blue', alpha=0.75)
        
        # Add range circles labels
        self.ax.set_yticks([1000, 2000, 3000, 4000, 5000, 6000])
        self.ax.set_yticklabels(['1m', '2m', '3m', '4m', '5m', '6m'])
        
    def init_animation(self):
        """Initialize animation"""
        self.scatter.set_offsets(np.empty((0, 2)))
        return self.scatter,
    
    def update_plot(self, frame):
        """Update plot with new scan data"""
        try:
            angles = []
            distances = []
            
            # Collect one complete scan
            for i in range(500):  # Collect up to 500 measurements
                data = self.serial_port.read(5)
                
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
                
                if quality > 0 and distance > 0:
                    angles.append(np.radians(angle))
                    distances.append(distance)
                
                # Complete scan on start flag
                if start_flag and len(angles) > 10:
                    break
            
            # Update scatter plot
            if len(angles) > 0:
                offsets = np.column_stack([angles, distances])
                self.scatter.set_offsets(offsets)
            
            # Progress indicator
            if SAVE_MODE and frame % 50 == 0:
                print(f"Collected {frame} frames...")
            
        except Exception as e:
            print(f"Error updating plot: {e}")
        
        return self.scatter,
    
    def run(self):
        """Start visualization"""
        try:
            print(f"Connecting to RPLidar on {self.port}...")
            self.serial_port = serial.Serial(
                self.port,
                115200,
                timeout=1,
                dsrdtr=True
            )
            time.sleep(0.5)
            print("✓ Connected successfully!\n")
            
            # Initialize LIDAR
            self._init_lidar()
            
            # Start scanning
            self._start_scan()
            
            # Setup plot
            self.setup_plot()
            
            if SAVE_MODE:
                print(f"Starting visualization in SAVE mode...")
                print(f"Collecting {self.max_frames} frames (~{self.max_frames//20} seconds)")
                print("Output: lidar_scan.gif")
            else:
                print("Starting visualization... (Close the window to stop)")
            
            # Create animation
            # In save mode, specify exact number of frames
            # In interactive mode, run indefinitely
            ani = animation.FuncAnimation(
                self.fig,
                self.update_plot,
                init_func=self.init_animation,
                frames=self.max_frames if SAVE_MODE else None,  # Limit frames in save mode
                interval=50,  # 50ms = ~20 FPS
                blit=True,
                cache_frame_data=False,
                repeat=False  # Don't repeat animation
            )
            
            if SAVE_MODE:
                # Save to file
                print("\nSaving animation (this may take a minute)...")
                ani.save('lidar_scan.gif', writer='pillow', fps=20)
                print(f"✓ Animation saved to: lidar_scan.gif ({self.max_frames} frames)")
            else:
                # Show interactive plot
                plt.show()
                
        except KeyboardInterrupt:
            print("\n\nStopped by user (Ctrl+C)")
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
    
    def _init_lidar(self):
        """Initialize RPLIDAR"""
        # Clear buffers
        self.serial_port.reset_input_buffer()
        self.serial_port.reset_output_buffer()
        time.sleep(0.5)
        
        # Get device info
        print("Device info:")
        self.serial_port.write(b'\xA5\x50')
        time.sleep(0.2)
        descriptor = self.serial_port.read(7)
        if len(descriptor) == 7:
            data_len = struct.unpack('<I', descriptor[2:6])[0] & 0x3FFFFFFF
            info_data = self.serial_port.read(data_len)
            if len(info_data) >= 20:
                model = info_data[0]
                firmware_minor = info_data[1]
                firmware_major = info_data[2]
                print(f"  Model: {model}")
                print(f"  Firmware: {firmware_major}.{firmware_minor}\n")
        
        # Stop any previous scan
        self.serial_port.write(b'\xA5\x25')
        time.sleep(0.5)
        self.serial_port.reset_input_buffer()
        
        # Start motor (DTR=False for A1M8)
        print("Starting motor...")
        self.serial_port.setDTR(False)
        time.sleep(3)
        print("✓ Motor ready\n")
        
        self.serial_port.reset_input_buffer()
        time.sleep(0.2)
    
    def _start_scan(self):
        """Start LIDAR scan"""
        self.serial_port.write(b'\xA5\x20')
        self.serial_port.flush()
        time.sleep(0.3)
        
        # Read descriptor
        descriptor = self.serial_port.read(7)
        if len(descriptor) != 7 or descriptor[0:2] != b'\xA5\x5A':
            raise Exception("Failed to start scan")
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.serial_port and self.serial_port.is_open:
                # Stop scan
                self.serial_port.write(b'\xA5\x25')
                time.sleep(0.2)
                
                # Stop motor
                self.serial_port.setDTR(False)
                self.serial_port.setRTS(False)
                time.sleep(0.2)
                
                self.serial_port.close()
                print("✓ RPLidar stopped and disconnected")
        except:
            pass

def main():
    """Main function"""
    port = None
    
    # Check for command line argument first
    if len(sys.argv) > 1:
        port = sys.argv[1]
        print(f"Using specified port: {port}")
        
        # Verify it exists
        if not os.path.exists(port):
            print(f"✗ Port {port} does not exist!")
            print("Available ports:")
            for p in glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'):
                print(f"  {p}")
            sys.exit(1)
    else:
        # Auto-detect RPLidar port
        port = find_lidar_port()
        
        if not port:
            print("\n✗ Could not find RPLidar port")
            print("\nSpecify port manually:")
            print("  python3 visualize.py /dev/ttyUSB0")
            sys.exit(1)
    
    visualizer = LidarVisualizer(port)
    visualizer.run()

if __name__ == "__main__":
    main()
