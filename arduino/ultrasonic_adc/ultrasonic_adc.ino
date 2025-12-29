/*
 * Ultrasonic Echo Profiler for MB1300 Sensors
 * 
 * This sketch captures the acoustic echo envelope from MB1300 ultrasonic sensors
 * using the PW (Pin 2) output with sensor chaining to prevent interference.
 * 
 * MB1300 Specifications:
 * - Range: 300mm to 5000mm
 * - PW Output: Analog envelope of acoustic waveform
 * - Provides echo strength vs time for spatial profiling
 * - Update Rate: ~49ms per sensor in chaining mode
 * 
 * Echo Profiling Method:
 * - Uses PW pin instead of AN pin to capture raw acoustic returns
 * - Samples PW output rapidly after trigger to build spatial profile
 * - Each sample represents echo amplitude at a specific distance
 * - 240 samples at 50µs intervals = 1cm resolution over 2m range
 * 
 * Chaining Method:
 * - Pin 1 (BW) held LOW enables pulse output on Pin 5 (TX)
 * - Each sensor's TX triggers the next sensor's RX via 1kΩ resistor
 * - Prevents acoustic interference by ensuring sequential operation
 * - Arduino triggers first sensor by pulsing its RX pin HIGH for 20µS
 * 
 * Protocol:
 * Commands from Orange Pi:
 *   START:<samples>\n - Start data collection with specified samples per trigger
 *   STOP\n - Stop data collection
 *   CONFIG:<samples>\n - Update samples per trigger
 * 
 * Data Output Format:
 *   S,<timestamp_ms>,<sensor1_r1>,<sensor1_r2>,...,<sensor2_r1>,<sensor2_r2>,...\n
 */

// Configuration
const int NUM_SENSORS = 2;
const int SENSOR_PINS[] = {A0, A1};  // Analog pins for sensor AN outputs
const int TRIGGER_PIN = 2;           // Digital pin to trigger first sensor's RX
const int READINGS_PER_TRIGGER = 240; // 240 readings for 2m range at ~1cm resolution
const unsigned long SAMPLING_INTERVAL = 100; // ms between sample cycles (sensors fire sequentially)
const unsigned long SAMPLE_DELAY_US = 50; // 50us between samples (~1cm resolution)

// State variables
bool isCollecting = false;
int samplesPerTrigger = 10;
int currentSample = 0;
unsigned long lastSampleTime = 0;
unsigned long triggerStartTime = 0;

// Data buffer
struct SensorReading {
  unsigned long timestamp;
  int values[NUM_SENSORS];
};

void setup() {
  Serial.begin(115200);
  
  // Enable fast ADC mode (prescaler 32 for ~50us per reading)
  // Default prescaler is 128 (~100us per reading)
  // Prescaler 32 gives ~50us per reading for 1cm resolution
  ADCSRA &= ~0x07;  // Clear prescaler bits
  ADCSRA |= 0x05;   // Set prescaler to 32 (16MHz/32 = 500kHz ADC clock)
  
  // Initialize analog pins
  for (int i = 0; i < NUM_SENSORS; i++) {
    pinMode(SENSOR_PINS[i], INPUT);
  }
  
  // Initialize trigger pin for first sensor's RX
  pinMode(TRIGGER_PIN, OUTPUT);
  digitalWrite(TRIGGER_PIN, LOW);  // Start LOW
  
  // Wait for serial connection
  while (!Serial) {
    ; // Wait for serial port to connect
  }
  
  Serial.println("READY");
  Serial.print("NUM_SENSORS:");
  Serial.println(NUM_SENSORS);
  Serial.println("MODE:AN_CHAINED");
}

void loop() {
  // Check for commands from Orange Pi
  if (Serial.available() > 0) {
    processCommand();
  }
  
  // Collect data if enabled
  if (isCollecting) {
    unsigned long currentTime = millis();
    
    // Check if it's time for next sample
    if (currentTime - lastSampleTime >= SAMPLING_INTERVAL) {
      // collectSample will trigger and capture echo profile
      collectSample(currentTime);
      lastSampleTime = currentTime;
      currentSample++;
      
      // Check if we've completed a trigger cycle
      if (currentSample >= samplesPerTrigger) {
        currentSample = 0;
        triggerStartTime = currentTime;
      }
    }
  }
}

void triggerSensorChain() {
  // Pulse the first sensor's RX pin high for 20µS to start the chain
  digitalWrite(TRIGGER_PIN, HIGH);
  delayMicroseconds(20);
  digitalWrite(TRIGGER_PIN, LOW);
  // Sensors will now fire sequentially via TX->RX chaining
}

void processCommand() {
  String command = Serial.readStringUntil('\n');
  command.trim();
  
  if (command.startsWith("START:")) {
    int samples = command.substring(6).toInt();
    if (samples > 0 && samples <= 100) {
      samplesPerTrigger = samples;
      isCollecting = true;
      currentSample = 0;
      triggerStartTime = millis();
      lastSampleTime = triggerStartTime;
      Serial.println("ACK:STARTED");
    } else {
      Serial.println("ERROR:INVALID_SAMPLES");
    }
  } 
  else if (command == "STOP") {
    isCollecting = false;
    currentSample = 0;
    Serial.println("ACK:STOPPED");
  }
  else if (command.startsWith("CONFIG:")) {
    int samples = command.substring(7).toInt();
    if (samples > 0 && samples <= 100) {
      samplesPerTrigger = samples;
      Serial.println("ACK:CONFIG_UPDATED");
    } else {
      Serial.println("ERROR:INVALID_SAMPLES");
    }
  }
  else {
    Serial.println("ERROR:UNKNOWN_COMMAND");
  }
}

void collectSample(unsigned long timestamp) {
  // Collect echo envelope readings for spatial profiling
  int readings[NUM_SENSORS][READINGS_PER_TRIGGER];
  
  // Trigger and wait for ultrasonic burst transmission (~300µs)
  triggerSensorChain();
  delayMicroseconds(300);
  
  // Now capture echo returns as they arrive
  // Start timing from when echoes begin (after transmission)
  unsigned long startTime = micros();
  
  // Sample PW pins at precise intervals to capture echo envelope
  // Each 50µs interval corresponds to ~0.86cm of distance (round-trip)
  for (int reading = 0; reading < READINGS_PER_TRIGGER; reading++) {
    unsigned long targetTime = startTime + (reading * SAMPLE_DELAY_US);
    
    // Read PW envelope for all sensors
    for (int sensor = 0; sensor < NUM_SENSORS; sensor++) {
      readings[sensor][reading] = analogRead(SENSOR_PINS[sensor]);
    }
    
    // Precise timing - wait until next sample time
    while (micros() < targetTime + SAMPLE_DELAY_US) {
      // Tight timing loop for accuracy
    }
  }
  
  // Send data in CSV format: S,timestamp,sensor1_r1,sensor1_r2,...,sensor2_r1,sensor2_r2,...
  Serial.print("S,");
  Serial.print(timestamp);
  for (int sensor = 0; sensor < NUM_SENSORS; sensor++) {
    for (int reading = 0; reading < READINGS_PER_TRIGGER; reading++) {
      Serial.print(",");
      Serial.print(readings[sensor][reading]);
    }
  }
  Serial.println();
}

// Convert ADC value to distance in cm
// MB1300: (Vcc/1024) per cm
// For 5V: (ADC_value / 1024) * 5V / (5V / 1024) = ADC_value cm
// But actual scaling is: ADC_value * (Vcc/1024) = distance in cm
// For 5V: distance_cm = ADC_value * (5.0/1024) / (5.0/1024) = ADC_value
// Simplified: ADC reads directly as ~cm (with ADC scaling factor)
float adcToDistance(int adcValue) {
  // MB1300: (Vcc/1024) per cm at 5V
  // This gives roughly 1 ADC unit per cm
  return adcValue;  // Approximation: ADC value ≈ distance in cm
}
