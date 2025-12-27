# Ultrasonic Detection ADC System

A comprehensive system for detecting objects using multiple MB1300 ultrasonic sensors with Arduino Uno ADC processing and Orange Pi 5 data collection.

## System Architecture

```
MB1300 Sensors (2x) → Arduino Uno (ADC) → Serial → Orange Pi 5 (Processing/Storage)
```

## Components

- **Orange Pi 5**: Primary processing unit for data collection and analysis
- **Arduino Uno**: ADC converter for analog sensor signals
- **MaxBotix XL-MaxSonar-AE MB1300**: Ultrasonic sensors (2x to start, expandable)

## Features

- ✅ Configurable number of samples per trigger event (default: 10)
- ✅ Real-time data collection and storage
- ✅ Time series data recording in CSV or JSON format
- ✅ Real-time visualization
- ✅ Data analysis tools with statistics and object detection
- ✅ Multi-sensor support (easily expandable beyond 2)
- ✅ Threaded data collection for optimal performance

## Hardware Setup

### MB1300 Sensor Connections

The MB1300 sensors use the **AN Output Constantly Looping** method.

**Sensor 1:**
- VCC → Arduino 5V
- GND → Arduino GND
- AN (Analog Output) → Arduino A0
- TX → Not connected (or Arduino RX if using serial mode)

**Sensor 2:**
- VCC → Arduino 5V
- GND → Arduino GND
- AN (Analog Output) → Arduino A1
- TX → Not connected

**Arduino to Orange Pi:**
- Arduino USB → Orange Pi USB port

### MB1300 Sensor Specifications

- **Range**: 300mm to 5000mm
- **Resolution**: 1mm
- **Output**: ~(Vcc/512) per inch
- **Update Rate**: ~49ms in constantly looping mode
- **Supply Voltage**: 3.3V - 5.5V
- **Current**: 2.0mA typical, 50mA max

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

Data is saved to the `data/` directory with timestamps.

### 2. Real-time Visualization

View sensor data in real-time:
```bash
python realtime_viewer.py
```

Options:
- `-c, --config`: Path to configuration file
- `-H, --history`: Number of data points to display (default: 100)

### 3. Data Analysis

Analyze collected data:
```bash
# Show statistics
python data_analyzer.py ../data/sensor_data_YYYYMMDD_HHMMSS.csv --stats

# Plot time series
python data_analyzer.py ../data/sensor_data_YYYYMMDD_HHMMSS.csv --plot

# Plot histogram
python data_analyzer.py ../data/sensor_data_YYYYMMDD_HHMMSS.csv --histogram

# Detect objects below 100cm threshold
python data_analyzer.py ../data/sensor_data_YYYYMMDD_HHMMSS.csv --detect 100

# Save plot to file
python data_analyzer.py ../data/sensor_data_YYYYMMDD_HHMMSS.csv --plot -o plot.png
```

## Configuration

Edit `config.yaml` to customize the system:

```yaml
# Sensor Configuration
sensors:
  count: 2                    # Number of sensors
  samples_per_trigger: 10     # Samples to collect per trigger
  sampling_interval_ms: 50    # Time between samples

# Arduino Configuration
arduino:
  port: "/dev/ttyACM0"        # Arduino serial port
  baudrate: 115200            # Serial communication speed
  timeout: 2                  # Serial timeout in seconds

# Data Storage
data:
  output_directory: "./data"  # Where to save data files
  file_format: "csv"          # csv or json
  buffer_size: 100            # Records to buffer before writing

# Pin Mapping
pins:
  sensor_1: A0
  sensor_2: A1
  # sensor_3: A2              # Uncomment to add more sensors
```

## Project Structure

```
ultrasonic_detection_adc/
├── arduino/
│   └── ultrasonic_adc/
│       └── ultrasonic_adc.ino    # Arduino ADC code
├── orangepi/
│   ├── data_collector.py         # Main data collection script
│   ├── realtime_viewer.py        # Real-time visualization
│   └── data_analyzer.py          # Data analysis tools
├── data/                          # Output directory for collected data
├── config.yaml                    # System configuration
├── requirements.txt               # Python dependencies
└── README.md                      # This file
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

The MB1300 outputs approximately (Vcc/512) volts per inch:

```
For 5V supply:
- ADC value: 0-1023 (10-bit)
- Distance (inches) = ADC_value × 0.5
- Distance (cm) = ADC_value × 0.5 × 2.54
```

Example:
- ADC = 100 → 50 inches → 127 cm
- ADC = 200 → 100 inches → 254 cm

## Expanding the System

### Adding More Sensors

1. Connect additional MB1300 sensors to Arduino analog pins (A2-A5)
2. Update `arduino/ultrasonic_adc/ultrasonic_adc.ino`:
   ```cpp
   const int NUM_SENSORS = 3;  // Change from 2 to 3
   const int SENSOR_PINS[] = {A0, A1, A2};  // Add A2
   ```
3. Update `config.yaml`:
   ```yaml
   sensors:
     count: 3
   pins:
     sensor_1: A0
     sensor_2: A1
     sensor_3: A2
   ```
4. Re-upload the Arduino sketch

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
