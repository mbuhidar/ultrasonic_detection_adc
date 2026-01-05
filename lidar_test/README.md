# RPLidar A1M8 Test Setup

Successfully configured tools for testing and visualizing data from an RPLidar A1M8 sensor.

## Solution Summary

This RPLidar A1M8 requires **DTR=False** to spin the motor and needs **3 seconds of stabilization time** before scanning. The scripts handle motor control and timing correctly by:
1. Setting DTR=False to start the motor
2. Waiting 3+ seconds for full spin-up
3. Clearing serial buffers
4. Sending SCAN command directly
5. Reading raw scan data from the serial port

## Hardware Requirements

- RPLidar A1M8 sensor
- USB connection to your computer
- 5V power supply (via USB)

## Software Requirements

- Python 3.7 or higher
- USB serial port access

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Check your LiDAR connection:**
   ```bash
   # List USB devices to find your LiDAR
   ls /dev/ttyUSB*
   # or
   ls /dev/ttyACM*
   ```

3. **Set permissions (if needed):**
   ```bash
   # Option 1: Temporary permission for current session
   sudo chmod 666 /dev/ttyUSB0
   
   # Option 2: Add your user to dialout group (permanent, requires logout)
   sudo usermod -a -G dialout $USER
   ```

## Usage

### Basic Test Script

Run the basic test to verify connection and get sample readings:

```bash
python basic_test.py
```

Or specify a custom port:
```bash
python basic_test.py /dev/ttyUSB0
```

**What it does:**
- Connects to the RPLidar
- Displays device information (model, firmware, serial number)
- Starts motor and waits for stabilization
- Collects 50 measurements showing angle, distance, and quality data
- Runs continuous monitoring with statistics for 10 seconds

### Visualization Script

For real-time 2D visualization of LiDAR data:

```bash
python visualize.py
```

Or with a custom port:
```bash
python visualize.py /dev/ttyUSB0
```

**What it does:**
- Opens a polar plot showing real-time scan data
- Displays distance measurements around 360 degrees
- Updates in real-time as the LiDAR scans
- Shows scan statistics (min, max, average distances)

Close the plot window to stop the visualization.

### Direct Control Script

For low-level testing and diagnostics:

```bash
python direct_control.py
```

**What it does:**
- Provides interactive motor control testing
- Sends raw serial commands directly
- Useful for troubleshooting and understanding the device protocol

## Understanding the Output

### Data Format
Each LiDAR measurement consists of:
- **Quality**: Signal quality (0-63, higher is better)
- **Angle**: Direction in degrees (0-360)
- **Distance**: Range in millimeters

### Specifications (A1M8)
- Range: 0.15m - 12m
- Scan Rate: ~5 Hz (5 rotations per second)
- Points per scan: ~260-270
- Angular Resolution: ~1.3 degrees

## Troubleshooting

### Common Issues

1. **"Permission denied" error:**
   - Run: `sudo chmod 666 /dev/ttyUSB0`
   - Or add user to dialout group: `sudo usermod -a -G dialout $USER` (requires logout/login)

2. **"Device not found" error:**
   - Check USB connection
   - Verify port with `ls /dev/ttyUSB*`
   - Try different USB ports

3. **Motor not spinning:**
   - Ensure adequate USB power (use USB 2.0/3.0 port directly on PC)
   - Check USB cable supports both data and power (not charge-only)
   - Device confirmed to work with DTR=False

4. **No data or "Wrong body size" error:**
   - This usually means motor isn't fully stabilized
   - Scripts include 3-second stabilization delay
   - If issue persists, try power cycling the device

## File Descriptions

- **basic_test.py**: Command-line test script with scan data output
- **visualize.py**: Real-time 2D polar visualization
- **direct_control.py**: Low-level diagnostic and testing tool
- **requirements.txt**: Python package dependencies
- **README.md**: This file

## Next Steps

Once you verify basic functionality, you can:
- Save scan data to files for analysis
- Implement obstacle detection algorithms
- Create 3D visualizations
- Integrate with ROS (Robot Operating System)
- Build SLAM (Simultaneous Localization and Mapping) applications

## Resources

- [RPLidar SDK Documentation](https://github.com/Slamtec/rplidar_sdk)
- [rplidar Python Library](https://github.com/SkoltechRobotics/rplidar)
- [RPLidar A1M8 Datasheet](https://www.slamtec.com/en/Lidar/A1)

## License

These scripts are provided as-is for testing purposes.
