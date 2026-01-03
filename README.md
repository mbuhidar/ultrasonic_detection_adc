# Ultrasonic Echo Profiling System

A comprehensive system for spatial echo profiling using MB1300 ultrasonic sensors with Arduino Uno and Orange Pi 5 for 2-meter range coverage at 1cm resolution.

**NEW:** Optional RPLIDAR integration for ML training with 2D position ground truth!

## System Architecture

### Basic Echo Profiling Mode
```
MB1300 Sensors (PW output) → Arduino Uno (Fast ADC) → Serial → Orange Pi 5 (Analysis)
```

### Optional: ML Training Mode (with RPLIDAR)
```
MB1300 Sensors (Echo) ──→ Arduino Uno ──→ USB Serial ──→ Orange Pi 5 (Data Fusion)
RPLIDAR A1 (2D Position) ────────────→ USB Serial ──→
```

**Note:** RPLIDAR is only needed if you want to collect ML training data with ground truth position labels.

## Components

### Required
- **Orange Pi 5**: Primary processing unit for data collection and visualization
- **Arduino Uno**: High-speed ADC sampling (50µs intervals) for echo envelope capture
- **MaxBotix MB1300 (XL-MaxSonar-AE)**: Ultrasonic sensors with PW (acoustic envelope) output

### Optional (for ML Training)
- **RPLIDAR A1M8**: 2D LiDAR for ground truth position data (~$100)

## Features

- ✅ **Echo profiling**: Captures full acoustic envelope (not just distance)
- ✅ **1cm spatial resolution** over 2-meter range (240 samples per trigger)
- ✅ **Fast ADC sampling**: 50µs intervals synchronized with acoustic propagation
- ✅ **Sensor chaining**: Sequential operation prevents acoustic interference
- ✅ **Real-time data collection** with CSV storage (separate rows per sensor)
- ✅ **Advanced visualization**: Echo profiles, heatmaps, distance tracking
- ✅ **Object detection**: Identifies echoes and tracks movement
- ✅ **Multi-sensor support**: Expandable architecture
- 🔧 **Optional: RPLIDAR integration**: Synchronized 2D position ground truth for ML training
- 🔧 **Optional: ML training data**: 240 acoustic features + (x,y) position labels

## Hardware Setup

### MB1300 Sensor Connections (PW Pin Mode)

The MB1300 sensors use **PW pin (acoustic envelope output) with Chaining** for spatial echo profiling.

**For detailed wiring instructions, see [WIRING_CHAINED.md](WIRING_CHAINED.md)**

**Quick Summary:**

**Sensor 1 (First in chain):**
- Pin 7 (GND) → Arduino GND
- Pin 6 (+5V) → Arduino 5V
- **Pin 2 (PW)** → Arduino A0 **(echo envelope output)**
- Pin 4 (RX) → Arduino D2 (trigger)
- Pin 5 (TX) → [1kΩ resistor] → Sensor 2 Pin 4 (RX)
- Pin 1 (BW) → Arduino GND (enables pulse mode)

**Sensor 2 (Second in chain):**
- Pin 7 (GND) → Arduino GND
- Pin 6 (+5V) → Arduino 5V
- **Pin 2 (PW)** → Arduino A1 **(echo envelope output)**
- Pin 4 (RX) → [1kΩ resistor] ← Sensor 1 Pin 5 (TX)
- Pin 5 (TX) → [1kΩ resistor] → Sensor 1 Pin 4 (RX) - loop back
- Pin 1 (BW) → Arduino GND (enables pulse mode)

**Required Components:**
- 2x 1kΩ resistors for TX→RX chaining
- Breadboard recommended

**Arduino to Orange Pi:**
- Arduino USB → Orange Pi USB port

### MB1300 Sensor Specifications

- **Range**: 300mm to 5000mm
- **Resolution**: 1mm per reading
- **PW Output**: Raw acoustic envelope (0-Vcc, amplitude of echo returns)
- **Spatial Resolution**: ~1cm with 50µs sampling intervals
- **Update Rate**: ~49ms per sensor in chaining mode
- **Supply Voltage**: 3.3V - 5.5V (5V recommended)
- **Current**: 2.0mA typical, 50mA max

### Echo Profiling Method

1. Arduino triggers Sensor 1 by pulsing D2 HIGH for 20µS
2. After 300µs (ultrasonic burst transmission), Arduino samples PW pin 240 times
3. Each sample (50µs apart) captures echo amplitude at progressive distances
4. 240 samples × 0.86cm/sample = 206cm range coverage at 1cm resolution
5. Sensors fire sequentially via chaining to prevent interference
6. Data format: 240 ADC values per sensor per trigger event

### Pin Configuration

The default pin configuration (can be modified in `config.yaml`):

```yaml
pins:
  sensor_1: A0  # Arduino analog pin A0
  sensor_2: A1  # Arduino analog pin A1
```

To add more sensors, connect them to additional analog pins (A2, A3, A4, A5) and update the configuration.

## Software Setup

### Prerequisites

**On Orange Pi 5:**
```bash
# Install Python 3 (if not already installed)
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Install system dependencies for matplotlib
sudo apt install python3-matplotlib python3-tk
```

### Installation

1. **Clone or copy the project to your Orange Pi:**
   ```bash
   cd /home/mbuhidar/Code/mbuhidar/ultrasonic_detection_adc
   ```

2. **Create a virtual environment:**
   ```bash
   cd orangepi
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r ../requirements.txt
   ```

4. **Upload Arduino code:**
   - Open `arduino/ultrasonic_adc/ultrasonic_adc.ino` in Arduino IDE
   - Select **Board**: Arduino Uno
   - Select **Port**: (your Arduino's port)
   - Click **Upload**

5. **Configure the system:**
   - Edit `config.yaml` to match your setup
   - Update the Arduino port (usually `/dev/ttyACM0` or `/dev/ttyUSB0`)
   - Adjust sensor count and sampling parameters

### Finding the Arduino Port

```bash
# List USB devices before connecting Arduino
ls /dev/tty*

# Connect Arduino, then list again
ls /dev/tty*

# The new device is your Arduino (typically /dev/ttyACM0)
```

Or check with:
```bash
dmesg | grep tty
```

## Usage

### 1. Data Collection

Basic data collection:
```bash
cd orangepi
source venv/bin/activate
python data_collector.py
```

With custom parameters:
```bash
# Collect 20 samples per trigger for 60 seconds
python data_collector.py -s 20 -d 60

# Use custom config file
python data_collector.py -c /path/to/config.yaml
```

Options:
- `-c, --config`: Path to configuration file (default: `../config.yaml`)
- `-s, --samples`: Number of samples per trigger (overrides config)
- `-d, --duration`: Collection duration in seconds (0 for infinite)

Data is saved to the `data/` directory with timestamps. Each trigger event produces 2 rows (one per sensor) with 240 echo readings each.

### 2. Echo Profile Analysis

Analyze echo profile data and visualize spatial information:

```bash
# Show all visualizations (profile, heatmap, comparison, distance tracking)
python echo_analyzer.py ../data/sensor_data_YYYYMMDD_HHMMSS.csv

# View single echo profile
python echo_analyzer.py data.csv --plot-type profile --sensor 1 --row 5

# View heatmap (shows movement over time)
python echo_analyzer.py data.csv --plot-type heatmap --sensor 1

# Track object distance over time
python echo_analyzer.py data.csv --plot-type distance --sensor 1 --threshold 50

# Compare both sensors
python echo_analyzer.py data.csv --plot-type comparison --row 10

# Generate report with statistics
python echo_analyzer.py data.csv --report --output report.txt

# Detect objects in specific trigger
python echo_analyzer.py data.csv --detect --row 5
```

### 3. ML Training with RPLIDAR (Optional)

**Collect synchronized ultrasonic echo + RPLIDAR position data for ML training:**

```bash
# Install RPLIDAR library first
pip install rplidar-roboticia

# Collect training data with 2D position ground truth
python data_collector_with_lidar.py --duration 120

# Output: training_data_YYYYMMDD_HHMMSS.csv
# Format: 240 echo values (features) + (x,y) position (labels)
```

**Position Data:**
- Captures only objects **in front of the box** (Y > 66.5cm from RPLIDAR)
- Records the **nearest point to the front line** (minimum Y value)
- Coordinates are **front-line-relative**: X = left/right position, Y = distance in front
- Y=0 is the front edge of the box, positive Y extends forward

**See [RPLIDAR_SETUP.md](RPLIDAR_SETUP.md) for detailed setup instructions.**

### 4. Legacy Data Analysis

**See [RPLIDAR_SETUP.md](RPLIDAR_SETUP.md) for detailed setup instructions.**

### 4. 

### 3. Legacy Data Analysis

For simple distance measurements (if using AN pin mode):
```bash
# Show statistics
python data_analyzer.py ../data/sensor_data_YYYYMMDD_HHMMSS.csv --stats

# Plot time series
python data_analyzer.py ../data/sensor_data_YYYYMMDD_HHMMSS.csv --plot

# Detect objects below 100cm threshold
python data_analyzer.py ../data/sensor_data_YYYYMMDD_HHMMSS.csv --detect 100
```

## Configuration

Edit `config.yaml` to customize the system:

```yaml
# Sensor Configuration
sensors:
  count: 2                      # Number of sensors
  model: "MB1300"               # Sensor model
  samples_per_trigger: 10       # Arduino trigger samples (not used in echo mode)
  readings_per_trigger: 240     # Number of echo samples per trigger (1cm resolution)
  sampling_interval_ms: 100     # Time between trigger events
  chaining_mode: true           # Sensors fire sequentially

# Arduino Configuration
arduino:
  port: "/dev/ttyACM0"          # Arduino serial port
  baudrate: 115200              # Serial communication speed
  timeout: 2                    # Serial timeout in seconds

# Data Storage
data:
  output_directory: "./data"    # Where to save data files
  file_format: "csv"            # csv or json
  buffer_size: 100              # Records to buffer before writing

# Pin Mapping (PW pins for echo profiling)
pins:
  sensor_1: A0                  # Connect to MB1300 Pin 2 (PW)
  sensor_2: A1                  # Connect to MB1300 Pin 2 (PW)
  # sensor_3: A2                # Uncomment to add more sensors
```

## Project Structure

```
ultrasonic_detection_adc/
├── arduino/echo profiling code (PW pin mode)
├── orangepi/
│   ├── data_collector.py         # Main data collection script
│   ├── echo_analyzer.py          # Echo profile analysis & visualization
│   ├── data_analyzer.py          # Legacy analyzer (for AN pin mode)
│   ├── realtime_viewer.py        # Real-time visualization
│   └── test_system.py            # System test utilities
├── data/                          # Collected data files
├── config.yaml                    # System configuration
├── WIRING_CHAINED.md             # Detailed wiring guide (PW pin)
├── PINOUT.md                     # Complete pinout reference
├── ARDUINO_CLI_GUIDE.md          # Programming Arduino from Orange Pi
└── README.md                     # This file
```n script
│   ├── realtime_viewer.py        # Real-time visualization
│   └── data_analyzer.py          # Data analysis tools
├── data/                          # Output directory for collected data
├── config.yaml                    # System configuration
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── QUICKSTART.md                  # Quick setup guide
├── WIRING_CHAINED.md              # Detailed chained wiring guide
├── PINOUT.md                      # Complete pin reference
├── SETUP_ARDUINO.md               # Arduino setup instructions
├── SETUP_ORANGEPI.md              # Orange Pi setup instructions
└── ARDUINO_CLI_GUIDE.md           # Program Arduino from Orange Pi
```

## Communication Protocol

The Arduino and Orange Pi communicate via serial using a simple text-based protocol:

**Commands (Orange Pi → Arduino):**
- `START:<samples>\n` - Start data collection with N samples per trigger
- `STOP\n` - Stop data collection
- `CONFIG:<samples>\n` - Update samples per trigger

**Responses (Arduino → Orange Pi):**
- `READY\n` - Arduino initialized and ready
- `NUM_SENSORS:<count>\n` - Number of connected sensors
- `ACK:STARTED\n` - Data collection started
- `ACK:STOPPED\n` - Data collection stopped
- `ACK:CONFIG_UPDATED\n` - Configuration updated
- `S,<timestamp>,<sensor1>,<sensor2>,...\n` - Sensor data

**Data Format:**
- `S` - Data packet identifier
- `timestamp` - Arduino millis() timestamp
- `sensor1, sensor2, ...` - ADC values (0-1023) for each sensor

## Distance Calculation

The MB1300 outputs approximately (Vcc/1024) per cm:

```
For 5V supply:
- ADC value: 0-1023 (10-bit)
- Distance (cm) ≈ ADC_value
- Scaling: ~4.9mV/cm
```

Example:
- ADC = 100 → ~100 cm
- ADC = 250 → ~250 cm
- ADC = 400 → ~400 cm

## Expanding the System

### Adding More Sensors

1. Connect additional MB1300 sensors following the chaining pattern (see WIRING_CHAINED.md)
2. Add 1kΩ resistors between each TX→RX connection
3. Update `arduino/ultrasonic_adc/ultrasonic_adc.ino`:
   ```cpp
   const int NUM_SENSORS = 3;  // Change from 2 to 3
   const int SENSOR_PINS[] = {A0, A1, A2};  // Add A2
   ```
4. Update `config.yaml`:
   ```yaml
   sensors:
     count: 3
   pins:
     sensor_1: A0
     sensor_2: A1
     sensor_3: A2
   ```
5. Re-upload the Arduino sketch

**Note:** With chaining, cycle time increases by ~50ms per sensor added.

### Adjusting Sample Rate

The sampling interval can be adjusted in `config.yaml`:

```yaml
sensors:
  sampling_interval_ms: 50  # Time between samples (milliseconds)
```

Note: MB1300 updates at ~49ms intervals, so sampling faster may yield duplicate readings.

## Troubleshooting

### Arduino Not Detected

```bash
# Check if Arduino is connected
lsusb | grep Arduino

# Check permissions
sudo usermod -a -G dialout $USER
# Log out and back in for this to take effect

# Or give temporary permission
sudo chmod 666 /dev/ttyACM0
```

### No Data Received

1. Check Arduino serial monitor (115200 baud) to verify it's sending data
2. Verify the port in `config.yaml` matches your Arduino
3. Ensure sensors are properly powered (5V)
4. Check sensor wiring connections
5. Verify Pin 1 (BW) connected to GND on both sensors
6. Check chaining: S1.TX → 1kΩ → S2.RX and S2.TX → 1kΩ → S1.RX
7. Verify Arduino D2 connected to Sensor 1 Pin 4 (RX)

### Inaccurate Readings

1. Verify sensor power supply is stable 5V
2. Check for electrical noise interference
3. Ensure sensors have clear line of sight to target
4. Verify analog pins are correctly connected
5. Calibrate using known distances

### Serial Communication Errors

```bash
# Check if port is in use
lsof /dev/ttyACM0

# Kill any processes using the port
sudo fuser -k /dev/ttyACM0
```

## Performance Notes

- **Sample Rate**: Up to 20 samples/second per sensor (limited by MB1300 update rate)
- **Data Buffering**: 100 records buffered before disk write (configurable)
- **Memory Usage**: Approximately 50MB for continuous operation
- **Storage**: ~1KB per second of data (CSV format, 2 sensors, 10 samples/sec)

## Future Enhancements

- [ ] Add support for I2C sensor communication
- [ ] Implement sensor calibration routines
- [ ] Add web-based dashboard for remote monitoring
- [ ] Support for data streaming to cloud services
- [ ] Machine learning for object classification
- [ ] Multi-sensor fusion algorithms

## License

This project is provided as-is for educational and research purposes.

## References

- [MB1300 Datasheet](https://maxbotix.com/pages/xl-maxsonar-ae-datasheet)
- [Arduino Serial Communication](https://www.arduino.cc/reference/en/language/functions/communication/serial/)
- [Orange Pi 5 Documentation](http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Orange-Pi-5.html)

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Verify all hardware connections
3. Review Arduino serial monitor output
4. Check the data/ directory for logged errors

## Version History

- **v1.0.0** - Initial release
  - Support for 2 MB1300 sensors
  - Arduino Uno ADC processing
  - Orange Pi data collection and analysis
  - Real-time visualization
  - CSV/JSON data export
