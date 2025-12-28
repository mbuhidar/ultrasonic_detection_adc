/*
 * Ultrasonic ADC Reader for MB1300 Sensors
 * 
 * This sketch reads analog values from multiple MB1300 ultrasonic sensors
 * using AN Output Constantly Looping mode with sensor chaining to prevent
 * interference.
 * 
 * MB1300 Specifications:
 * - Range: 300mm to 5000mm (adjustable)
 * - AN Output: (Vcc/1024) per cm (~4.9mV/cm at 5V)
 * - Update Rate: ~49ms per sensor in chaining mode
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
 *   S,<timestamp_ms>,<sensor1_val>,<sensor2_val>,...\n
 */

// Configuration
const int NUM_SENSORS = 2;
const int SENSOR_PINS[] = {A0, A1};  // Analog pins for sensor AN outputs
const int TRIGGER_PIN = 2;           // Digital pin to trigger first sensor's RX
const int READINGS_PER_TRIGGER = 10; // Number of peak values to capture
const unsigned long SAMPLING_INTERVAL = 100; // ms between sample cycles (sensors fire sequentially)
const int SAMPLES_PER_PEAK = 50;     // Number of ADC samples to check for each peak
const unsigned long PEAK_WINDOW_US = 5000; // Microseconds to sample for each peak (5ms)

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
      // Trigger the sensor chain
      triggerSensorChain();
      
      // Wait for sensors to complete ranging (~49ms per sensor * NUM_SENSORS)
      delay(NUM_SENSORS * 50 + 10);  // Add 10ms buffer
      
      // Collect sample from all sensors
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
  // Collect peak values for each sensor across multiple return pulses
  int peakReadings[NUM_SENSORS][READINGS_PER_TRIGGER];
  
  // For each expected return pulse
  for (int reading = 0; reading < READINGS_PER_TRIGGER; reading++) {
    unsigned long windowStart = micros();
    unsigned long sampleDelay = PEAK_WINDOW_US / SAMPLES_PER_PEAK;
    
    // Initialize peak values to 0
    for (int sensor = 0; sensor < NUM_SENSORS; sensor++) {
      peakReadings[sensor][reading] = 0;
    }
    
    // Sample rapidly during this pulse window to find peak
    for (int sample = 0; sample < SAMPLES_PER_PEAK; sample++) {
      for (int sensor = 0; sensor < NUM_SENSORS; sensor++) {
        int value = analogRead(SENSOR_PINS[sensor]);
        if (value > peakReadings[sensor][reading]) {
          peakReadings[sensor][reading] = value;
        }
      }
      
      // Wait until next sample time
      while (micros() - windowStart < (sample + 1) * sampleDelay) {
        // Busy wait for precise timing
      }
    }
    
    // Small delay before next pulse window
    delayMicroseconds(1000);
  }
  
  // Send data in CSV format: S,timestamp,sensor1_peak1,sensor1_peak2,...,sensor2_peak1,sensor2_peak2,...
  Serial.print("S,");
  Serial.print(timestamp);
  for (int sensor = 0; sensor < NUM_SENSORS; sensor++) {
    for (int reading = 0; reading < READINGS_PER_TRIGGER; reading++) {
      Serial.print(",");
      Serial.print(peakReadings[sensor][reading]);
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
