# Quick Start Guide

Get up and running in minutes!

## Overview

This system uses:
- **2x MB1300 ultrasonic sensors** → detect objects (chained for sequential operation)
- **Arduino Uno** → convert analog signals to digital
- **Orange Pi 5** → collect and analyze data

## Arduino Setup (10 minutes)

### 1. Wire Sensors to Arduino (Chained Configuration)

**Required Materials:**
- 2x MB1300 sensors
- 2x 1kΩ resistors (for TX→RX chaining)
- Jumper wires

**Sensor 1 (First in chain):**
| MB1300 Pin | Arduino Pin | Wire Color |
|------------|-------------|------------|
| Pin 1 (BW) | GND         | Black      |
| Pin 3 (AN) | A0          | White      |
| Pin 4 (RX) | D2          | Yellow     |
| Pin 5 (TX) | → 1kΩ → Sensor 2 RX | Blue |
| Pin 6 (+5V)| 5V          | Red        |
| Pin 7 (GND)| GND         | Black      |

**Sensor 2 (Second in chain):**
| MB1300 Pin | Arduino Pin | Wire Color |
|------------|-------------|------------|
| Pin 1 (BW) | GND         | Black      |
| Pin 3 (AN) | A1          | White      |
| Pin 4 (RX) | ← 1kΩ ← Sensor 1 TX | Yellow |
| Pin 5 (TX) | → 1kΩ → Sensor 1 RX | Blue |
| Pin 6 (+5V)| 5V          | Red        |
| Pin 7 (GND)| GND         | Black      |

**Important:** The 1kΩ resistors between TX and RX pins are required!

### 2. Upload Code

1. Open Arduino IDE
2. Open: `arduino/ultrasonic_adc/ultrasonic_adc.ino`
3. Select: Board → Arduino Uno
4. Select: Port → (your Arduino port)
5. Click Upload (→)

### 3. Test

1. Tools → Serial Monitor (115200 baud)
2. Should see:
   ```
   READY
   NUM_SENSORS:2
   MODE:AN_CHAINED
   ```
3. Type: `START:10` + Enter
4. Should see: `S,1234,150,200` (data lines)
5. Type: `STOP` + Enter

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
- Check wiring connections and 1kΩ resistors
- Verify Pin 1 (BW) connected to GND on both sensors
- Check chaining: Sensor 1 TX → 1kΩ → Sensor 2 RX

**Sensors not triggering in sequence:**
- Verify D2 connected to Sensor 1 RX
- Check 1kΩ resistors in TX→RX connections
- Ensure chain loops back: Sensor 2 TX → Sensor 1 RX

---

## Configuration

Edit `config.yaml` to change:
- Number of sensors
- Samples per trigger (default: 10)
- Output format (CSV or JSON)
- Arduino port

---

## Next Steps

- Read [WIRING_CHAINED.md](WIRING_CHAINED.md) for detailed chained wiring
- Read [SETUP_ARDUINO.md](SETUP_ARDUINO.md) for detailed Arduino setup
- Read [SETUP_ORANGEPI.md](SETUP_ORANGEPI.md) for detailed Orange Pi setup
- Read [PINOUT.md](PINOUT.md) for complete pin reference
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
├── config.yaml                 # Settings
├── WIRING_CHAINED.md          # Chained wiring guide
└── PINOUT.md                   # Pin reference
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
- **WIRING_CHAINED.md** - Chained sensor wiring
- SETUP_ARDUINO.md
- SETUP_ORANGEPI.md
- PINOUT.md
- README.md
