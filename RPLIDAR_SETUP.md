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
- USB-to-Serial adapter (usually included with RPLIDAR)
- 5V power supply (500mA minimum for A1)
- Mounting hardware for positioning above sensor array

## Physical Setup

### 1. RPLIDAR Mounting

Mount the RPLIDAR at the center of your ultrasonic sensor array, typically overhead or ceiling-mounted:

```
        [RPLIDAR]  ← Ceiling/overhead mount
           (0,0)     Center of coordinate system
            
    [-15cm] [+15cm]
      S1        S2    ← Ultrasonic sensors below
```

**Coordinate System:**
- **Origin (0, 0)**: RPLIDAR center
- **X-axis**: Left (-) to Right (+)
- **Y-axis**: Back (-) to Forward (+)
- **Z-axis**: Down (-) to Up (+)
- **Angles**: 0° = Right, 90° = Forward, 180° = Left, 270° = Back

### 2. RPLIDAR Connections

**RPLIDAR → USB Adapter → Orange Pi:**

```
RPLIDAR Connector        USB-Serial Adapter
─────────────────        ──────────────────
Pin 1 (GND, black)   →   GND
Pin 2 (5V, red)      →   5V (external supply recommended)
Pin 3 (TX, green)    →   RX
Pin 4 (RX, white)    →   TX
Pin 5 (Motor PWM)    →   (leave disconnected for full speed)
```

**Power Options:**
1. **External 5V supply** (recommended for A1): 500mA minimum
2. **Powered USB hub**: Ensure adequate current capacity
3. **Orange Pi USB**: May work but check power budget

### 3. Connect to Orange Pi

Plug the USB-Serial adapter into the Orange Pi:

```bash
# Check which port RPLIDAR is on
ls -l /dev/ttyUSB*

# Expected output: /dev/ttyUSB0 (or ttyUSB1, etc.)
# Update config.yaml if different
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

### 3. Configure Sensor Positions

Edit `config.yaml` to match your physical sensor layout:

```yaml
# Update these coordinates to match your actual setup
sensor_positions:
  sensor_1:
    x: -15      # 15cm left of RPLIDAR
    y: 0        # Same front/back position
    angle: 90   # Facing forward
    fov: 60     # 60° field of view
  
  sensor_2:
    x: 15       # 15cm right of RPLIDAR
    y: 0
    angle: 90
    fov: 60
```

**Measuring Your Layout:**

1. **Mount RPLIDAR** at center of your detection area
2. **Mark origin**: RPLIDAR position = (0, 0)
3. **Measure sensor offsets**: 
   - X: Left/right from RPLIDAR (cm)
   - Y: Forward/back from RPLIDAR (cm)
4. **Determine sensor orientation**:
   - 0° = pointing right
   - 90° = pointing forward
   - 180° = pointing left
   - 270° = pointing back
5. **Estimate FOV**: MB1300 typically has ~60° beam width

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
- `lidar_x`: Object X position in cm from RPLIDAR
- `lidar_y`: Object Y position in cm from RPLIDAR
- `lidar_quality`: RPLIDAR signal quality (0-15, higher is better)
- `lidar_distance`: Distance to object in cm
- `num_objects`: Total objects detected in LIDAR scan

### Data Collection Tips

1. **Move objects through the field**: Walk around, wave hands, move objects at different distances
2. **Cover the full range**: 30cm to 2m for ultrasonics
3. **Vary speeds**: Slow and fast movement
4. **Multiple positions**: Different angles and orientations
5. **Collect 5-10 minutes**: Aim for 1000+ training samples

## Coordinate System Calibration

### Quick Calibration Method

1. **Place marker object** at known position:
   ```
   Example: 100cm forward, 0cm lateral from RPLIDAR
   Position: (x=0, y=100)
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
   - `lidar_x` should be near 0 cm
   - `lidar_y` should be near 100 cm
   - Adjust `sensor_positions` in config if needed

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

# Check permissions
ls -l /dev/ttyUSB0

# If permission denied, add user to dialout group
sudo usermod -a -G dialout $USER
# Then logout and login for this to take effect

# Or temporarily fix permissions
sudo chmod 666 /dev/ttyUSB0
```

### Motor Not Spinning

```bash
# Test motor control
python3 << 'EOF'
from rplidar import RPLidar
import time

print("Testing RPLIDAR motor...")
lidar = RPLidar('/dev/ttyUSB0')
lidar.start_motor()
print("Motor should be spinning now")
time.sleep(5)
lidar.stop_motor()
lidar.disconnect()
print("✓ Motor test complete")
EOF
```

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
