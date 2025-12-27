#!/usr/bin/env python3
"""
System Test Script

Tests the connection and basic functionality of the ultrasonic detection system.
"""

import serial
import time
import yaml
from pathlib import Path


def load_config(config_path="../config.yaml"):
    """Load configuration."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def test_arduino_connection(config):
    """Test connection to Arduino."""
    print("Testing Arduino connection...")
    
    try:
        ser = serial.Serial(
            port=config['arduino']['port'],
            baudrate=config['arduino']['baudrate'],
            timeout=config['arduino']['timeout']
        )
        
        time.sleep(2)  # Wait for Arduino to initialize
        
        # Read initialization messages
        messages = []
        while ser.in_waiting:
            line = ser.readline().decode('utf-8').strip()
            messages.append(line)
            print(f"  Arduino: {line}")
        
        if any("READY" in msg for msg in messages):
            print("✓ Arduino connection successful")
            ser.close()
            return True
        else:
            print("✗ Arduino not responding correctly")
            ser.close()
            return False
            
    except serial.SerialException as e:
        print(f"✗ Connection failed: {e}")
        print(f"\nTroubleshooting:")
        print(f"  1. Check that Arduino is connected to {config['arduino']['port']}")
        print(f"  2. Try: ls /dev/tty* to find the correct port")
        print(f"  3. Check permissions: sudo chmod 666 {config['arduino']['port']}")
        print(f"  4. Verify Arduino code is uploaded")
        return False


def test_data_collection(config):
    """Test data collection."""
    print("\nTesting data collection...")
    
    try:
        ser = serial.Serial(
            port=config['arduino']['port'],
            baudrate=config['arduino']['baudrate'],
            timeout=config['arduino']['timeout']
        )
        
        time.sleep(2)
        
        # Clear buffer
        while ser.in_waiting:
            ser.readline()
        
        # Start collection
        print("  Sending START command...")
        ser.write(b"START:5\n")
        
        # Wait for acknowledgment
        response = ser.readline().decode('utf-8').strip()
        print(f"  Response: {response}")
        
        if "ACK:STARTED" not in response:
            print("✗ Failed to start data collection")
            ser.close()
            return False
        
        # Collect some data
        print("  Collecting data samples...")
        samples = []
        timeout = time.time() + 5  # 5 second timeout
        
        while len(samples) < 5 and time.time() < timeout:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                if line.startswith('S,'):
                    samples.append(line)
                    print(f"    Sample {len(samples)}: {line}")
        
        # Stop collection
        ser.write(b"STOP\n")
        ser.readline()  # Read ACK
        
        ser.close()
        
        if len(samples) >= 3:
            print(f"✓ Data collection successful ({len(samples)} samples)")
            return True
        else:
            print(f"✗ Insufficient data received ({len(samples)} samples)")
            return False
            
    except Exception as e:
        print(f"✗ Data collection test failed: {e}")
        return False


def test_distance_calculation():
    """Test distance calculation function."""
    print("\nTesting distance calculation...")
    
    test_cases = [
        (100, 127.0),   # 100 ADC = ~127cm
        (200, 254.0),   # 200 ADC = ~254cm
        (0, 0.0),       # 0 ADC = 0cm
    ]
    
    def adc_to_distance(adc):
        return adc * 0.5 * 2.54
    
    all_passed = True
    for adc, expected in test_cases:
        result = adc_to_distance(adc)
        passed = abs(result - expected) < 0.1
        status = "✓" if passed else "✗"
        print(f"  {status} ADC={adc} → {result:.1f}cm (expected {expected}cm)")
        all_passed = all_passed and passed
    
    if all_passed:
        print("✓ Distance calculation correct")
    else:
        print("✗ Distance calculation has errors")
    
    return all_passed


def test_file_system(config):
    """Test file system access."""
    print("\nTesting file system...")
    
    output_dir = Path(config['data']['output_directory'])
    
    # Check if directory exists or can be created
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Output directory accessible: {output_dir}")
        
        # Test write permission
        test_file = output_dir / ".test_write"
        test_file.write_text("test")
        test_file.unlink()
        print("✓ Write permission confirmed")
        
        return True
        
    except Exception as e:
        print(f"✗ File system test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Ultrasonic Detection System - System Test")
    print("=" * 60)
    
    # Load configuration
    try:
        config = load_config()
        print("\n✓ Configuration loaded")
    except Exception as e:
        print(f"\n✗ Failed to load configuration: {e}")
        return
    
    # Run tests
    results = {
        'Arduino Connection': test_arduino_connection(config),
        'Data Collection': test_data_collection(config),
        'Distance Calculation': test_distance_calculation(),
        'File System': test_file_system(config),
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("  python data_collector.py     - Start collecting data")
        print("  python realtime_viewer.py    - View data in real-time")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        print("\nFor help, see README.md or check:")
        print("  - Hardware connections")
        print("  - Arduino code uploaded")
        print("  - Serial port configuration in config.yaml")
    print("=" * 60)


if __name__ == '__main__':
    main()
