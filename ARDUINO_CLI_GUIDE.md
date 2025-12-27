# Programming Arduino from Orange Pi using arduino-cli

Quick guide to program the Arduino Uno directly from your Orange Pi 5 without needing a separate computer.

---

## Why arduino-cli?

- Program Arduino directly from Orange Pi (headless operation)
- No GUI needed - works over SSH
- Faster deployment for remote setups
- Single device for both programming and data collection

---

## Installation

### Step 1: Install arduino-cli

```bash
# Download and install arduino-cli
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh

# Add to PATH (add this to ~/.bashrc for persistence)
export PATH=$PATH:$HOME/bin

# Verify installation
arduino-cli version
```

### Step 2: Initialize Configuration

```bash
# Create config file
arduino-cli config init

# Update core index
arduino-cli core update-index
```

### Step 3: Install Arduino AVR Core

```bash
# Install support for Arduino Uno
arduino-cli core install arduino:avr
```

---

## Programming the Arduino Uno

### Find Your Arduino Port

```bash
# Before connecting Arduino
ls /dev/tty* > /tmp/before.txt

# Connect Arduino via USB
sleep 2

# After connecting
ls /dev/tty* > /tmp/after.txt

# Find the difference
diff /tmp/before.txt /tmp/after.txt
```

Usually shows: `/dev/ttyACM0` or `/dev/ttyUSB0`

### Set Permissions

```bash
# One-time permission (temporary)
sudo chmod 666 /dev/ttyACM0

# Or add user to dialout group (permanent)
sudo usermod -a -G dialout $USER
# Log out and back in for this to take effect
```

### Compile and Upload

Navigate to the project directory:

```bash
cd /home/mbuhidar/Code/mbuhidar/ultrasonic_detection_adc
```

**Compile the sketch:**

```bash
arduino-cli compile --fqbn arduino:avr:uno arduino/ultrasonic_adc
```

**Upload to Arduino:**

```bash
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno arduino/ultrasonic_adc
```

**Compile and upload in one command:**

```bash
arduino-cli compile --upload -p /dev/ttyACM0 --fqbn arduino:avr:uno arduino/ultrasonic_adc
```

---

## Verify Upload

Check that Arduino is running correctly:

```bash
# Install screen if not available
sudo apt install screen

# Connect to serial monitor (115200 baud)
screen /dev/ttyACM0 115200
```

You should see:
```
READY
NUM_SENSORS:2
MODE:AN_CHAINED
```

**Exit screen:** Press `Ctrl+A` then `K` then `Y`

---

## Troubleshooting

### Error: "Permission denied"

```bash
# Check current permissions
ls -l /dev/ttyACM0

# Add yourself to dialout group
sudo usermod -a -G dialout $USER
# Then logout and login again
```

### Error: "Port not found"

```bash
# List all USB devices
lsusb | grep -i arduino

# Check kernel messages
dmesg | tail -20

# Verify port
ls -l /dev/ttyACM*
ls -l /dev/ttyUSB*
```

### Error: "Board not responding"

```bash
# Press reset button on Arduino
# Wait 2 seconds, then try upload again

# Or use alternative programmer
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno \
  --programmer arduino:avrisp arduino/ultrasonic_adc
```

### Error: "Platform not installed"

```bash
# Reinstall AVR core
arduino-cli core install arduino:avr

# List installed cores
arduino-cli core list
```

---

## Quick Reference Commands

```bash
# List available boards
arduino-cli board list

# List installed cores
arduino-cli core list

# Search for cores
arduino-cli core search arduino

# Compile only (no upload)
arduino-cli compile --fqbn arduino:avr:uno arduino/ultrasonic_adc

# Upload pre-compiled sketch
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno arduino/ultrasonic_adc

# Get board details
arduino-cli board details -b arduino:avr:uno

# Monitor serial output (if available)
arduino-cli monitor -p /dev/ttyACM0 -c baudrate=115200
```

---

## Board FQBN Reference

For Arduino Uno, the Fully Qualified Board Name (FQBN) is:
```
arduino:avr:uno
```

Other common boards:
- Arduino Mega: `arduino:avr:mega`
- Arduino Nano: `arduino:avr:nano`
- Arduino Leonardo: `arduino:avr:leonardo`

---

## Complete Workflow Example

From fresh Orange Pi to programmed Arduino:

```bash
# 1. Install arduino-cli
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
export PATH=$PATH:$HOME/bin

# 2. Setup arduino-cli
arduino-cli config init
arduino-cli core update-index
arduino-cli core install arduino:avr

# 3. Set permissions
sudo usermod -a -G dialout $USER
# Logout and login

# 4. Connect Arduino and find port
arduino-cli board list

# 5. Navigate to project
cd /home/mbuhidar/Code/mbuhidar/ultrasonic_detection_adc

# 6. Compile and upload
arduino-cli compile --upload -p /dev/ttyACM0 --fqbn arduino:avr:uno arduino/ultrasonic_adc

# 7. Verify with serial monitor
screen /dev/ttyACM0 115200
# Should see: READY, NUM_SENSORS:2, MODE:AN_CHAINED
# Exit: Ctrl+A, K, Y

# 8. Start data collection
cd orangepi
source venv/bin/activate
python data_collector.py
```

---

## Automated Upload Script

Create a helper script for easy uploads:

```bash
cat > ~/upload_arduino.sh << 'EOF'
#!/bin/bash
# Quick upload script for Arduino

SKETCH_PATH="/home/mbuhidar/Code/mbuhidar/ultrasonic_detection_adc/arduino/ultrasonic_adc"
BOARD="arduino:avr:uno"
PORT="/dev/ttyACM0"

# Find Arduino port if not specified
if [ ! -e "$PORT" ]; then
    PORT=$(ls /dev/ttyACM* 2>/dev/null | head -n1)
    if [ -z "$PORT" ]; then
        PORT=$(ls /dev/ttyUSB* 2>/dev/null | head -n1)
    fi
fi

if [ -z "$PORT" ]; then
    echo "Error: Arduino not found"
    exit 1
fi

echo "Compiling and uploading to $PORT..."
arduino-cli compile --upload -p "$PORT" --fqbn "$BOARD" "$SKETCH_PATH"

if [ $? -eq 0 ]; then
    echo "✓ Upload successful!"
    echo "Verifying..."
    sleep 2
    timeout 3 screen -L "$PORT" 115200 || true
else
    echo "✗ Upload failed"
    exit 1
fi
EOF

chmod +x ~/upload_arduino.sh
```

Usage:
```bash
~/upload_arduino.sh
```

---

## Comparison: arduino-cli vs Arduino IDE

| Feature | arduino-cli | Arduino IDE |
|---------|-------------|-------------|
| Installation | Lightweight (~50MB) | Heavy (~500MB) |
| Interface | Command-line | GUI |
| SSH Support | ✓ Yes | ✗ No |
| Automation | ✓ Easy | ✗ Difficult |
| Speed | ✓ Fast | Slower |
| Beginner-friendly | Medium | ✓ Easy |

**Recommendation:**
- Use Arduino IDE for initial development and debugging
- Use arduino-cli for deployment and production

---

## Integration with Data Collection

Once Arduino is programmed, you can immediately start data collection:

```bash
# Upload Arduino code
arduino-cli compile --upload -p /dev/ttyACM0 --fqbn arduino:avr:uno arduino/ultrasonic_adc

# Wait for Arduino to initialize
sleep 3

# Start data collection
cd orangepi
source venv/bin/activate
python data_collector.py
```

Or create a one-command startup:

```bash
cat > ~/start_system.sh << 'EOF'
#!/bin/bash
cd /home/mbuhidar/Code/mbuhidar/ultrasonic_detection_adc

# Upload if needed (optional - comment out if already uploaded)
# arduino-cli compile --upload -p /dev/ttyACM0 --fqbn arduino:avr:uno arduino/ultrasonic_adc
# sleep 3

# Start collection
cd orangepi
source venv/bin/activate
python data_collector.py "$@"
EOF

chmod +x ~/start_system.sh
```

---

## Additional Resources

- arduino-cli documentation: https://arduino.github.io/arduino-cli/
- Arduino CLI GitHub: https://github.com/arduino/arduino-cli
- Original guide: https://siytek.com/arduino-cli-raspberry-pi/

---

## Notes

- arduino-cli is officially supported by Arduino
- Works on any Linux system (Raspberry Pi, Orange Pi, Ubuntu, etc.)
- Can be used in automated scripts and CI/CD pipelines
- Supports all official Arduino boards and many third-party boards
