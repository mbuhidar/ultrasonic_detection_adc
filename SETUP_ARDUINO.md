# Arduino Uno Setup Instructions

Follow these steps to set up the Arduino Uno for the ultrasonic detection system.

## Prerequisites

- Arduino IDE installed on your computer ([Download here](https://www.arduino.cc/en/software))
- USB cable (Type A to Type B)
- Arduino Uno board
- 2x MB1300 ultrasonic sensors
- 2x 1kΩ resistors (for sensor chaining)
- Breadboard (recommended)
- Jumper wires

## Hardware Setup

### Step 1: Connect MB1300 Sensors to Arduino

**This system uses AN Output Constantly Looping with chaining to prevent interference.**

For detailed step-by-step wiring instructions, see [WIRING_CHAINED.md](WIRING_CHAINED.md).

**Quick Reference - Sensor 1 (First in chain):**
```
MB1300 Pin    →    Arduino Pin / Connection
────────────────────────────────────────────────
Pin 7 (GND)   →    Arduino GND (Black)
Pin 6 (+5V)   →    Arduino 5V (Red)
Pin 3 (AN)    →    Arduino A0 (White)
Pin 4 (RX)    →    Arduino D2 (Yellow) - trigger pin
Pin 5 (TX)    →    [1kΩ resistor] → Sensor 2 Pin 4 (Blue)
Pin 1 (BW)    →    Arduino GND (enables pulse mode)
Pin 2 (PW)    →    Not connected
```

**Quick Reference - Sensor 2 (Second in chain):**
```
MB1300 Pin    →    Arduino Pin / Connection
────────────────────────────────────────────────
Pin 7 (GND)   →    Arduino GND (Black)
Pin 6 (+5V)   →    Arduino 5V (Red)
Pin 3 (AN)    →    Arduino A1 (White)
Pin 4 (RX)    →    ← [1kΩ resistor] ← Sensor 1 Pin 5 (Yellow)
Pin 5 (TX)    →    [1kΩ resistor] → Sensor 1 Pin 4 (Blue) - loop back
Pin 1 (BW)    →    Arduino GND (enables pulse mode)
Pin 2 (PW)    →    Not connected
```

**Critical Notes:**
- **Pin 1 (BW) MUST be connected to GND** on both sensors (enables pulse chaining)
- **1kΩ resistors are required** between TX and RX connections
- Sensor 1 Pin 4 receives TWO inputs: Arduino D2 and Sensor 2 TX (both via resistor)
- MB1300 sensors run on 3.3V-5.5V, but 5V is recommended
- Each sensor draws ~2mA typically, 50mA max
- Keep sensor faces clear and at least 15cm apart

### Step 2: Verify Connections

Before powering on, double-check:
- ✓ All Pin 6 (+5V) connected to Arduino 5V
- ✓ All Pin 7 (GND) connected to Arduino GND
- ✓ Sensor 1 Pin 3 (AN) → Arduino A0
- ✓ Sensor 2 Pin 3 (AN) → Arduino A1
- ✓ Both Pin 1 (BW) → Arduino GND (CRITICAL!)
- ✓ Sensor 1 Pin 4 (RX) → Arduino D2
- ✓ Sensor 1 Pin 5 (TX) → [1kΩ] → Sensor 2 Pin 4 (RX)
- ✓ Sensor 2 Pin 5 (TX) → [1kΩ] → Sensor 1 Pin 4 (RX)
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
   MODE:AN_CHAINED
   ```

3. **Test the sensors:**
   - Type: `START:10` and press Enter
   - You should see data lines like: `S,1234,150,200`
   - Wave your hand in front of Sensor 1 → first number changes
   - Wave your hand in front of Sensor 2 → second number changes
   - If both change together, check Pin 1 (BW) connections to GND
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
- Verify sensors have power (5V between Pin 6 and Pin 7)
- Ensure Pin 1 (BW) connected to GND on both sensors
- Check Arduino D2 connected to Sensor 1 Pin 4 (RX)

### Sensors Not Firing in Sequence

**Symptom:** Both sensor readings change at the same time.

**Causes:**
- Pin 1 (BW) not connected to GND (critical!)
- Missing 1kΩ resistors in TX→RX connections
- Incorrect TX→RX wiring

**Check:**
1. Verify Pin 1 on both sensors connected to Arduino GND
2. Confirm 1kΩ resistors between TX and RX pins
3. Verify: S1.TX → S2.RX and S2.TX → S1.RX (with resistors)
4. Check Arduino D2 connected to Sensor 1 RX

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
