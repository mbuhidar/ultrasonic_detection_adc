# Arduino Uno Setup Instructions

Follow these steps to set up the Arduino Uno for the ultrasonic detection system.

## Prerequisites

- Arduino IDE installed on your computer ([Download here](https://www.arduino.cc/en/software))
- USB cable (Type A to Type B)
- Arduino Uno board
- 2x MB1300 ultrasonic sensors

## Hardware Setup

### Step 1: Connect MB1300 Sensors to Arduino

**Sensor 1:**
```
MB1300 Pin    →    Arduino Pin
─────────────────────────────────
VCC (Red)     →    5V
GND (Black)   →    GND
AN (White)    →    A0
TX (Leave unconnected or tie to Arduino RX if needed later)
```

**Sensor 2:**
```
MB1300 Pin    →    Arduino Pin
─────────────────────────────────
VCC (Red)     →    5V
GND (Black)   →    GND
AN (White)    →    A1
TX (Leave unconnected)
```

**Important Notes:**
- MB1300 sensors can run on 3.3V-5.5V, but 5V is recommended for best range
- Each sensor draws ~2mA typically, 50mA max
- The AN pin outputs analog voltage proportional to distance
- Keep sensor faces clear of obstructions

### Step 2: Verify Connections

Before powering on, double-check:
- ✓ All VCC pins connected to Arduino 5V
- ✓ All GND pins connected to Arduino GND
- ✓ Sensor 1 AN pin → A0
- ✓ Sensor 2 AN pin → A1
- ✓ No short circuits between pins

## Software Setup

### Step 3: Install Arduino IDE

If not already installed:

**Windows:**
1. Download from https://www.arduino.cc/en/software
2. Run installer
3. Follow installation wizard

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install arduino
```

Or download the latest version:
```bash
wget https://downloads.arduino.cc/arduino-ide/arduino-ide_latest_Linux_64bit.AppImage
chmod +x arduino-ide_latest_Linux_64bit.AppImage
./arduino-ide_latest_Linux_64bit.AppImage
```

**macOS:**
```bash
brew install --cask arduino
```

### Step 4: Upload the Code

1. **Open Arduino IDE**

2. **Connect Arduino to your computer via USB**

3. **Open the sketch:**
   - File → Open
   - Navigate to: `ultrasonic_detection_adc/arduino/ultrasonic_adc/ultrasonic_adc.ino`
   - Click Open

4. **Select your board:**
   - Tools → Board → Arduino AVR Boards → Arduino Uno

5. **Select your port:**
   - Tools → Port → Select the port with "Arduino Uno" 
   - **Windows:** Usually COM3, COM4, etc.
   - **Linux:** Usually /dev/ttyACM0 or /dev/ttyUSB0
   - **macOS:** Usually /dev/cu.usbmodem* or /dev/cu.usbserial*

6. **Upload the code:**
   - Click the Upload button (→) or Sketch → Upload
   - Wait for "Done uploading" message

### Step 5: Verify Operation

1. **Open Serial Monitor:**
   - Tools → Serial Monitor
   - Set baud rate to: **115200**

2. **You should see:**
   ```
   READY
   NUM_SENSORS:2
   ```

3. **Test the sensors:**
   - Type: `START:10` and press Enter
   - You should see data lines like: `S,1234,150,200`
   - Wave your hand in front of sensors to see values change
   - Type: `STOP` to stop data collection

## Troubleshooting

### Arduino Not Detected

**Linux:**
```bash
# Check if Arduino is connected
lsusb | grep Arduino

# Add your user to dialout group
sudo usermod -a -G dialout $USER

# Log out and log back in, then reconnect Arduino
```

**Windows:**
- Install CH340 or FTDI drivers if needed
- Check Device Manager for COM port

### Upload Errors

**Error: "avrdude: stk500_recv(): programmer is not responding"**
- Check USB cable connection
- Try a different USB port
- Press reset button on Arduino before upload
- Try a different USB cable

**Error: "Access denied" or "Permission denied"**
- Close any programs using the serial port (Serial Monitor, etc.)
- On Linux: `sudo chmod 666 /dev/ttyACM0`

### No Data in Serial Monitor

- Verify baud rate is 115200
- Press Arduino reset button
- Check sensor connections
- Verify sensors have power (5V between VCC and GND)

## Testing Sensors Individually

To test if sensors are working:

1. Open Serial Monitor (115200 baud)
2. Send: `START:1`
3. Observe ADC values (should be 0-1023)
4. Move your hand closer/farther from sensor
5. Values should change:
   - Closer = higher values
   - Farther = lower values
   - Typical range: 30-400 for useful distances

## Pin Modifications

To use different analog pins, modify this section in the code:

```cpp
const int NUM_SENSORS = 2;
const int SENSOR_PINS[] = {A0, A1};  // Change these pins as needed
```

For example, to use A2 and A3:
```cpp
const int SENSOR_PINS[] = {A2, A3};
```

## Adding More Sensors

The Arduino Uno has 6 analog inputs (A0-A5). To add more:

1. Connect additional sensors to available analog pins
2. Update the code:
   ```cpp
   const int NUM_SENSORS = 4;  // Update count
   const int SENSOR_PINS[] = {A0, A1, A2, A3};  // Add pins
   ```
3. Re-upload the sketch

## Next Steps

Once the Arduino is working:

1. Keep Arduino connected via USB
2. Note the serial port (e.g., /dev/ttyACM0)
3. Proceed to Orange Pi setup
4. The Orange Pi will communicate with Arduino through this USB connection

## LED Indicators

- **Power LED (ON)**: Arduino is powered
- **L LED (blinking)**: Arduino is running (built-in LED on pin 13)
- **TX/RX LEDs (flashing)**: Serial communication active

## Support

If you encounter issues:
- Verify all connections match the wiring diagram
- Test with Serial Monitor before connecting to Orange Pi
- Check sensor datasheets: https://maxbotix.com/pages/xl-maxsonar-ae-datasheet
- Ensure sensors are not facing each other (can cause interference)

## Serial Communication Protocol

The Arduino responds to these commands:
- `START:<n>` - Start collecting n samples per trigger (1-100)
- `STOP` - Stop data collection
- `CONFIG:<n>` - Update samples per trigger

Data format: `S,<timestamp_ms>,<sensor1_adc>,<sensor2_adc>,...`

Example: `S,12450,156,203` means:
- Timestamp: 12.45 seconds since Arduino started
- Sensor 1: ADC value 156 (~198cm)
- Sensor 2: ADC value 203 (~258cm)
