# RPLIDAR Integration Setup (Optional)

**⚠️ IMPORTANT: RPLIDAR is OPTIONAL and only needed for ML training with ground truth position labels.**

If you only want to collect echo profile data without position labels, you can skip this entire setup and use the basic `data_collector.py` script instead.

## When Do You Need RPLIDAR?

**You need RPLIDAR if:**
- You want to train ML models with labeled position data
- You need (x, y) coordinates for detected objects
- You want to correlate echo patterns with precise object locations

**You DON'T need RPLIDAR if:**
- You only want to collect raw echo profile data
- You're doing basic distance measurement or object detection
- You're analyzing echo patterns without position labels
- You're just getting started with the system

---

## Hardware Requirements

- **RPLIDAR A1M8** (recommended, ~$100) or A2M8 (~$320)
- USB-to-Serial adapter (CP2102 or similar, usually included with RPLIDAR)
- 5V power supply (500mA minimum for A1, external recommended)
- Mounting hardware for positioning at center of platform

## USB Connection Overview

Both the Arduino and RPLIDAR connect to separate USB ports on the Orange Pi:

```
Orange Pi 5
├── USB Port 1 → Arduino Uno (USB-A to USB-B cable)
│   └── /dev/ttyACM0
│
└── USB Port 2 → RPLIDAR A1 (USB-to-Serial adapter)
    └── /dev/ttyUSB0
```

### Arduino Uno Connection
- **Cable**: Standard USB-A to USB-B cable (printer-style cable)
- **Arduino side**: USB-B port on Arduino Uno board
- **Orange Pi side**: Any USB-A port (USB 2.0 or 3.0)
- **Device name**: `/dev/ttyACM0` (or `/dev/ttyACM1`)
- **Power**: Arduino powered via USB from Orange Pi (draws ~200mA)

### RPLIDAR Connection
- **Adapter**: USB-to-Serial adapter (CP2102, usually included with RPLIDAR)
- **RPLIDAR side**: 4-pin connector → Adapter wires
- **Orange Pi side**: USB-A port (adapter's USB connector)
- **Device name**: `/dev/ttyUSB0` (or `/dev/ttyUSB1`)
- **Power**: Motor requires external 5V supply (500mA), USB only for data

### Identifying Devices

```bash
# List all USB serial devices
ls -l /dev/tty{ACM,USB}*

# Expected output:
# /dev/ttyACM0  ← Arduino Uno
# /dev/ttyUSB0  ← RPLIDAR

# More detailed info
dmesg | tail -20
# Look for:
# "Arduino Uno" or "ttyACM0: USB ACM device"
# "CP210x" or "ttyUSB0: USB Serial converter"
```

## Physical Setup

### 1. RPLIDAR Mounting

Mount the RPLIDAR at the **center (0, 0)** of your rectangular platform:

```
Platform dimensions: 29.5" × 52.36" (74.93cm × 132.99cm)

         Front (short edge)
    ┌─────────────────────────┐
    │  S1                  S2 │  ← Ultrasonic sensors on front edge
    │                         │
    │          [LIDAR]        │  ← Center of platform (0, 0)
    │           (0,0)         │
    │                         │
    │                         │
    └─────────────────────────┘
         Back (short edge)
```

**Coordinate System:**

**Hardware Coordinates (RPLIDAR-centered):**
- **Origin (0, 0)**: RPLIDAR at center of platform
- **X-axis**: Left (-) to Right (+)
- **Y-axis**: Back (-) to Front (+)
- **Front edge**: Y = +66.5cm (half of 132.99cm length)
- **0° reference**: Points toward front of platform

**Training Data Coordinates (Front-line-relative):**
- **Origin (0, 0)**: Center of front edge
- **X-axis**: Left (-) to Right (+), same as hardware
- **Y-axis**: Distance in front of the platform (always ≥ 0)
  - 0 = at front edge
  - Positive values = forward distance from edge
- **Transformation**: `x_train = x_rplidar`, `y_train = y_rplidar - 66.5`

**Data Filtering:**
- Only RPLIDAR points with Y > 66.5cm (in front of platform) are included
- From filtered points, the one **nearest to the front line** is selected
- This gives you the closest object position in front of your sensors

### 2. RPLIDAR Wiring

**Detailed Connection Diagram:**

```
RPLIDAR 4-pin Connector    USB-to-Serial Adapter (CP2102)
───────────────────────    ──────────────────────────────
Pin 1 (GND)  black     →   GND (black wire)
Pin 2 (5V)   red       →   5V External Supply (500mA min)
Pin 3 (TX)   green     →   RX (white wire)
Pin 4 (RX)   white     →   TX (green wire)
Pin 5 (PWM)  yellow    →   (not connected, full speed)

                           USB Connector
                                │
                                │
                                ▼
                        Orange Pi USB Port
                        (any USB 2.0/3.0 port)
                        → /dev/ttyUSB0
```

**Power Setup:**

```
External 5V Power Supply
(500mA minimum, 1A recommended)
        │
        ├─→ 5V (red wire) → RPLIDAR Pin 2
        └─→ GND (black wire) → RPLIDAR Pin 1
                               (also connect to adapter GND)
```

**Important Power Notes:**
- **DO NOT** power RPLIDAR motor from USB adapter's 5V pin
- USB data pins cannot provide enough current (500mA needed)
- Motor stall or unreliable operation will occur without external power
- Use a dedicated 5V power supply or powered USB hub
- Ground must be common between RPLIDAR, adapter, and Orange Pi

### 3. Complete System Wiring

```
┌─────────────────────────────────────────────────────┐
│                    Orange Pi 5                       │
│                                                      │
│  USB Port 1  ←─── USB-A to USB-B ───→ Arduino Uno  │
│  /dev/ttyACM0                                       │
│                                                      │
│  USB Port 2  ←─── USB-to-Serial ────→ RPLIDAR A1   │
│  /dev/ttyUSB0        Adapter                        │
│                                                      │
└─────────────────────────────────────────────────────┘

Arduino Uno                          RPLIDAR A1
    │                                    │
    │ D2 ──────→ Sensor Chain           │ 4-pin connector
    │ A0 ←────── Sensor 1 PW             │  ├── Pin 1 (GND)
    │ A1 ←────── Sensor 2 PW             │  ├── Pin 2 (5V) ←─── External 5V
    │                                    │  ├── Pin 3 (TX)
    └── USB-B ──→ Orange Pi              │  └── Pin 4 (RX)
                                         │
                                    USB Adapter
                                    └── USB-A ──→ Orange Pi
```

### 4. Connect to Orange Pi

```bash
# Plug in Arduino first
ls -l /dev/ttyACM0
# Should show: crw-rw---- 1 root dialout ... /dev/ttyACM0

# Plug in RPLIDAR with external power
ls -l /dev/ttyUSB0
# Should show: crw-rw---- 1 root dialout ... /dev/ttyUSB0

# If you see permission errors, add user to dialout group
sudo usermod -a -G dialout $USER
# Then logout and login
```

## Software Setup

### 1. Install RPLIDAR Python Library

```bash
cd ~/Code/mbuhidar/ultrasonic_detection_adc/orangepi

# If using virtual environment
source venv/bin/activate

# Install rplidar library
pip install rplidar-roboticia
```

### 2. Test RPLIDAR Connection

```bash
# Simple test script
python3 << 'EOF'
from rplidar import RPLidar

print("Testing RPLIDAR connection...")
lidar = RPLidar('/dev/ttyUSB0')

print("\nRPLIDAR Info:")
info = lidar.get_info()
for key, value in info.items():
    print(f"  {key}: {value}")

print("\nRPLIDAR Health:")
health = lidar.get_health()
print(f"  Status: {health[0]}")
print(f"  Error code: {health[1]}")

lidar.disconnect()
print("\n✓ RPLIDAR working!")
EOF
```

**Expected output:**
```
RPLIDAR Info:
  model: 24
  firmware: (1, 29)
  hardware: 7
  serialnumber: ...

RPLIDAR Health:
  Status: Good
  Error code: 0

✓ RPLIDAR working!
```

### 3. Test Both Devices

```bash
# Terminal 1: Check Arduino data
cat /dev/ttyACM0
# Should see: S,timestamp,readings... scrolling

# Terminal 2: Check RPLIDAR data
python3 -c "from rplidar import RPLidar; [print(f'Scan: {len(s)} points') for s in RPLidar('/dev/ttyUSB0').iter_scans()]"
# Should see: Scan: XXX points (repeating)
```

### 4. Configure Sensor Positions

The `config.yaml` file already has the correct positions for your platform layout:

```yaml
# Platform dimensions (cm)
sensor_positions:
  front_line_y: 66.5  # Distance from RPLIDAR (0,0) to front edge

  sensor_1:
    x: -37.47         # Left corner of front edge
    y: 66.5           # At front edge
    angle: 30         # Pointing inward-right (30°)
  
  sensor_2:
    x: 37.47          # Right corner of front edge
    y: 66.5           # At front edge
    angle: 150        # Pointing inward-left (150°)
```

**No changes needed** unless you modify your physical layout!

## Usage

### Basic Synchronized Data Collection

```bash
cd ~/Code/mbuhidar/ultrasonic_detection_adc/orangepi

# Collect for 60 seconds (default)
python data_collector_with_lidar.py

# Collect for 120 seconds
python data_collector_with_lidar.py --duration 120

# Infinite collection (Ctrl+C to stop)
python data_collector_with_lidar.py --duration 0

# Custom config file
python data_collector_with_lidar.py --config my_config.yaml --duration 120
```

### Output Format

Training data CSV format:
```csv
system_timestamp,arduino_timestamp_ms,sensor_id,
echo_r1,echo_r2,...,echo_r240,
lidar_x,lidar_y,lidar_quality,lidar_distance,num_objects

1735423200.123,45000,1,
3,4,5,...,200,
75.3,45.2,15,89.5,3
```

**Columns:**
- `system_timestamp`: Unix timestamp from Orange Pi (seconds)
- `arduino_timestamp_ms`: Arduino millis() value
- `sensor_id`: Which ultrasonic sensor (1, 2, ...)
- `echo_r1` to `echo_r240`: Echo amplitude profile (0-1023 ADC values)
- `lidar_x`: Object X position (cm) relative to front line center (- = left, + = right)
- `lidar_y`: Object Y position (cm) in front of box (0 = front edge, + = forward)
- `lidar_quality`: RPLIDAR signal quality (0-15, higher is better)
- `lidar_distance`: Distance to object from RPLIDAR (cm)
- `num_objects`: Total objects detected in LIDAR scan

**Position Data Notes:**
- Only objects **in front of the box** (Y > 66.5cm from RPLIDAR) are captured
- Position is the **nearest point to the front line** (minimum Y value from filtered points)
- Coordinates are **front-line-relative**: (0,0) is center of front edge
- All Y values in training data are ≥ 0 (0 = at front line, positive = forward distance)

### Data Collection Tips

1. **Move objects through the field**: Walk around, wave hands, move objects at different distances
2. **Cover the full range**: 30cm to 2m for ultrasonics
3. **Vary speeds**: Slow and fast movement
4. **Multiple positions**: Different angles and orientations
5. **Collect 5-10 minutes**: Aim for 1000+ training samples

## Coordinate System Calibration

### Understanding the Coordinate Systems

**Hardware Coordinates (RPLIDAR-centered):**
- Origin: RPLIDAR center (middle of box)
- X-axis: Left (-) to Right (+)
- Y-axis: Back (-) to Front (+)
- Front edge is at Y = +66.5cm

**Training Data Coordinates (Front-line-relative):**
- Origin: Center of front edge
- X-axis: Left (-) to Right (+), same as hardware
- Y-axis: Distance in front of box (0 = front edge, positive values forward)
- Transformation: `x_train = x_rplidar`, `y_train = y_rplidar - 66.5`
- Only points with `y_rplidar > 66.5` are included

### Quick Calibration Method

1. **Place marker object** in front of the box at known position:
   ```
   Example: 50cm forward from front edge, centered
   Expected training coordinates: (x=0, y=50)
   ```

2. **Run test collection:**
   ```bash
   python data_collector_with_lidar.py --duration 10
   ```

3. **Check output CSV:**
   ```bash
   # View LIDAR positions
   tail -20 data/training_data_*.csv | cut -d',' -f244-248
   ```

4. **Verify positions**:
   - `lidar_x` should be near 0 cm (centered)
   - `lidar_y` should be near 50 cm (distance from front)
   - If incorrect, check `front_line_y` setting in config.yaml

### Verification Script

```bash
# Quick verification of sensor-LIDAR alignment
python3 << 'EOF'
import pandas as pd
import glob

# Find latest training file
files = sorted(glob.glob('data/training_data_*.csv'))
if not files:
    print("No training data files found")
    exit(1)

df = pd.read_csv(files[-1])

print(f"File: {files[-1]}")
print(f"\nTotal samples: {len(df)}")
print(f"Samples with LIDAR data: {df['lidar_x'].notna().sum()}")

if df['lidar_x'].notna().sum() > 0:
    print(f"\nLIDAR position range:")
    print(f"  X: {df['lidar_x'].min():.1f} to {df['lidar_x'].max():.1f} cm")
    print(f"  Y: {df['lidar_y'].min():.1f} to {df['lidar_y'].max():.1f} cm")
    print(f"  Distance: {df['lidar_distance'].min():.1f} to {df['lidar_distance'].max():.1f} cm")
else:
    print("\n⚠ No LIDAR data found - check RPLIDAR connection")
EOF
```

## Troubleshooting

### RPLIDAR Not Detected

```bash
# Check USB connection
lsusb | grep -i CP210

# Check device file
ls -l /dev/ttyUSB*

# If permission denied, add user to dialout group
sudo usermod -a -G dialout $USER
# Then logout and login

# Or temporarily fix permissions
sudo chmod 666 /dev/ttyUSB0
```

### Arduino Not Detected

```bash
# Check USB connection
lsusb | grep -i Arduino

# Check device file
ls -l /dev/ttyACM*

# Fix permissions
sudo chmod 666 /dev/ttyACM0
```

### Motor Not Spinning

```bash
# Check if motor is getting power
# Motor should spin when RPLIDAR is connected

# Test motor control
python3 << 'EOF'
from rplidar import RPLidar
import time

print("Testing RPLIDAR motor...")
lidar = RPLidar('/dev/ttyUSB0')
lidar.start_motor()
print("Motor should be spinning now - listen for sound")
time.sleep(5)
lidar.stop_motor()
lidar.disconnect()
print("✓ Motor test complete")
EOF
```

**If motor doesn't spin:**
1. Check external 5V power supply is connected
2. Verify 500mA minimum current capacity
3. Check GND connection between power supply and RPLIDAR
4. Try different power supply

### Poor Synchronization (Low Match Rate)

If match rate is < 80%:

1. **Increase sync window:**
   ```yaml
   sync:
     window_ms: 100  # Increase from 50ms to 100ms
   ```

2. **Check timing alignment:**
   - Arduino cycle: ~120ms per sensor pair
   - RPLIDAR A1: 180ms per scan (5.5Hz)
   - RPLIDAR A2: 100ms per scan (10Hz)
   - Should get 4-5 ultrasonic samples per LIDAR scan

3. **Verify both systems running:**
   ```bash
   # Check Arduino output (separate terminal)
   cat /dev/ttyACM0  # Should see "S,..." lines scrolling
   
   # Check RPLIDAR output (separate terminal)
   python3 -c "from rplidar import RPLidar; [print(f'Scan: {len(s)} points') for s in RPLidar('/dev/ttyUSB0').iter_scans()]"
   ```

4. **Check for dropped data:**
   - Monitor queue sizes in progress reports
   - If queues fill up (>150), system is overloaded
   - Try closing other programs

### Device Names Swap on Reboot

If `/dev/ttyACM0` and `/dev/ttyUSB0` swap positions:

```bash
# Check which is which
udevadm info /dev/ttyACM0 | grep ID_MODEL
udevadm info /dev/ttyUSB0 | grep ID_MODEL

# Update config.yaml with correct ports
nano config.yaml
```

### No LIDAR Data in Output

Check detection range:
- **RPLIDAR A1**: 15cm to 12m range
- **MB1300**: 30cm to 5m range
- **Overlap**: Place objects 50cm-2m away for best results

```bash
# Test LIDAR detection
python3 << 'EOF'
from rplidar import RPLidar
import time

lidar = RPLidar('/dev/ttyUSB0')
print("Scanning for 5 seconds...")
start = time.time()

for scan in lidar.iter_scans():
    if time.time() - start > 5:
        break
    points = len(scan)
    valid = sum(1 for q, a, d in scan if q > 0 and d > 0)
    print(f"Scan: {points} total points, {valid} valid detections")

lidar.stop()
lidar.disconnect()
EOF
```

### Permission Issues

If getting permission errors:

```bash
# Add yourself to dialout group (permanent fix)
sudo usermod -a -G dialout $USER

# Apply immediately (or logout/login)
newgrp dialout

# Verify group membership
groups | grep dialout
```

## Performance Notes

- **RPLIDAR scan rate**: 
  - A1: 5.5Hz → new data every 180ms
  - A2: 10Hz → new data every 100ms
- **Ultrasonic cycle**: ~120ms per sensor pair
- **Expected match rate**: 80-95% (depends on timing)
- **Data rate**: 5-10 training samples/second
- **Storage**: ~2KB per sample → 10-20KB/sec

## Next Steps

After successful setup:

1. ✅ **Collect training data** with objects at various positions
2. ✅ **Verify data quality** using verification script above
3. ✅ **Visualize echo profiles** using `echo_analyzer.py`
4. ✅ **Train ML model** using synchronized dataset
5. ✅ **Deploy model** for real-time position prediction

See the main [README.md](README.md) for complete system documentation and ML training workflow.

## Tips for Best Results

1. **Calibrate coordinate system** before large data collection
2. **Label different scenarios**: Note when collecting (walking, stationary, multiple objects)
3. **Maintain consistent environment**: Same mounting, lighting, temperature
4. **Collect diverse data**: Different heights, speeds, materials
5. **Monitor match rate**: Aim for >85% for good training data
6. **Regular verification**: Check output files periodically during collection

## Hardware Recommendations

For best ML training results:

- **RPLIDAR A1**: Great balance of cost/performance (~$100)
- **RPLIDAR A2**: Better for fast movement (10Hz, ~$320)
- **Mount height**: 2-2.5m above ground for good coverage
- **Sensor spacing**: 20-40cm apart for overlapping fields
- **Clear field of view**: Minimize obstructions between RPLIDAR and detection area
