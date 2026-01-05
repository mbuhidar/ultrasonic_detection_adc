#!/usr/bin/env python3
"""
Basic RPLidar A1M8 Test Script
This script connects to the RPLidar and prints basic scan data.
"""

from rplidar import RPLidar
import sys
import time

# Default port for RPLidar (adjust if needed)
PORT_NAME = '/dev/ttyUSB0'

def test_device_info(lidar):
    """Test connection and get device info"""
    print("\n=== Device Information ===")
    try:
        info = lidar.get_info()
        print(f"Model: {info['model']}")
        print(f"Firmware: {info['firmware'][0]}.{info['firmware'][1]}")
        print(f"Hardware: {info['hardware']}")
        print(f"Serial Number: {info['serialnumber']}")
        
        health = lidar.get_health()
        print(f"\nHealth Status: {health[0]}")
        print(f"Error Code: {health[1]}")
        return True
    except Exception as e:
        print(f"Error getting device info: {e}")
        return False

def basic_scan_test(lidar, num_measurements=50):
    """Perform basic scan test and print sample measurements"""
    print("\n=== Starting Basic Scan Test ===")
    print(f"Collecting {num_measurements} measurements...\n")
    
    import struct
    
    try:
        # Stop any existing operations
        print("Preparing device...")
        try:
            lidar.stop()
        except:
            pass
        
        # Motor control: DTR=False makes motor spin on this device
        print("Starting motor (DTR=False)...")
        lidar._serial_port.setDTR(False)
        time.sleep(3)  # Wait for motor to reach full speed
        
        # Clear buffers after motor stabilizes
        lidar._serial_port.reset_input_buffer()
        time.sleep(0.5)
        print("Motor ready!\n")
        
        print("Starting scan...")
        # Send SCAN command directly
        lidar._serial_port.write(b'\xA5\x20')
        lidar._serial_port.flush()
        time.sleep(0.3)
        
        # Read descriptor
        descriptor = lidar._serial_port.read(7)
        if len(descriptor) != 7 or descriptor[0:2] != b'\xA5\x5A':
            print(f"Error: Invalid scan descriptor")
            return
        
        print("Format: Quality | Angle (degrees) | Distance (mm)")
        print("-" * 50)
        
        count = 0
        scan_num = 1
        
        # Read measurements directly
        while count < num_measurements:
            data = lidar._serial_port.read(5)
            
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
            
            if start_flag and count > 0:
                print(f"\n--- Scan #{scan_num} complete ---\n")
                scan_num += 1
            
            print(f"  {quality:3d}   | {angle:6.2f}°        | {distance:6.1f} mm")
            count += 1
        
        print(f"\n✓ Collected {count} measurements across {scan_num} scans")
        
        # Stop scan
        lidar._serial_port.write(b'\xA5\x25')
        time.sleep(0.2)
                
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"Error during scan: {e}")
        import traceback
        traceback.print_exc()

def continuous_monitoring(lidar, duration=10):
    """Monitor LiDAR continuously for a specified duration"""
    print(f"\n=== Continuous Monitoring ({duration} seconds) ===")
    print("Displaying measurement statistics...\n")
    
    import struct
    
    # Stop any existing operations
    print("Preparing device...")
    try:
        lidar.stop()
    except:
        pass
    
    # Motor control: DTR=False makes motor spin
    print("Starting motor (DTR=False)...")
    lidar._serial_port.setDTR(False)
    time.sleep(3)
    
    lidar._serial_port.reset_input_buffer()
    time.sleep(0.5)
    print("Motor ready!\n")
    
    # Send SCAN command
    print("Starting scan...")
    lidar._serial_port.write(b'\xA5\x20')
    lidar._serial_port.flush()
    time.sleep(0.3)
    
    # Read descriptor
    descriptor = lidar._serial_port.read(7)
    if len(descriptor) != 7 or descriptor[0:2] != b'\xA5\x5A':
        print("Error: Invalid scan descriptor")
        return
    
    start_time = time.time()
    scan_count = 0
    measurement_count = 0
    distances = []
    current_scan_dists = []
    
    try:
        while time.time() - start_time < duration:
            data = lidar._serial_port.read(5)
            
            if len(data) != 5:
                break
            
            measurement_count += 1
            
            # Parse measurement
            byte0 = data[0]
            start_flag = (byte0 & 0x01) != 0
            
            distance_raw = struct.unpack('<H', data[3:5])[0]
            distance = distance_raw / 4.0
            
            if distance > 0:
                current_scan_dists.append(distance)
                distances.append(distance)
            
            # new_scan is True at the start of each 360° rotation
            if start_flag and measurement_count > 0:
                scan_count += 1
                # Print statistics every 5 scans
                if scan_count % 5 == 0 and current_scan_dists:
                    print(f"Scan #{scan_count}: "
                          f"Min: {min(current_scan_dists):.0f}mm | "
                          f"Max: {max(current_scan_dists):.0f}mm | "
                          f"Avg: {sum(current_scan_dists)/len(current_scan_dists):.0f}mm")
                current_scan_dists = []
        
        elapsed = time.time() - start_time
        print(f"\n=== Statistics ===")
        print(f"Total scans: {scan_count}")
        print(f"Total measurements: {measurement_count}")
        print(f"Average measurements per scan: {measurement_count/scan_count:.1f}" if scan_count > 0 else "N/A")
        print(f"Scan rate: {scan_count/elapsed:.1f} Hz" if elapsed > 0 else "N/A")
        if distances:
            print(f"Distance range: {min(distances):.0f}mm - {max(distances):.0f}mm")
        
        # Stop scan
        lidar._serial_port.write(b'\xA5\x25')
        time.sleep(0.2)
        
    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user")
    except Exception as e:
        print(f"Error during monitoring: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run RPLidar tests"""
    print("=" * 60)
    print("RPLidar A1M8 Basic Test Script")
    print("=" * 60)
    
    # Allow custom port via command line
    port = PORT_NAME
    if len(sys.argv) > 1:
        port = sys.argv[1]
    
    print(f"\nAttempting to connect to RPLidar on port: {port}")
    print("(Use Ctrl+C to stop at any time)")
    
    try:
        # Connect to the RPLidar
        lidar = RPLidar(port)
        print("✓ Successfully connected to RPLidar!")
        
        # Test 1: Get device information
        if not test_device_info(lidar):
            print("Failed to get device info. Exiting.")
            lidar.stop()
            lidar.disconnect()
            return
        
        # Test 2: Basic scan test
        input("\nPress Enter to start basic scan test (or Ctrl+C to skip)...")
        basic_scan_test(lidar, num_measurements=50)
        
        # Test 3: Continuous monitoring
        input("\nPress Enter to start continuous monitoring (or Ctrl+C to skip)...")
        continuous_monitoring(lidar, duration=10)
        
        # Cleanup
        print("\n=== Stopping LiDAR ===")
        lidar.stop()
        lidar.stop_motor()
        lidar.disconnect()
        print("✓ Disconnected successfully")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check that the RPLidar is connected via USB")
        print("2. Verify the correct port (default: /dev/ttyUSB0)")
        print("   - List available ports: ls /dev/ttyUSB* or ls /dev/ttyACM*")
        print("3. Ensure you have permission to access the port:")
        print("   sudo chmod 666 /dev/ttyUSB0")
        print("   or add your user to dialout group: sudo usermod -a -G dialout $USER")
        print("4. Make sure rplidar library is installed: pip install rplidar")
        return 1
    
    print("\n✓ All tests completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
