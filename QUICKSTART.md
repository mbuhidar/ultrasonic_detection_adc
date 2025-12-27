# Quick Start Guide

Get up and running in minutes!

## Overview

This system uses:
- **2x MB1300 ultrasonic sensors** → detect objects
- **Arduino Uno** → convert analog signals to digital
- **Orange Pi 5** → collect and analyze data

## Arduino Setup (5 minutes)

### 1. Wire Sensors to Arduino

| MB1300 Pin | Arduino Pin |
|------------|-------------|
| VCC (Red)  | 5V          |
| GND (Black)| GND         |
| AN (White) | A0 (sensor 1), A1 (sensor 2) |

### 2. Upload Code

1. Open Arduino IDE
2. Open: `arduino/ultrasonic_adc/ultrasonic_adc.ino`
3. Select: Board → Arduino Uno
4. Select: Port → (your Arduino port)
5. Click Upload (→)

### 3. Test

1. Tools → Serial Monitor (115200 baud)
2. Type: `START:10` + Enter
3. Should see: `S,1234,150,200` (data lines)
4. Type: `STOP` + Enter

✓ Arduino is ready!

---

## Orange Pi Setup (10 minutes)

### 1. Install Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-matplotlib python3-tk
```

### 2. Set Up Project

```bash
cd /home/mbuhidar/Code/mbuhidar/ultrasonic_detection_adc/orangepi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r ../requirements.txt
```

### 3. Configure Arduino Port

```bash
# Find Arduino port
ls /dev/tty* | grep -E "(ACM|USB)"

# Add permission
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyACM0  # Use your actual port

# Edit config
nano ../config.yaml
# Change: port: "/dev/ttyACM0"  (to your port)
```

### 4. Test System

```bash
python test_system.py
```

Should see all ✓ PASS.

### 5. Start Collecting Data

```bash
python data_collector.py
```

Press Ctrl+C to stop. Data saved to `../data/` directory.

✓ Orange Pi is ready!

---

## Usage

### Collect Data
```bash
cd orangepi
source venv/bin/activate
python data_collector.py
```

### View Real-time
```bash
python realtime_viewer.py
```

### Analyze Data
```bash
python data_analyzer.py ../data/sensor_data_*.csv --stats --plot
```

---

## Common Issues

**"Permission denied" on serial port:**
```bash
sudo chmod 666 /dev/ttyACM0
```

**"Module not found" errors:**
```bash
source venv/bin/activate
pip install -r ../requirements.txt
```

**Arduino not found:**
```bash
lsusb | grep -i arduino
ls /dev/tty* | grep -E "(ACM|USB)"
```

**No data showing:**
- Check Arduino serial monitor first (115200 baud)
- Verify sensors are powered (5V to VCC)
- Check wiring connections

---

## Configuration

Edit `config.yaml` to change:
- Number of sensors
- Samples per trigger (default: 10)
- Output format (CSV or JSON)
- Arduino port

---

## Next Steps

- Read [SETUP_ARDUINO.md](SETUP_ARDUINO.md) for detailed Arduino setup
- Read [SETUP_ORANGEPI.md](SETUP_ORANGEPI.md) for detailed Orange Pi setup
- Read [README.md](README.md) for complete documentation

---

## File Structure

```
ultrasonic_detection_adc/
├── arduino/ultrasonic_adc/    # Arduino code
├── orangepi/                   # Python scripts
│   ├── data_collector.py      # Main collection
│   ├── realtime_viewer.py     # Live view
│   └── data_analyzer.py       # Analysis
├── data/                       # Output files
└── config.yaml                 # Settings
```

---

## Getting Help

Run system test:
```bash
python test_system.py
```

Check Arduino:
```bash
# Arduino IDE: Tools → Serial Monitor (115200 baud)
# Type: START:5
```

Check Orange Pi:
```bash
python -c "import serial, yaml, pandas; print('OK')"
```

See detailed docs:
- SETUP_ARDUINO.md
- SETUP_ORANGEPI.md
- README.md
