# Physical Sensor Layout and Wiring

Complete physical layout diagram for ultrasonic echo profiling system with optional RPLIDAR integration.

## System Overview

**Basic System (Required):**
```
┌─────────────────────────────────────────────────────────┐
│  Ultrasonic Sensors (MB1300) → Arduino Uno → Orange Pi  │
└─────────────────────────────────────────────────────────┘
```

**Optional: With RPLIDAR (for ML Training):**
```
┌─────────────────────────────────────────────────────────┐
│  Ultrasonic Sensors (MB1300) → Arduino Uno → Orange Pi  │
│  RPLIDAR A1 ─────────────────────────────→ Orange Pi    │
└─────────────────────────────────────────────────────────┘
```

## Top-Down Physical Layout

```
                    FRONT (Forward, 90°)
                           ▲
                           │
        S1 ────────────────┼────────────────── S2
        ──►    Front Edge  │  Front Edge     ◄──
       30°  (74.93cm wide) │                150°
        │                  │                  │
        ├──────────────────┼──────────────────┤
        │                  │                  │
        │                  │                  │
        │       ╲          │          ╱       │
        │        ╲         │         ╱        │
        │         ╲        │        ╱         │
        │          ╲       │       ╱          │
        │           ╲      │      ╱           │
        │            ╲     │     ╱            │
        │             ╲    │    ╱             │
        │              ╲   │   ╱              │
        │               ╲  │  ╱               │
        │                ╲ │ ╱                │
        │                 ╲│╱                 │
        │                  ╳                  │
        │                 ╱│╲                 │
        │                ╱ │ ╲                │
        │               ╱  │  ╲               │
        │              ╱   │   ╲              │
        │             ╱    │    ╲             │
        │            ╱     │     ╲            │
        │           ╱      │      ╲           │
        │          ╱   [RPLIDAR]   ╲          │
        │         ╱       (0,0)      ╲        │
        │        ╱    Center point    ╲       │
        │       ╱                      ╲      │
        │      ╱                        ╲     │
        │     ╱                          ╲    │
        │    ╱                            ╲   │
        │   ╱  Platform: 74.93 × 132.99cm  ╲  │
        │  ╱   (29.5" × 52.36")             ╲ │
        │ ╱                                  ╲│
        │╱                                    ╲
        └──────────────────────────────────────┘
        ▲                                     ▲
     (-37.47, +66.5)                    (+37.47, +66.5)
    Left sensor on                     Right sensor on
    front edge @30°                    front edge @150°
    
                    BACK (Rear, 270°)

Coordinate System:
  Origin (0,0): RPLIDAR center (center of rectangle)
  X-axis: Left (-) to Right (+)
  Y-axis: Back (-) to Front (+)
  Angles: 0° = Right, 90° = Front, 180° = Left, 270° = Back

Sensor Mounting:
  Both sensors physically mounted ON the front edge of the box
  S1 (Left):  (-37.47cm, +66.5cm) pointing at 30°
  S2 (Right): (+37.47cm, +66.5cm) pointing at 150°
  Sensors face each other with converging beams
```

## Sensor Positions

| Sensor | Position (X, Y) | Angle | FOV Range | Coverage Area |
|--------|----------------|-------|-----------|---------------|
| S1 (Left) | (-37.47cm, +66.5cm) | 30° | 0° to 60° | Inward-right-forward, overlaps with S2 |
| S2 (Right) | (+37.47cm, +66.5cm) | 150° | 120° to 180° | Inward-left-forward, overlaps with S1 |
| RPLIDAR | (0cm, 0cm) | N/A | 0° to 360° | Full circular scan |

### Sensor Coverage Diagram

```
                     90° (Forward)
                          ▲
                          │
              120° ╱──────┼──────╲ 60°
                  ╱       │       ╲
         S2 FOV  ╱        │        ╲  S1 FOV
       (120-180)╱         │         ╲(0-60)
       150° ───╱──────────┼──────────╲─── 30°
              ╱           │           ╲
    180° ────┤        [RPLIDAR]        ├──── 0°
     (Left)  │            │            │  (Right)
             │        S2  │  S1        │
             │            │            │
             └────────────┼────────────┘
                          │
                        270°
                       (Back)

Sensors face EACH OTHER across front of platform:
  - S1: At left corner, pointing 30° (inward-right-forward)
  - S2: At right corner, pointing 150° (inward-left-forward)
  - Coverage overlaps in center forward area (60° to 120°)
```

## Complete System Wiring Diagram

### Component Connections

```
┌─────────────────────────────────────────────────────────────────┐
│                         Orange Pi 5                             │
│  ┌────────────┐    ┌─────────────────┐    ┌─────────────────┐   │
│  │ USB-Serial │    │   USB Serial    │    │   5V Power Out  │   │
│  │ (Arduino)  │    │   (RPLIDAR)     │    │                 │   │
│  └─────┬──────┘    └────────┬────────┘    └────────┬────────┘   │
└────────┼────────────────────┼──────────────────────┼────────────┘
         │                    │                      │
         │ USB                │ USB                  │ 5V/GND
         │                    │                      │
    ┌────▼─────┐         ┌────▼──────────┐           │
    │          │         │  USB-to-TTL   │           │
    │ Arduino  │         │   Adapter     │           │
    │   Uno    │         └────┬──────────┘           │
    │          │              │                      │
    └──┬───┬───┘         ┌────▼──────────┐           │
       │   │             │   RPLIDAR A1  │ ◄─────────┘
```
┌─────────────────────────────────────────────────────────────────┐
│                         Orange Pi 5                             │
│  ┌────────────┐    ┌─────────────────┐    ┌─────────────────┐   │
│  │ USB-Serial │    │   USB Serial    │    │   5V Power Out  │   │
│  │ (Arduino)  │    │   (RPLIDAR)     │    │                 │   │
│  └─────┬──────┘    └────────┬────────┘    └────────┬────────┘   │
└────────┼────────────────────┼──────────────────────┼────────────┘
         │                    │                      │
         │ USB                │ USB                  │ 5V/GND
         │                    │                      │
    ┌────▼─────┐         ┌────▼──────────┐           │
    │          │         │  USB-to-TTL   │           │
    │ Arduino  │         │   Adapter     │           │
    │   Uno    │         └────┬──────────┘           │
    │          │              │                      │
    └──┬───┬───┘         ┌────▼──────────┐           │
       │   │             │   RPLIDAR A1  │ ◄─────────┘
    A0 │   │ A1          │               │   External 5V
       │   │             │ 360° Scanner  │   500mA min
       │   │             └───────────────┘
       │   │
   ┌───▼───▼───────────────────────────┐
   │  PW    PW     GND   +5V    RX/TX  │
   │  ↓     ↓      ↓     ↓      ↓      │
   │ ┌──┐ ┌──┐   ┌──┐  ┌──┐   ┌──┐     │
   │ │S1│ │S2│   Common Power  Chain   │
   │ └──┘ └──┘   Supply  Supply Logic  │
   │                                   │
   │  MB1300 Ultrasonic Sensors        │
   │  (Chained Configuration)          │
   └───────────────────────────────────┘
```
    A0 │   │ A1          │               │   External 5V
       │   │             │ 360° Scanner  │   500mA min
       │   │             └───────────────┘
       │   │
   ┌───▼───▼───────────────────────────┐
   │  PW    PW     GND   +5V    RX/TX  │
   │  ↓     ↓      ↓     ↓      ↓      │
   │ ┌──┐ ┌──┐   ┌──┐  ┌──┐   ┌──┐     │
   │ │S1│ │S2│   Common Power  Chain   │
   │ └──┘ └──┘   Supply  Supply Logic  │
   │                                   │
   │  MB1300 Ultrasonic Sensors        │
   │  (Chained Configuration)          │
   └───────────────────────────────────┘
```

## Component Pinouts

### 1. MB1300 Ultrasonic Sensor Pinout

```
┌─────────────────────────────────┐
│      MB1300 XL-MaxSonar-AE      │
│  (Looking at connector pins)    │
│                                 │
│  Pin 1: [BW] - Leave open       │
│  Pin 2: [PW] - Echo envelope ◄──┼── Connect to Arduino A0/A1
│  Pin 3: [AN] - Leave open       │
│  Pin 4: [RX] - Serial input  ◄──┼── For chaining
│  Pin 5: [TX] - Serial output ───┼── For chaining
│  Pin 6: [+5] - Power (+5V)   ◄──┼── Arduino 5V
│  Pin 7: [GND] - Ground       ◄──┼── Arduino GND
└─────────────────────────────────┘

PW Pin Output (Pin 2):
  - Acoustic envelope profile
  - 0-5V analog signal
  - Sampled at 50µs intervals
  - 240 samples per trigger = 12ms = ~2m range
```

### 2. Arduino Uno Pinout

```
┌─────────────────────────────────────┐
│         Arduino Uno                 │
├─────────────────────────────────────┤
│  Digital Pins:                      │
│    D0  - USB Serial RX (don't use)  │
│    D1  - USB Serial TX (don't use)  │
│    D2  - Available                  │
│    ...                              │
│                                     │
│  Analog Pins (10-bit ADC):          │
│    A0  - Sensor 1 PW input ◄────────┼── MB1300 #1 Pin 2
│    A1  - Sensor 2 PW input ◄────────┼── MB1300 #2 Pin 2
│    A2  - Available                  │
│    A3  - Available                  │
│    A4  - I2C SDA (available)        │
│    A5  - I2C SCL (available)        │
│                                     │
│  Power:                             │
│    5V  - Sensor power out ──────────┼── MB1300 Pin 6 (+5V)
│    GND - Common ground ─────────────┼── MB1300 Pin 7 (GND)
│    VIN - Not used                   │
│                                     │
│  USB Port: ─────────────────────────┼── Orange Pi USB (data + power)
└─────────────────────────────────────┘
```

### 3. RPLIDAR A1 Pinout

```
┌─────────────────────────────────────────────┐
│              RPLIDAR A1M8                   │
│  (7-pin connector on motor housing)         │
├─────────────────────────────────────────────┤
│  Pin 1: [GND]     - Ground          (Black) │◄── USB Adapter GND
│  Pin 2: [+5V]     - Power 5V 500mA  (Red)   │◄── External 5V supply
│  Pin 3: [TX]      - UART TX         (Green) │──► USB Adapter RX
│  Pin 4: [RX]      - UART RX         (White) │◄── USB Adapter TX
│  Pin 5: [MOTOR]   - Motor PWM       (Blue)  │    (leave disconnected)
│  Pin 6: [GND]     - Ground          (Black) │◄── USB Adapter GND
│  Pin 7: [+5V]     - Power           (Red)   │◄── External 5V supply
└─────────────────────────────────────────────┘

USB-to-TTL Adapter:
  VCC → External 5V power supply (500mA min)
  GND → RPLIDAR Pins 1,6 + Power supply GND
  RX  → RPLIDAR Pin 3 (TX)
  TX  → RPLIDAR Pin 4 (RX)
  USB → Orange Pi USB port

IMPORTANT: RPLIDAR draws up to 500mA. Use external 
power supply, not Arduino or unpowered USB hub!
```

### 4. USB-to-Serial Adapter (for RPLIDAR)

```
┌──────────────────────────────┐
│  CP2102 / CH340 Adapter      │
├──────────────────────────────┤
│  VCC  → Not connected        │  (Use external 5V instead)
│  GND  → RPLIDAR GND + PSU    │
│  TXD  → RPLIDAR RX (Pin 4)   │
│  RXD  → RPLIDAR TX (Pin 3)   │
│  USB  → Orange Pi USB        │
└──────────────────────────────┘
```

## Wiring Tables

### Sensor 1 (Left Corner) Connections

| MB1300 Pin | Signal | Wire Color | Connect To |
|------------|--------|------------|------------|
| Pin 1 (BW) | Bandwidth | - | Leave open |
| Pin 2 (PW) | Echo envelope | White/Signal | Arduino A0 |
| Pin 3 (AN) | Analog voltage | - | Leave open |
| Pin 4 (RX) | Serial RX | - | Via 1kΩ to S2 TX |
| Pin 5 (TX) | Serial TX | - | Via 1kΩ to Arduino D2 |
| Pin 6 (+5) | Power | Red | Arduino 5V |
| Pin 7 (GND) | Ground | Black | Arduino GND |

### Sensor 2 (Right Corner) Connections

| MB1300 Pin | Signal | Wire Color | Connect To |
|------------|--------|------------|------------|
| Pin 1 (BW) | Bandwidth | - | Leave open |
| Pin 2 (PW) | Echo envelope | White/Signal | Arduino A1 |
| Pin 3 (AN) | Analog voltage | - | Leave open |
| Pin 4 (RX) | Serial RX | - | Direct to Arduino D2 |
| Pin 5 (TX) | Serial TX | - | Via 1kΩ to S1 RX |
| Pin 6 (+5) | Power | Red | Arduino 5V |
| Pin 7 (GND) | Ground | Black | Arduino GND |

### RPLIDAR Connections

| RPLIDAR Pin | Signal | Wire Color | Connect To |
|-------------|--------|------------|------------|
| Pin 1 (GND) | Ground | Black | USB Adapter GND + PSU GND |
| Pin 2 (+5V) | Power | Red | External 5V 500mA supply |
| Pin 3 (TX) | UART TX | Green | USB Adapter RX |
| Pin 4 (RX) | UART RX | White | USB Adapter TX |
| Pin 5 (MOTOR) | PWM | Blue | Leave open (full speed) |
| Pin 6 (GND) | Ground | Black | USB Adapter GND + PSU GND |
| Pin 7 (+5V) | Power | Red | External 5V 500mA supply |

## Sensor Chaining Diagram

```
    Arduino D2 (Trigger)
         │
         ├─────────────────┐
         │                 │
    1kΩ resistor      Direct wire
         │                 │
         ▼                 ▼
    ┌────────┐        ┌────────┐
    │   S1   │        │   S2   │
    │  (TX)  │        │  (RX)  │
    └────┬───┘        └────────┘
         │
    1kΩ resistor
         │
         ▼
    ┌────────┐
    │   S2   │
    │  (RX)  │
    └────────┘

Trigger Sequence:
1. Arduino D2 sends trigger pulse
2. S2 receives trigger, starts ranging
3. After 110ms, S2 triggers S1 via serial
4. S1 ranges
5. Arduino samples PW pins during ranging
```

## Physical Mounting Guidelines

### RPLIDAR Mounting

```
┌─────────────────────────────────┐
│         Top View                 │
│                                  │
│  Mount RPLIDAR at exact center:  │
│  - X = 0 (37.47cm from L/R)     │
│  - Y = 0 (66.5cm from F/B)      │
│  - Center of 74.93×132.99cm box │
│                                  │
│  Height: At platform level       │
│  Orientation: Scan plane level   │
│  Cable: Route to side/rear      │
│                                  │
│  Mounting options:               │
│  - Surface mount on platform    │
│  - Standoff/bracket             │
│  - Tripod at platform level     │
│                                  │
│  Ultrasonic sensors mounted:    │
│  - ON front edge of platform    │
│  - At same height as RPLIDAR    │
│  - 66.5cm forward from RPLIDAR  │
└─────────────────────────────────┘
```

### Ultrasonic Sensor Mounting

```
Front Edge View (Looking Down from Above):

    ┌────────────────────────────────┐
    │  Front Edge (74.93cm / 29.5")  │
    └────────────────────────────────┘
    S1                           S2
    ──►                         ◄──
   30° ╲                       ╱ 150°
        ╲                     ╱
         ╲    Converging    ╱
          ╲    Beams       ╱
           ╲              ╱
            ╲            ╱
             ╲          ╱
              ╲        ╱
               ╲      ╱
                ╲    ╱
                 ╲  ╱
                  ╲╱
                  ╳  ← Beams cross in forward area
                 ╱ ╲
                ╱   ╲
               ╱     ╲
    (Interior of box below)

Side View:

         S1          RPLIDAR          S2
         │              │              │
         │              │              │
    ┌────●──────────────○──────────────●────┐
    │   Front        Center          Front  │  ← Platform surface
    │   Edge         (0,0)           Edge   │
    │                                       │
    │           132.99cm long               │
    │           (52.36")                    │
    └───────────────────────────────────────┘

Mounting notes:
- Sensors: Mounted directly ON front edge of platform
- S1 position: Left end of front edge (-37.47cm, +66.5cm)
- S2 position: Right end of front edge (+37.47cm, +66.5cm)
- Height: Same as RPLIDAR scan plane (both at platform level)
- S1 orientation: Pointing 30° (inward-right-forward)
- S2 orientation: Pointing 150° (inward-left-forward)
- Sensors face each other across platform front
- Secure: Prevent vibration
- Clear FOV: No obstructions in beam paths
- Cable management: Route along edges to center
- Beams overlap in forward center area
```

## Power Requirements

| Component | Voltage | Current | Power | Notes |
|-----------|---------|---------|-------|-------|
| Arduino Uno | 5V USB | ~50mA | 0.25W | Powered via USB from Orange Pi |
| MB1300 Sensor 1 | 5V | 50mA | 0.25W | From Arduino 5V rail |
| MB1300 Sensor 2 | 5V | 50mA | 0.25W | From Arduino 5V rail |
| RPLIDAR A1 | 5V | 500mA max | 2.5W | **External supply required** |
| **Total** | 5V | **~650mA** | **3.25W** | RPLIDAR needs separate supply |

### Power Supply Recommendations

1. **Arduino + Sensors**: Powered via USB from Orange Pi (adequate for 100mA total)
2. **RPLIDAR**: Use dedicated 5V 1A power supply or powered USB hub
3. **Common ground**: Connect all GND together for signal integrity

## Cable Lengths

| Connection | Recommended Length | Max Length | Notes |
|------------|-------------------|------------|-------|
| Sensor 1 → Arduino | 50-100cm | 2m | Keep short, analog signal |
| Sensor 2 → Arduino | 50-100cm | 2m | Keep short, analog signal |
| Arduino → Orange Pi | 1-2m | 3m | Standard USB cable |
| RPLIDAR → Orange Pi | 1-2m | 5m | USB-to-Serial adapter |

## Device Addresses

| Device | Connection | Port | Baud Rate |
|--------|-----------|------|-----------|
| Arduino Uno | USB Serial | `/dev/ttyACM0` | 115200 |
| RPLIDAR A1 | USB-Serial | `/dev/ttyUSB0` | 115200 |

Check actual ports on Orange Pi:
```bash
ls -l /dev/tty{ACM,USB}*
```

## System Startup Sequence

1. **Power on Orange Pi** (powers Arduino via USB)
2. **Connect RPLIDAR** to external 5V supply
3. **Wait 2 seconds** for Arduino reset
4. **RPLIDAR motor** starts spinning automatically
5. **Start data collection**:
   ```bash
   python data_collector_with_lidar.py --duration 120
   ```

## Testing Checklist

### Hardware Tests

- [ ] RPLIDAR motor spinning
- [ ] RPLIDAR USB detected (`/dev/ttyUSB0`)
- [ ] Arduino USB detected (`/dev/ttyACM0`)
- [ ] Both ultrasonic sensors powered (LEDs on)
- [ ] No loose connections
- [ ] Clear FOV for all sensors
- [ ] Common ground connected
- [ ] RPLIDAR on external power (not Arduino 5V)

### Software Tests

```bash
# Test Arduino
cat /dev/ttyACM0  # Should see "S,..." data

# Test RPLIDAR
python3 -c "from rplidar import RPLidar; print(RPLidar('/dev/ttyUSB0').get_info())"

# Test synchronized collection
python data_collector_with_lidar.py --duration 10
```

### Verification

- [ ] Ultrasonic data streaming (check terminal output)
- [ ] RPLIDAR scans updating (check terminal output)
- [ ] Match rate > 80% (check progress reports)
- [ ] CSV file created in `data/` directory
- [ ] LIDAR positions reasonable (check CSV)

## Troubleshooting Quick Reference

| Issue | Check | Solution |
|-------|-------|----------|
| No RPLIDAR data | Motor spinning? | Check external power supply |
| No Arduino data | USB connected? | Check `/dev/ttyACM0` exists |
| Low match rate | Timing alignment | Increase `sync.window_ms` in config |
| Permission error | User in dialout group | `sudo  (center of box), not platform corner
- **RPLIDAR position**: Center of 74.93cm × 132.99cm rectangular platform at (0, 0)
- **Sensor positions**: Both mounted ON the front edge (short side) of the box
- **Sensor angles** are measured from positive X-axis (0° = right, 90° = forward)
- **Sensors face each other** at 30° and 150° with converging beams
- **Overlapping coverage** in forward center area (60° to 120°)
- **All sensors at same height**: RPLIDAR and ultrasonics at platform level

- **Coordinate system origin** is at RPLIDAR center, not platform corner
- **Sensor angles** are measured from positive X-axis (0° = right)
- **Sensors face each other** at 30° and 150° with converging beams
- **Overlapping coverage** in forward center area (60° to 120°)
- **RPLIDAR scan plane** should be at same height as ultrasonic sensors
- **External power** for RPLIDAR is mandatory - Arduino cannot supply enough current

## References

- [MB1300 Datasheet](https://maxbotix.com/pages/xl-maxsonar-ae-datasheet)
- [RPLIDAR A1 Manual](https://www.slamtec.com/en/Lidar/A1)
- [Arduino Uno Pinout](https://docs.arduino.cc/hardware/uno-rev3)
- System configuration: [config.yaml](config.yaml)
- Wiring details: [WIRING_CHAINED.md](WIRING_CHAINED.md)
- Setup guide: [RPLIDAR_SETUP.md](RPLIDAR_SETUP.md)
