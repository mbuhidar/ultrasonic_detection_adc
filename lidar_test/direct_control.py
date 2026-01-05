#!/usr/bin/env python3
"""
RPLidar A1M8 - Direct motor control then scan
Completely bypass library's motor methods
"""

import serial
import time
import sys
import struct

PORT = '/dev/ttyUSB0'
BAUDRATE = 115200

def start_scan_direct(ser):
    """Start scan using raw serial commands"""
    print("Sending SCAN command...")
    ser.write(b'\xA5\x20')
    ser.flush()
    time.sleep(0.2)
    
    # Read descriptor
    descriptor = ser.read(7)
    if len(descriptor) != 7:
        raise Exception(f"Descriptor incomplete: {len(descriptor)} bytes")
    
    if descriptor[0:2] != b'\xA5\x5A':
        raise Exception(f"Invalid descriptor: {descriptor.hex()}")
    
    length_val = struct.unpack('<I', descriptor[2:6])[0]
    response_len = length_val & 0x3FFFFFFF
    
    if response_len != 5:
        raise Exception(f"Unexpected response length: {response_len}")
    
    print("✓ Scan started successfully")
    return True

def read_scans(ser, num_scans=10):
    """Read and parse scan data"""
    print(f"\nReading {num_scans} scans...\n")
    
    scan_num = 0
    point_count = 0
    current_scan_points = []
    
    while scan_num < num_scans:
        data = ser.read(5)
        
        if len(data) != 5:
            print(f"✗ Incomplete data: {len(data)} bytes")
            break
        
        # Parse measurement
        byte0 = data[0]
        start_flag = (byte0 & 0x01) != 0
        quality = (byte0 >> 2) & 0x3F
        
        angle_raw = struct.unpack('<H', data[1:3])[0]
        angle = (angle_raw >> 1) / 64.0
        
        distance_raw = struct.unpack('<H', data[3:5])[0]
        distance = distance_raw / 4.0
        
        if start_flag and len(current_scan_points) > 0:
            # Complete scan collected
            scan_num += 1
            distances = [p[2] for p in current_scan_points if p[2] > 0]
            angles = [p[1] for p in current_scan_points]
            
            if distances:
                print(f"Scan #{scan_num}:")
                print(f"  Points: {len(current_scan_points)}")
                print(f"  Angles: {min(angles):.1f}° - {max(angles):.1f}°")
                print(f"  Distances: {min(distances):.0f}mm - {max(distances):.0f}mm")
                print(f"  Average: {sum(distances)/len(distances):.0f}mm")
                print()
            
            current_scan_points = []
        
        current_scan_points.append((quality, angle, distance))
    
    return scan_num

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else PORT
    
    print("=" * 60)
    print("RPLidar A1M8 - Direct Serial Control")
    print("=" * 60)
    
    try:
        print(f"\nOpening {port}...")
        ser = serial.Serial(port, BAUDRATE, timeout=1, dsrdtr=True)
        print("✓ Port opened")
        
        # Clear buffers
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.5)
        
        # Test communication with GET_INFO
        print("\nTesting communication...")
        ser.write(b'\xA5\x50')
        time.sleep(0.2)
        descriptor = ser.read(7)
        if len(descriptor) == 7:
            data_len = struct.unpack('<I', descriptor[2:6])[0] & 0x3FFFFFFF
            info_data = ser.read(data_len)
            print("✓ Communication OK")
        
        # Send STOP to ensure clean state
        print("\nSending STOP command...")
        ser.write(b'\xA5\x25')
        time.sleep(0.5)
        ser.reset_input_buffer()
        
        # START MOTOR using DTR
        print("\n" + "=" * 60)
        print("Starting Motor")
        print("=" * 60)
        
        print("\nMethod 1: DTR=True")
        ser.setDTR(True)
        print("  Waiting 2 seconds...")
        time.sleep(2)
        motor_spinning = input("  Is motor spinning? (yes/no): ").strip().lower()
        
        if motor_spinning != 'yes':
            print("\nMethod 2: DTR=False")
            ser.setDTR(False)
            print("  Waiting 2 seconds...")
            time.sleep(2)
            motor_spinning = input("  Is motor spinning? (yes/no): ").strip().lower()
            
            if motor_spinning != 'yes':
                print("\nMethod 3: RTS=True")
                ser.setRTS(True)
                print("  Waiting 2 seconds...")
                time.sleep(2)
                motor_spinning = input("  Is motor spinning? (yes/no): ").strip().lower()
                
                if motor_spinning != 'yes':
                    print("\n✗ Motor not spinning with any method!")
                    print("\nYour device may:")
                    print("1. Require external 5V power to motor pins")
                    print("2. Use a different control method")
                    print("3. Have a hardware issue")
                    ser.close()
                    return 1
        
        print("\n✓ Motor is spinning!")
        
        # Wait for motor to stabilize
        print("\nWaiting 3 more seconds for stabilization...")
        time.sleep(3)
        
        # Clear any startup data
        ser.reset_input_buffer()
        time.sleep(0.2)
        
        # Start scanning
        print("\n" + "=" * 60)
        print("Scanning")
        print("=" * 60)
        
        start_scan_direct(ser)
        scans_read = read_scans(ser, 10)
        
        if scans_read > 0:
            print(f"✓ Successfully read {scans_read} scans!")
        
        # Stop
        print("\n" + "=" * 60)
        print("Stopping")
        print("=" * 60)
        
        ser.write(b'\xA5\x25')
        time.sleep(0.2)
        
        ser.setDTR(False)
        ser.setRTS(False)
        
        ser.close()
        print("✓ Done!")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        try:
            ser.write(b'\xA5\x25')
            ser.setDTR(False)
            ser.close()
        except:
            pass
        return 1
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
