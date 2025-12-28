# System Pinout Guide

Complete wiring diagram for the ultrasonic detection system.

---

## System Overview

```
┌─────────────────┐         ┌──────────────┐         ┌──────────────┐
│   MB1300 x2     │ Analog  │  Arduino Uno │  USB    │  Orange Pi 5 │
│ Ultrasonic      ├────────►│     ADC      ├────────►│  Processing  │
│   Sensors       │         │              │ Serial  │              │
└─────────────────┘         └──────────────┘         └──────────────┘
```

---

## MB1300 Sensor Pinout

Each MB1300 (AE Series) sensor has these pins:

```
MB1300 Sensor (XL-MaxSonar-AE)
┌──────────────────────────────────────────────────────────────┐
│  Pin 1: BW    │ Beam Width / Chaining Control                │
│  Pin 2: PW    │ Analog Envelope Output (MB1300)              │
│  Pin 3: AN    │ Analog Voltage Output ← We use this          │
│  Pin 4: RX    │ Range Start/Stop Control                     │
│  Pin 5: TX    │ Serial Output (9600 baud)                    │
│  Pin 6: +5V   │ Power Supply (Red wire)                      │
│  Pin 7: GND   │ Ground (Black wire)                          │
└──────────────────────────────────────────────────────────────┘
```

**Pin Details for MB1300-AE Series:**

- **Pin 1 (BW)**: Leave open or high for serial output on Pin 5. Hold low for pulse output (chaining mode).
  
- **Pin 2 (PW)**: Outputs analog voltage envelope of the acoustic waveform. This allows processing the raw waveform. *Not used in this project.*
  
- **Pin 3 (AN)**: Analog voltage output with scaling factor of (Vcc/1024) per cm.
  - At 5V supply: ~4.9mV/cm
  - At 3.3V supply: ~3.2mV/cm
  - Maximum range: ~700cm at 5V, ~600cm at 3.3V
  - **This is the pin we connect to Arduino analog inputs (A0, A1, etc.)**
  
- **Pin 4 (RX)**: Internally pulled high. Sensor continuously measures when high or open. Hold low to stop ranging. Bring high for 20µS or more to trigger a range reading.
  
- **Pin 5 (TX)**: When Pin 1 is open/high: Sends RS232-format serial data (0-Vcc levels, 9600 baud, 8N1). Format: "R" + 3 digits (range in cm) + carriage return. When Pin 1 is low: Sends single pulse for chaining. *Not used in this project.*
  
- **Pin 6 (+5V)**: Power supply (3.3V - 5.5V, 5V recommended)
  
- **Pin 7 (GND)**: Ground

**Pin Configuration for AN Output Constantly Looping Mode (Chained):**

This method chains sensors so they fire sequentially, preventing interference:

- Pin 1 (BW): **Hold LOW** for pulse output on Pin 5 (required for chaining)
- Pin 2 (PW): Leave disconnected
- Pin 3 (AN): **Connect to Arduino analog input (A0, A1, etc.)** ← Signal wire
- Pin 4 (RX): **First sensor:** Connect to Arduino digital pin (pull high to start)
               **Other sensors:** Connect to previous sensor's Pin 5 (TX) via 1kΩ resistor
- Pin 5 (TX): **Connect to next sensor's Pin 4 (RX) via 1kΩ resistor** (pulse chaining)
               **Last sensor:** Connect back to first sensor's RX to loop
- Pin 6 (+5V): **Connect to Arduino 5V** ← Power wire (Red)
- Pin 7 (GND): **Connect to Arduino GND** ← Ground wire (Black)

**How Chaining Works:**
1. Arduino pulls first sensor's RX high for 20µS → Sensor 1 starts ranging
2. When Sensor 1 completes, it sends pulse on TX (Pin 5) → triggers Sensor 2's RX
3. Sensor 2 ranges and triggers Sensor 3, and so on...
4. Last sensor triggers first sensor → continuous loop

**Benefits:**
- Prevents acoustic interference between sensors
- Sequential operation ensures clean readings
- Automatic timing - no delays needed in code

---

## Complete Wiring Diagram

### Two-Sensor Configuration (AN Constantly Looping with Chaining)

```
MB1300 SENSOR 1                    ARDUINO UNO
┌─────────────┐                   ┌─────────────┐
│             │                   │             │
│  Pin 7 GND  ├──────────────────►│  GND        │
│             │  (Black)          │             │
│  Pin 6 +5V  ├──────────────────►│  5V         │
│             │  (Red)            │             │
│  Pin 3 AN   ├──────────────────►│  A0         │
│             │  (Analog Signal)  │             │
│  Pin 4 RX   ├───────────────────┤  D2 (Trig)  │◄─┐
│             │  (Start Chain)    │             │  │
│  Pin 1 BW   ├──────────────────►│  GND        │  │
│             │  (Held LOW)       │             │  │
│             │                   │             │  │
│  Pin 5 TX   ├──┐                │             │  │
│             │  │ 1kΩ            │             │  │
└─────────────┘  │                │             │  │
                 │                │             │  │
MB1300 SENSOR 2  │                │             │  │
┌─────────────┐  │                │             │  │
│             │  │                │             │  │
│  Pin 7 GND  ├──┼───────────────►│  GND        │  │
│             │  │ (Black)        │             │  │
│  Pin 6 +5V  ├──┼───────────────►│  5V         │  │
│             │  │ (Red)          │             │  │
│  Pin 3 AN   ├──┼───────────────►│  A1         │  │
│             │  │ (Analog Signal)│             │  │
│  Pin 4 RX   ├──┘                │             │  │
│             │  (From Sensor 1)  │             │  │
│  Pin 1 BW   ├──────────────────►│  GND        │  │
│             │  (Held LOW)       │             │  │
│             │                   │             │  │
│  Pin 5 TX   ├───────────────────┼─────────────┼──┘
│             │  1kΩ (Loop back)  │             │
└─────────────┘                   │             │
                                  │             │
                                  │  USB Port   ├───────────┐
                                  │             │   USB     │
                                  └─────────────┘  Cable    │
                                                            │
                                  ORANGE PI 5               │
                                  ┌─────────────┐           │
                                  │             │           │
                                  │  USB Port   │◄──────────┘
                                  │  (any)      │
                                  │             │
                                  └─────────────┘
```

**Chaining Details:**
- All Pin 1 (BW) connected to GND enables pulse mode on Pin 5
- 1kΩ resistors condition signals between TX and RX pins
- Arduino D2 pin starts the chain by pulling Sensor 1 RX high
- Sensors automatically trigger each other in sequence
- Last sensor loops back to first sensor for continuous operation

---

## Detailed Connection Table

### Sensor 1 Connections (First in Chain)

| MB1300 Sensor 1 Pin | Wire Color    | Arduino/Connection      | Notes                          |
|---------------------|---------------|-------------------------|--------------------------------|
| Pin 7 (GND)         | Black         | Arduino GND             | Common ground                  |
| Pin 6 (+5V)         | Red           | Arduino 5V              | Power supply (5V recommended)  |
| Pin 3 (AN)          | White/Signal  | Arduino A0              | Analog voltage output (0-5V)   |
| Pin 4 (RX)          | Yellow        | Arduino D2 (trigger)    | Start chain (pull high 20µS)   |
| Pin 5 (TX)          | Blue          | Sensor 2 Pin 4 via 1kΩ  | Trigger next sensor            |
| Pin 1 (BW)          | —             | Arduino GND             | Enable pulse mode (hold LOW)   |
| Pin 2 (PW)          | —             | Not connected           | Not used                       |

### Sensor 2 Connections (Second in Chain)

| MB1300 Sensor 2 Pin | Wire Color    | Arduino/Connection      | Notes                          |
|---------------------|---------------|-------------------------|--------------------------------|
| Pin 7 (GND)         | Black         | Arduino GND             | Common ground                  |
| Pin 6 (+5V)         | Red           | Arduino 5V              | Power supply (5V recommended)  |
| Pin 3 (AN)          | White/Signal  | Arduino A1              | Analog voltage output (0-5V)   |
| Pin 4 (RX)          | Blue          | Sensor 1 Pin 5 via 1kΩ  | Triggered by Sensor 1          |
| Pin 5 (TX)          | Yellow        | Sensor 1 Pin 4 via 1kΩ  | Loop back to start             |
| Pin 1 (BW)          | —             | Arduino GND             | Enable pulse mode (hold LOW)   |
| Pin 2 (PW)          | —             | Not connected           | Not used                       |

**Required Components:**
- 2x 1kΩ resistors for signal conditioning between TX/RX pins

### Arduino to Orange Pi

| Arduino Side | Cable      | Orange Pi Side | Notes                   |
|-------------|------------|----------------|--------------------------|
| USB Type B  | USB Cable  | USB Type A     | Serial communication     |
| (built-in)  |            | (any port)     | Also provides power      |

---

## Arduino Uno Pin Reference

```
               ARDUINO UNO
        ┌────────────────────┐
        │    ┌──────────┐    │
        │    │ USB Port │    │  ◄── Connect to Orange Pi
        │    └──────────┘    │
        │                    │
DIGITAL │  0  RX        AREF │
 PINS   │  1  TX         GND │
        │  2             A0  │ ◄── Sensor 1 AN (white)
        │  3~            A1  │ ◄── Sensor 2 AN (white)
        │  4             A2  │ ◄── Available for Sensor 3
        │  5~            A3  │ ◄── Available for Sensor 4
        │  6~            A4  │ ◄── Available for Sensor 5
        │  7             A5  │ ◄── Available for Sensor 6
        │  8                 │
        │  9~                │   ANALOG INPUTS
        │ 10~                │
        │ 11~                │
        │ 12                 │
        │ 13 (LED)           │
        │                    │
POWER   │ GND           GND  │ ◄── All sensor GND (black)
        │ AREF          5V   │ ◄── All sensor +5V (red)
        │ SDA           VIN  │
        │ SCL                │
        │                    │
        │  ┌──────────┐      │
        │  │ DC Power │      │  Optional: 7-12V if not
        │  └──────────┘      │  powered via USB
        └────────────────────┘
```

---

## Expanding to More Sensors

### Four-Sensor Configuration

```
Sensor 1:  Pin 7 (GND) → Arduino GND,  Pin 6 (+5V) → Arduino 5V,  Pin 3 (AN) → Arduino A0
Sensor 2:  Pin 7 (GND) → Arduino GND,  Pin 6 (+5V) → Arduino 5V,  Pin 3 (AN) → Arduino A1
Sensor 3:  Pin 7 (GND) → Arduino GND,  Pin 6 (+5V) → Arduino 5V,  Pin 3 (AN) → Arduino A2
Sensor 4:  Pin 7 (GND) → Arduino GND,  Pin 6 (+5V) → Arduino 5V,  Pin 3 (AN) → Arduino A3

Leave Pin 1 (BW) and Pin 4 (RX) open on all sensors for continuous operation.
```

### Six-Sensor Configuration (Maximum)

```
Sensor 1:  Pin 7 (GND) → Arduino GND,  Pin 6 (+5V) → Arduino 5V,  Pin 3 (AN) → Arduino A0
Sensor 2:  Pin 7 (GND) → Arduino GND,  Pin 6 (+5V) → Arduino 5V,  Pin 3 (AN) → Arduino A1
Sensor 3:  Pin 7 (GND) → Arduino GND,  Pin 6 (+5V) → Arduino 5V,  Pin 3 (AN) → Arduino A2
Sensor 4:  Pin 7 (GND) → Arduino GND,  Pin 6 (+5V) → Arduino 5V,  Pin 3 (AN) → Arduino A3
Sensor 5:  Pin 7 (GND) → Arduino GND,  Pin 6 (+5V) → Arduino 5V,  Pin 3 (AN) → Arduino A4
Sensor 6:  Pin 7 (GND) → Arduino GND,  Pin 6 (+5V) → Arduino 5V,  Pin 3 (AN) → Arduino A5

Leave Pin 1 (BW) and Pin 4 (RX) open on all sensors for continuous operation.
```

**Arduino Uno Limitation:** 6 analog inputs maximum (A0-A5)

---

## Power Requirements

### MB1300 Sensor Specifications

- **Operating Voltage:** 3.3V - 5.5V (5V recommended)
- **Current Draw:** 2.0mA typical, 50mA max per sensor
- **Total for 2 sensors:** 4mA typical, 100mA max

### Arduino Uno Power Budget

**Via USB Power:**
- Total available: ~500mA from USB
- Arduino consumption: ~50mA
- Available for sensors: ~450mA
- **Can support:** All 6 sensors with headroom

**Via DC Jack (7-12V):**
- Total available: Depends on supply
- Recommended: 9V/500mA adapter
- **Can support:** All 6 sensors easily

### Orange Pi 5 Power

- Powers itself independently
- Provides 500mA via USB to Arduino (sufficient for 2-6 sensors)
- No additional power supply needed for Arduino

---

## Important Wiring Notes

### Ground Connections

⚠️ **CRITICAL:** All sensor GND pins must connect to Arduino GND
- Use a breadboard rail or wire all GND together
- Common ground is essential for accurate readings

### Power Distribution

✓ **Good Practice:** Use breadboard for power distribution
```
5V Rail: Arduino 5V → All sensor +5V pins
GND Rail: Arduino GND → All sensor GND pins
```

✓ **Alternative:** Wire sensors in parallel directly to Arduino pins

### Wire Gauge

- **Recommended:** 22-24 AWG solid core wire
- **Length:** Keep under 30cm (1 foot) for analog signals
- **Shielded cable:** Use if experiencing noise (optional)

### Sensor Placement

- Keep sensors at least 15cm (6 inches) apart
- Don't point sensors directly at each other
- Ensure clear line of sight to target area
- Mount securely to prevent vibration

---

## Breadboard Layout (Optional but Recommended)

```
                    BREADBOARD
    ┌───────────────────────────────────────┐
    │  Power Rails                          │
    │  + + + + + + + + + + + + + + + + + +  │ ◄── 5V from Arduino
    │                                       │
    │  - - - - - - - - - - - - - - - - - -  │ ◄── GND from Arduino
    │                                       │
    │  [Sensor 1]         [Sensor 2]        │
    │    GND                 GND            │
    │    +5V                 +5V            │
    │    AN ──► to A0        AN ──► to A1   │
    │                                       │
    └───────────────────────────────────────┘
```

**Benefits:**
- Cleaner wiring
- Easy to add more sensors
- Reduces wire clutter
- Better power distribution

---

## Testing Individual Connections

### Test Power Supply

```bash
# With Arduino connected and powered
# Measure voltage between 5V and GND: Should read ~5V
# Measure voltage at each sensor +5V and GND: Should read ~5V
```

### Test Analog Signals

Open Arduino Serial Monitor:
```
1. Tools → Serial Monitor (115200 baud)
2. Type: START:1
3. Wave hand in front of sensor 1 → A0 value should change
4. Wave hand in front of sensor 2 → A1 value should change
5. Type: STOP
```

Expected values:
- Near object (30cm): 200-400
- Far object (200cm): 50-150
- No object: ~20-50 (depends on environment)

---

## Troubleshooting

### Problem: No readings from sensor

**Check:**
1. ✓ Power: 5V between sensor +5V and GND pins
2. ✓ Ground: Continuity between sensor GND and Arduino GND
3. ✓ Signal: Voltage on AN pin changes when object moves (0-5V)
4. ✓ Wiring: Correct analog pin (A0, A1, etc.)

### Problem: Erratic readings

**Check:**
1. Wire length (keep analog wires short)
2. Loose connections (check all pins)
3. Sensor interference (move sensors apart)
4. Power supply stability (measure 5V rail)

### Problem: All sensors show same reading

**Check:**
1. Each sensor connected to different analog pin (A0, A1, etc.)
2. Code matches pin configuration
3. Sensors not too close together (min 15cm spacing)

---

## Safety Notes

⚠️ **Warnings:**
- Don't exceed 5.5V on MB1300 sensors (will damage sensor)
- Don't short circuit 5V to GND
- Don't exceed 20mA per Arduino GPIO pin (analog inputs are safe)
- Disconnect power before wiring/unwiring

✓ **Best Practices:**
- Double-check all connections before powering on
- Use color-coded wires (Red=Power, Black=Ground, Other=Signal)
- Keep wiring neat and organized
- Label sensors if using multiple units

---

## Quick Reference Card

**Copy this for quick reference:**

```
┌──────────────────────────────────────────┐
│  ULTRASONIC PINOUT QUICK REF             │
├──────────────────────────────────────────┤
│  MB1300 Pin Assignments:                 │
│    Pin 1 (BW)  → Leave OPEN              │
│    Pin 2 (PW)  → Not connected           │
│    Pin 3 (AN)  → Arduino A0/A1/etc.      │
│    Pin 4 (RX)  → Leave OPEN              │
│    Pin 5 (TX)  → Not connected           │
│    Pin 6 (+5V) → Arduino 5V (Red)        │
│    Pin 7 (GND) → Arduino GND (Black)     │
│                                          │
│  Sensor 1:                               │
│    Pin 7 (Black) → Arduino GND           │
│    Pin 6 (Red)   → Arduino 5V            │
│    Pin 3 (White) → Arduino A0            │
│                                          │
│  Sensor 2:                               │
│    Pin 7 (Black) → Arduino GND           │
│    Pin 6 (Red)   → Arduino 5V            │
│    Pin 3 (White) → Arduino A1            │
│                                          │
│  Arduino → Orange Pi:                    │
│    USB Type B → USB Type A               │
│                                          │
│  Scaling: ~4.9mV/cm at 5V (Pin 3 AN)     │
│  Add more sensors to A2-A5               │
└──────────────────────────────────────────┘
```

---

## Additional Resources

- MB1300 Datasheet: https://maxbotix.com/pages/xl-maxsonar-ae-datasheet
- Arduino Uno Pinout: https://docs.arduino.cc/hardware/uno-rev3
- Orange Pi 5: http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Orange-Pi-5.html
