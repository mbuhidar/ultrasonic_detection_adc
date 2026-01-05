#!/usr/bin/env python3
"""
Real-time RPLidar Visualization
Displays LiDAR scan data in a 2D polar plot using matplotlib
"""

import serial
import struct
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sys
import time
import glob
import os

# Default port for RPLidar (adjust if needed)
PORT_NAME = '/dev/ttyUSB0'

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
        self.angles = []
        self.distances = []
        self.iterator = None
        
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
            # Collect measurements until we have a complete scan
            for i in range(500):  # Read up to 500 points
                data = self.serial_port.read(5)
                
                if len(data) != 5:
                    break
                
                # Parse measurement
                byte0 = data[0]
                start_flag = (byte0 & 0x01) != 0
                quality = (byte0 >> 2) & 0x3F
                
                angle_raw = struct.unpack('<H', data[1:3])[0]
                angle = (angle_raw >> 1) / 64.0
                
                distance_raw = struct.unpack('<H', data[3:5])[0]
                distance = distance_raw / 4.0
                
                # new_scan is True at start of each 360° rotation
                if start_flag and len(self.angles) > 0:
                    # We have a complete scan, update the plot
                    break
                
                self.angles.append(np.radians(angle))
                self.distances.append(distance)
            
            if len(self.angles) > 0:
                # Update scatter plot
                self.scatter.set_offsets(np.c_[self.angles, self.distances])
                
                # Update title with scan info
                valid_dists = [d for d in self.distances if d > 0]
                if valid_dists:
                    self.ax.set_title(
                        f'RPLidar A1M8 - Real-time Scan ({len(self.angles)} points)\n'
                        f'Min: {min(valid_dists):.0f}mm | Max: {max(valid_dists):.0f}mm | '
                        f'Avg: {np.mean(valid_dists):.0f}mm',
                        pad=20
                    )
                
                # Clear for next scan
                self.angles = []
                self.distances = []
                
        except Exception as e:
            print(f"Error updating plot: {e}")
        
        return self.scatter,
    
    def run(self):
        """Start visualization"""
        try:
            print(f"Connecting to RPLidar on {self.port}...")
            self.serial_port = serial.Serial(
                self.port,
                115200,  # RPLidar A1M8 standard baudrate
                timeout=1,
                dsrdtr=True
            )
            time.sleep(0.5)
            print("✓ Connected successfully!")
            
            # Get device info
            print("\nGetting device info...")
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            time.sleep(0.2)
            
            self.serial_port.write(b'\xA5\x50')  # GET_INFO command
            time.sleep(0.2)
            descriptor = self.serial_port.read(7)
            if len(descriptor) == 7:
                data_len = struct.unpack('<I', descriptor[2:6])[0] & 0x3FFFFFFF
                info_data = self.serial_port.read(data_len)
                if len(info_data) >= 4:
                    model = info_data[0]
                    firmware_minor = info_data[1]
                    firmware_major = info_data[2]
                    hardware = info_data[3]
                    print(f"\nDevice: Model={model}, Firmware={firmware_major}.{firmware_minor}, Hardware={hardware}")
            
            print("\nStarting visualization... (Close the window to stop)")
            
            # Stop any previous operations
            print("Sending STOP command...")
            self.serial_port.write(b'\xA5\x25')
            time.sleep(0.5)
            self.serial_port.reset_input_buffer()
            
            # Start motor (DTR=False makes motor spin on A1M8)
            print("Starting motor...")
            self.serial_port.setDTR(False)
            time.sleep(3)  # Wait for motor stabilization
            print("✓ Motor ready!")
            
            # Clear buffers
            self.serial_port.reset_input_buffer()
            time.sleep(0.5)
            
            # Send SCAN command
            print("Starting scan...")
            self.serial_port.write(b'\xA5\x20')
            self.serial_port.flush()
            time.sleep(0.3)
            
            # Read and verify descriptor
            descriptor = self.serial_port.read(7)
            if len(descriptor) != 7 or descriptor[0:2] != b'\xA5\x5A':
                print("Error: Invalid scan descriptor")
                return
            
            print("✓ Scan active!\n")
            
            # Setup plot
            self.setup_plot()
            
            # Create animation
            ani = animation.FuncAnimation(
                self.fig,
                self.update_plot,
                init_func=self.init_animation,
                interval=50,  # Update every 50ms
                blit=True,
                cache_frame_data=False
            )
            
            plt.show()
            
        except KeyboardInterrupt:
            print("\nVisualization interrupted by user")
        except Exception as e:
            print(f"\n✗ Error: {e}")
            print("\nTroubleshooting tips:")
            print("1. Check RPLidar USB connection")
            print("2. Verify port: ls /dev/ttyUSB*")
            print("3. Check it's not Arduino port (Arduino uses /dev/ttyACM0)")
            print("4. Check permissions: sudo chmod 666 /dev/ttyUSB0")
            print("5. Add to dialout group: sudo usermod -a -G dialout $USER")
            print("6. Install dependencies: pip install matplotlib numpy")
            import traceback
            traceback.print_exc()
        finally:
            if self.serial_port:
                print("\nStopping LiDAR...")
                try:
                    # Stop scan
                    self.serial_port.write(b'\xA5\x25')
                    time.sleep(0.2)
                    
                    # Stop motor
                    self.serial_port.setDTR(False)
                    self.serial_port.setRTS(False)
                    time.sleep(0.2)
                    
                    self.serial_port.close()
                    print("✓ Disconnected")
                except Exception as e:
                    print(f"Error during cleanup: {e}")

def main():
    """Main function"""
    port = None
    
    # Check for command line argument first
    if len(sys.argv) > 1:
        port = sys.argv[1]
        print(f"Using specified port: {port}")
        
        # Verify it exists
        if not os.path.exists(port):
            print(f"\n✗ Error: Port {port} does not exist")
            print(f"Available ports: {', '.join(glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'))}")
            sys.exit(1)
    else:
        # Auto-detect RPLidar port
        port = find_lidar_port()
        
        if not port:
            print("\n✗ Could not auto-detect RPLidar port")
            print(f"\nTry specifying port manually:")
            print(f"  python3 visualize.py /dev/ttyUSB0")
            sys.exit(1)
    
    visualizer = LidarVisualizer(port)
    visualizer.run()

if __name__ == "__main__":
    main()
