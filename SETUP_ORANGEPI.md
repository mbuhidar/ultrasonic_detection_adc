# Orange Pi 5 Setup Instructions

Follow these steps to set up the Orange Pi 5 for data collection and analysis.

## Prerequisites

- Orange Pi 5 with Ubuntu/Debian-based OS
- Internet connection
- Arduino Uno already set up and connected via USB
- SSH access or direct terminal access

## Quick Start (One Command)

If you're comfortable with automated setup:

```bash
cd /home/mbuhidar/Code/mbuhidar/ultrasonic_detection_adc/orangepi
chmod +x setup.sh
./setup.sh
```

Then skip to **Step 6: Test the System**.

## Manual Setup (Step by Step)

### Step 1: Update System Packages

```bash
sudo apt update
sudo apt upgrade -y
```

### Step 2: Install Python and Dependencies

```bash
# Install Python 3 and pip
sudo apt install -y python3 python3-pip python3-venv

# Install system dependencies for matplotlib
sudo apt install -y python3-matplotlib python3-tk

# Install git (if you need to clone the project)
sudo apt install -y git
```

### Step 3: Copy Project Files

Transfer the project to your Orange Pi using one of these methods:

**Option A: Using SCP (from your computer):**
```bash
scp -r ultrasonic_detection_adc/ user@orangepi-ip:/home/mbuhidar/Code/mbuhidar/
```

**Option B: Using USB drive:**
1. Copy project folder to USB drive
2. Mount USB on Orange Pi:
   ```bash
   sudo mkdir -p /mnt/usb
   sudo mount /dev/sda1 /mnt/usb
   cp -r /mnt/usb/ultrasonic_detection_adc /home/mbuhidar/Code/mbuhidar/
   ```

**Option C: Using Git (if hosted):**
```bash
cd /home/mbuhidar/Code/mbuhidar
git clone <your-repo-url> ultrasonic_detection_adc
```

### Step 4: Configure Arduino Connection

Find your Arduino's serial port:

```bash
# Before connecting Arduino
ls /dev/tty* > before.txt

# Connect Arduino via USB
# Wait 2 seconds

# After connecting Arduino
ls /dev/tty* > after.txt

# Find the difference
diff before.txt after.txt
```

Common ports:
- `/dev/ttyACM0` (most common)
- `/dev/ttyUSB0` (with some USB adapters)

**Set up permissions:**

```bash
# Add your user to dialout group for serial access
sudo usermod -a -G dialout $USER

# Log out and log back in for this to take effect
# OR temporarily grant access:
sudo chmod 666 /dev/ttyACM0
```

**Update configuration:**

Edit the config file with your Arduino's port:

```bash
cd /home/mbuhidar/Code/mbuhidar/ultrasonic_detection_adc
nano config.yaml
```

Update the port line:
```yaml
arduino:
  port: "/dev/ttyACM0"  # Change this to your Arduino's port
```

Save with `Ctrl+O`, Enter, then `Ctrl+X`.

### Step 5: Set Up Python Environment

```bash
cd /home/mbuhidar/Code/mbuhidar/ultrasonic_detection_adc/orangepi

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r ../requirements.txt
```

**Note:** Keep the virtual environment activated for all subsequent commands.

### Step 6: Test the System

Run the system test:

```bash
python test_system.py
```

You should see:
```
✓ PASS     Arduino Connection
✓ PASS     Data Collection
✓ PASS     Distance Calculation
✓ PASS     File System
```

If any tests fail, see the troubleshooting section below.

### Step 7: Collect Data

**Start basic data collection:**

```bash
python data_collector.py
```

Press `Ctrl+C` to stop.

**Collect with custom parameters:**

```bash
# Collect 20 samples per trigger for 60 seconds
python data_collector.py -s 20 -d 60
```

**View real-time data:**

```bash
python realtime_viewer.py
```

**Analyze collected data:**

```bash
# List collected data files
ls ../data/

# Analyze a data file
python data_analyzer.py ../data/sensor_data_20251226_*.csv --stats --plot
```

## Configuration Options

Edit `config.yaml` to customize:

```yaml
# Sensor Configuration
sensors:
  count: 2                    # Number of sensors
  samples_per_trigger: 10     # Samples per trigger event
  sampling_interval_ms: 50    # Time between samples (ms)

# Arduino Configuration
arduino:
  port: "/dev/ttyACM0"        # Arduino port
  baudrate: 115200
  timeout: 2

# Data Storage
data:
  output_directory: "./data"   # Data output location
  file_format: "csv"           # csv or json
  buffer_size: 100             # Records to buffer before writing
```

## Running on Boot (Optional)

To automatically start data collection when Orange Pi boots:

### Create systemd service:

```bash
sudo nano /etc/systemd/system/ultrasonic-collector.service
```

Add this content:
```ini
[Unit]
Description=Ultrasonic Data Collector
After=network.target

[Service]
Type=simple
User=mbuhidar
WorkingDirectory=/home/mbuhidar/Code/mbuhidar/ultrasonic_detection_adc/orangepi
ExecStart=/home/mbuhidar/Code/mbuhidar/ultrasonic_detection_adc/orangepi/venv/bin/python data_collector.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ultrasonic-collector.service
sudo systemctl start ultrasonic-collector.service

# Check status
sudo systemctl status ultrasonic-collector.service

# View logs
sudo journalctl -u ultrasonic-collector.service -f
```

## Troubleshooting

### Cannot Find Arduino

**Check connection:**
```bash
lsusb | grep -i arduino
dmesg | tail -20
```

**Check permissions:**
```bash
ls -l /dev/ttyACM0

# Should show: crw-rw---- 1 root dialout
# If not accessible:
sudo chmod 666 /dev/ttyACM0
```

### Import Errors

If you see "ModuleNotFoundError":

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall packages
pip install -r ../requirements.txt
```

### Serial Port in Use

```bash
# Find what's using the port
sudo lsof /dev/ttyACM0

# Kill the process
sudo fuser -k /dev/ttyACM0
```

### No Data Received

1. Test Arduino directly with Serial Monitor first
2. Check Arduino is running (LED indicators)
3. Verify correct port in config.yaml
4. Check cable connection
5. Try unplugging and reconnecting USB

### Matplotlib Display Issues

If running headless (no display):

```bash
# Use non-GUI backend
export MPLBACKEND=Agg

# Or save plots to files instead
python data_analyzer.py data.csv --plot -o output.png
```

For SSH with X11 forwarding:
```bash
# On local machine
ssh -X user@orangepi-ip

# Then run viewer
python realtime_viewer.py
```

### Permission Denied Errors

```bash
# Fix serial port permissions permanently
sudo usermod -a -G dialout $USER
sudo usermod -a -G tty $USER

# Log out and log back in
```

## File Locations

- **Configuration:** `../config.yaml`
- **Data Output:** `../data/`
- **Python Scripts:** Current directory (`orangepi/`)
- **Virtual Environment:** `venv/`

## Command Reference

### Data Collection

```bash
# Basic collection (infinite)
python data_collector.py

# With duration
python data_collector.py -d 300  # 5 minutes

# With custom samples
python data_collector.py -s 20

# With custom config
python data_collector.py -c /path/to/config.yaml
```

### Real-time Viewing

```bash
# Default (100 data points)
python realtime_viewer.py

# More history
python realtime_viewer.py -H 200
```

### Data Analysis

```bash
# Statistics
python data_analyzer.py data.csv --stats

# Plot time series
python data_analyzer.py data.csv --plot

# Histogram
python data_analyzer.py data.csv --histogram

# Detect objects
python data_analyzer.py data.csv --detect 100  # 100cm threshold

# Save output
python data_analyzer.py data.csv --plot -o output.png
```

### System Test

```bash
# Run all tests
python test_system.py
```

## Performance Optimization

### For continuous long-term operation:

1. **Increase buffer size** (reduce disk writes):
   ```yaml
   data:
     buffer_size: 1000  # Write every 1000 records
   ```

2. **Use CSV format** (more efficient than JSON):
   ```yaml
   data:
     file_format: "csv"
   ```

3. **Monitor disk space:**
   ```bash
   df -h
   du -sh ../data/
   ```

4. **Rotate old data:**
   ```bash
   # Move old data to archive
   mkdir -p ../data/archive
   mv ../data/sensor_data_2024*.csv ../data/archive/
   ```

## Network Access (Optional)

To access data from another computer:

### Simple HTTP server:
```bash
cd ../data
python3 -m http.server 8000

# Access from browser: http://orangepi-ip:8000
```

### SSH access to data:
```bash
# From remote computer
scp user@orangepi-ip:/home/mbuhidar/Code/mbuhidar/ultrasonic_detection_adc/data/*.csv .
```

## Next Steps

1. **Test system:** Run `python test_system.py`
2. **Collect data:** Run `python data_collector.py`
3. **View real-time:** Run `python realtime_viewer.py`
4. **Analyze results:** Run `python data_analyzer.py` on collected files
5. **Customize:** Edit `config.yaml` for your needs

## Updating the System

To update sensor count, sampling rate, or other parameters:

1. Edit `config.yaml`
2. Restart data collection
3. No need to re-upload Arduino code unless changing pin assignments

## Support Resources

- **README.md** - Complete project documentation
- **SETUP_ARDUINO.md** - Arduino setup guide
- **Test script** - `python test_system.py` for diagnostics

## Deactivating Virtual Environment

When done:
```bash
deactivate
```

To reactivate later:
```bash
cd /home/mbuhidar/Code/mbuhidar/ultrasonic_detection_adc/orangepi
source venv/bin/activate
```
