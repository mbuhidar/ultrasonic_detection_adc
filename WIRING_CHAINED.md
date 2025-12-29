# PW Echo Profiling - Chained Wiring Guide

Step-by-step guide for wiring MB1300 sensors using PW (acoustic envelope) output with chaining for spatial echo profiling.

---

## Why Chaining?

**Problem:** Multiple ultrasonic sensors operating simultaneously can interfere with each other.

**Solution:** Chain sensors so they fire sequentially:
1. Sensor 1 fires → completes → triggers Sensor 2
2. Sensor 2 fires → completes → triggers Sensor 1 (loop)
3. No acoustic interference between sensors
4. Cleaner, more accurate readings

---

## Required Components

### For 2-Sensor Setup:
- 2x MB1300 ultrasonic sensors
- 1x Arduino Uno
- 2x 1kΩ resistors (1/4W or better)
- Jumper wires:
  - 2x Black (GND)
  - 2x Red (Power)
  - 2x White/Signal (AN outputs)
  - 2x Yellow (RX/Trigger)
  - 2x Blue (TX/Chaining)
- Breadboard (recommended)

---

## Wiring Steps

### Step 1: Power and Ground

Connect power for both sensors:

```
Sensor 1 Pin 7 (GND) → Arduino GND (Black wire)
Sensor 1 Pin 6 (+5V) → Arduino 5V (Red wire)

Sensor 2 Pin 7 (GND) → Arduino GND (Black wire)
Sensor 2 Pin 6 (+5V) → Arduino 5V (Red wire)
```

**Tip:** Use breadboard power rails for cleaner wiring.

### Step 2: Echo Envelope Outputs

Connect the PW pins to Arduino analog inputs for echo profiling:

```
Sensor 1 Pin 2 (PW) → Arduino A0 (White/Signal wire)
Sensor 2 Pin 2 (PW) → Arduino A1 (White/Signal wire)
```

**Important:** Use PW (Pin 2), not AN (Pin 3), to capture the acoustic echo envelope.

### Step 3: Enable Pulse Mode

Hold Pin 1 (BW) LOW on both sensors to enable pulse output on TX:

```
Sensor 1 Pin 1 (BW) → Arduino GND
Sensor 2 Pin 1 (BW) → Arduino GND
```

**Important:** This changes TX (Pin 5) from serial data to pulse output.

### Step 4: Trigger Chain (Critical Step)

This is where the chaining happens:

#### Sensor 1 (First in Chain):
```
Sensor 1 Pin 4 (RX) → Arduino D2 (Yellow wire)
```
This allows Arduino to start the chain.

#### Sensor 1 → Sensor 2 Connection:
```
Sensor 1 Pin 5 (TX) → [1kΩ resistor] → Sensor 2 Pin 4 (RX) (Blue wire)
```
When Sensor 1 completes, it triggers Sensor 2.

#### Sensor 2 → Sensor 1 Loop Back:
```
Sensor 2 Pin 5 (TX) → [1kΩ resistor] → Sensor 1 Pin 4 (RX) (Blue wire)
```
When Sensor 2 completes, it triggers Sensor 1 again (continuous loop).

**Note:** Sensor 1 Pin 4 receives TWO connections:
- From Arduino D2 (initial trigger)
- From Sensor 2 TX via 1kΩ (loop back)

### Step 5: Arduino to Orange Pi

```
Arduino USB Port → Orange Pi USB Port (USB A-to-B cable)
```

---

## Complete Wiring Table

| Component | Pin | → | Destination | Notes |
|-----------|-----|---|-------------|-------|
| **Sensor 1** |
| | Pin 7 (GND) | → | Arduino GND | Black wire |
| | Pin 6 (+5V) | → | Arduino 5V | Red wire |
| | Pin 3 (AN)  | → | Arduino A0 | White wire |
| | Pin 4 (RX)  | → | Arduino D2 | Yellow wire (trigger) |
| | Pin 4 (RX)  | → | Sensor 2 TX + 1kΩ | Blue wire (loop) |
| | Pin 5 (TX)  | → | Sensor 2 RX + 1kΩ | Blue wire (chain) |
| | Pin 1 (BW)  | → | Arduino GND | Enable pulse mode |
| **Sensor 2**  | 
| | Pin 7 (GND) | → | Arduino GND | Black wire |
| | Pin 6 (+5V) | → | Arduino 5V | Red wire |
| | Pin 3 (AN)  | → | Arduino A1 | White wire |
| | Pin 4 (RX)  | → | Sensor 1 TX + 1kΩ | Blue wire (from S1) |
| | Pin 5 (TX)  | → | Sensor 1 RX + 1kΩ | Blue wire (loop back) |
| | Pin 1 (BW)  | → | Arduino GND | Enable pulse mode |
| **Resistors** |
| | 1kΩ | between | S1 TX & S2 RX | Signal conditioning |
| | 1kΩ | between | S2 TX & S1 RX | Signal conditioning |

---

## Breadboard Layout

```
                    BREADBOARD
    ┌────────────────────────────────────────────┐
    │  Power Rails                               │
    │  [+5V]═══════════════════════════════════  │ ← Arduino 5V
    │  [GND]═══════════════════════════════════  │ ← Arduino GND
    │                                            │
    │  Pin 1 (BW) of both sensors to GND rail    │
    │                                            │
    │  [Sensor 1]              [Sensor 2]        │
    │   Pin 7 → GND rail       Pin 7 → GND rail  │
    │   Pin 6 → +5V rail       Pin 6 → +5V rail  │
    │   Pin 3 → A0             Pin 3 → A1        │
    │   Pin 4 → D2 & S2.TX     Pin 4 → S1.TX     │
    │   Pin 5 → S2.RX          Pin 5 → S1.RX     │
    │   Pin 1 → GND            Pin 1 → GND       │
    │                                            │
    │  [1kΩ]        [1kΩ]                        │
    │  S1.TX-S2.RX  S2.TX-S1.RX                  │
    └────────────────────────────────────────────┘
```

---

## How It Works

### Sequence:

1. **Arduino triggers:** D2 goes HIGH for 20µS
2. **Sensor 1 fires:** Takes ~49ms to measure
3. **Sensor 1 completes:** Sends pulse on TX (Pin 5)
4. **Sensor 2 receives:** Pulse on RX (Pin 4) triggers Sensor 2
5. **Sensor 2 fires:** Takes ~49ms to measure
6. **Sensor 2 completes:** Sends pulse on TX (Pin 5)
7. **Loop back:** Pulse triggers Sensor 1 RX (Pin 4) again
8. **Repeat:** Continuous loop

### Timing:

- Each sensor: ~49ms measurement time
- 2 sensors: ~100ms total cycle time
- 10 samples/sec maximum (single-threaded)
- No interference between sensors ✓

---

## Testing the Chain

### Step 1: Upload Arduino Code

Upload `arduino/ultrasonic_adc/ultrasonic_adc.ino` to Arduino Uno.

### Step 2: Check Serial Output

Open Arduino IDE Serial Monitor (115200 baud):

```
READY
NUM_SENSORS:2
MODE:AN_CHAINED
```

### Step 3: Test Chain Operation

In Serial Monitor, type:
```
START:5
```

You should see:
```
ACK:STARTED
S,12345,150,200
S,12450,152,198
S,12555,149,201
...
```

Numbers should change smoothly as objects move.

### Step 4: Verify Chaining

Place hand in front of Sensor 1:
- First number changes (Sensor 1 reading)

Place hand in front of Sensor 2:
- Second number changes (Sensor 2 reading)

If both numbers change together, check:
- Pin 1 (BW) connected to GND on both sensors
- 1kΩ resistors in place
- TX-RX connections correct

---

## Troubleshooting

### Problem: Only one sensor reading changes

**Cause:** Chain not working, sensors operating independently.

**Check:**
1. Pin 1 (BW) connected to GND on both sensors?
2. 1kΩ resistors in place between TX and RX?
3. Wiring: S1.TX → S2.RX and S2.TX → S1.RX?

### Problem: Erratic readings

**Cause:** Noise on trigger lines.

**Check:**
1. 1kΩ resistors present (not jumper wires)
2. Wires not too long (< 30cm)
3. Good connections at breadboard

### Problem: No readings at all

**Cause:** Chain not starting.

**Check:**
1. Arduino D2 connected to Sensor 1 Pin 4 (RX)?
2. Arduino code uploaded correctly?
3. Power to both sensors (5V between Pin 6 and Pin 7)?

### Problem: Chain stops after first cycle

**Cause:** Loop-back connection missing.

**Check:**
1. Sensor 2 TX → Sensor 1 RX connection via 1kΩ
2. Both ends of resistor making good contact

---

## Expanding to More Sensors

### 3-Sensor Chain:

```
Arduino D2 → S1.RX (start)
S1.TX → [1kΩ] → S2.RX
S2.TX → [1kΩ] → S3.RX
S3.TX → [1kΩ] → S1.RX (loop back)

All sensors Pin 1 (BW) → GND
Analog: S1→A0, S2→A1, S3→A2
```

**Cycle time:** ~150ms (3 sensors × 50ms)

### 4-Sensor Chain:

```
Arduino D2 → S1.RX
S1.TX → [1kΩ] → S2.RX
S2.TX → [1kΩ] → S3.RX
S3.TX → [1kΩ] → S4.RX
S4.TX → [1kΩ] → S1.RX (loop back)

All sensors Pin 1 (BW) → GND
Analog: S1→A0, S2→A1, S3→A2, S4→A3
```

**Cycle time:** ~200ms (4 sensors × 50ms)

---

## Important Notes

### Critical Connections:

⚠️ **Pin 1 (BW) MUST be connected to GND** on all sensors
- This enables pulse mode on TX (Pin 5)
- Without this, TX sends serial data (won't trigger next sensor)

⚠️ **Use 1kΩ resistors between TX and RX**
- Conditions the pulse signal
- Prevents voltage issues
- Required for reliable operation

⚠️ **Don't forget the loop-back**
- Last sensor TX must connect to first sensor RX
- Without this, chain runs once and stops

### Pin 4 (RX) on First Sensor:

The first sensor's RX pin receives TWO signals:
1. Initial trigger from Arduino D2
2. Loop-back pulse from last sensor

This is normal - the pin handles both inputs.

---

## Distance Calculation

MB1300 with 5V supply:
```
Scaling: (Vcc/1024) per cm = ~4.9mV/cm
At 5V: ADC value ≈ distance in cm

Examples:
  ADC 100 ≈ 100 cm
  ADC 250 ≈ 250 cm
  ADC 400 ≈ 400 cm
```

For accurate calibration, measure known distances and adjust.

---

## Summary Checklist

Before powering on:

- [ ] All Pin 7 (GND) → Arduino GND
- [ ] All Pin 6 (+5V) → Arduino 5V
- [ ] Pin 3 (AN) → Arduino analog inputs (A0, A1, ...)
- [ ] All Pin 1 (BW) → Arduino GND (CRITICAL!)
- [ ] Sensor 1 Pin 4 (RX) → Arduino D2
- [ ] Sensor 1 Pin 5 (TX) → [1kΩ] → Sensor 2 Pin 4 (RX)
- [ ] Sensor 2 Pin 5 (TX) → [1kΩ] → Sensor 1 Pin 4 (RX)
- [ ] Arduino uploaded with ultrasonic_adc.ino
- [ ] Arduino → Orange Pi via USB cable

---

## References

- MB1300 Datasheet: https://maxbotix.com/pages/xl-maxsonar-ae-datasheet
- See PINOUT.md for detailed pin specifications
- See README.md for software setup
