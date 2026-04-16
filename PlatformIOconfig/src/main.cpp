/*
 * ESP32 WROOM - Temperature & Humidity MQTT Publisher
 * PlatformIO Version
 *
 * Reads DHT11 sensor data and publishes to MQTT broker
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <AccelStepper.h>

// WiFi Configuration
const char *ssid = "HTL-Weiz";
const char *password = "HTL-Weiz";

// MQTT Broker Configuration
const char *mqtt_server = "172.31.183.207"; // e.g., "192.168.1.100" or "broker.hivemq.com"
const int mqtt_port = 1883;
const char *mqtt_user = "";     // Leave empty "" if no authentication
const char *mqtt_password = ""; // Leave empty "" if no authentication
const char *mqtt_client_id = "ESP32_DHT_Sensor";

// MQTT Topics
const char *topic_temperature = "home/sensor/temperature";
const char *topic_humidity = "home/sensor/humidity";
const char *topic_temperature_f = "home/sensor/temperature_f";
const char *topic_heat_index = "home/sensor/heat_index";
const char *topic_status = "home/sensor/status";
const char *topic_error = "home/sensor/error";
const char *topic_debug = "home/sensor/debug";
const char *topic_motor_command = "home/sensor/motor/command";
const char *topic_motor_status = "home/sensor/motor/status";
const char *topic_motion_status = "home/sensor/motion/status";
const char *topic_buzzer_status = "home/sensor/buzzer/status";
const char *topic_buzzer_command = "home/sensor/buzzer/command";

// DHT11 Sensor Configuration
#define DHTPIN 4      // GPIO pin connected to DHT11 data pin
#define DHTTYPE DHT11 // DHT 11 sensor
DHT dht(DHTPIN, DHTTYPE);

// Buzzer Configuration (active buzzer B27)
#define BUZZER_PIN 21 // 21 actual

// RGB LED Configuration
// NOTE: GPIO 34 and 35 are input-only on ESP32 — reassign red/green to output-capable pins
#define LED_RED_PIN 32
#define LED_GREEN_PIN 19
#define LED_BLUE_PIN 18 

// Motion Sensor Configuration
#define MOTION_PIN 25 // GPIO pin connected to motion sensor (HIGH = motion detected)

// Stepper Motor Configuration
// Choose your motor type by uncommenting ONE of the following:
#define MOTOR_28BYJ48 // 28BYJ-48 with ULN2003 driver (most common)
// #define MOTOR_NEMA17   // NEMA 17 with A4988/DRV8825 driver

#ifdef MOTOR_28BYJ48
// 28BYJ-48 Motor with ULN2003 Driver
// Connect: IN1->GPIO13, IN2->GPIO12, IN3->GPIO14, IN4->GPIO27
#define MOTOR_PIN1 13
#define MOTOR_PIN2 12
#define MOTOR_PIN3 14
#define MOTOR_PIN4 27
#define STEPS_PER_REVOLUTION 2048 // 28BYJ-48 in half-step mode
AccelStepper stepper(AccelStepper::HALF4WIRE, MOTOR_PIN1, MOTOR_PIN3, MOTOR_PIN2, MOTOR_PIN4);
#endif

#ifdef MOTOR_NEMA17
// NEMA 17 Motor with A4988/DRV8825 Driver
// Connect: STEP->GPIO13, DIR->GPIO12
#define MOTOR_STEP_PIN 13
#define MOTOR_DIR_PIN 12
#define STEPS_PER_REVOLUTION 200 // NEMA 17 (1.8° per step)
AccelStepper stepper(AccelStepper::DRIVER, MOTOR_STEP_PIN, MOTOR_DIR_PIN);
#endif

// Motor control variables
bool motorRunning = false;
long targetSteps = 0;

// Motion sensor cooldown
unsigned long lastMotionTime = 0;
const long MOTION_COOLDOWN = 5000; // ms to wait before re-triggering after motor stops
bool lastMotionState = false;      // track state changes for MQTT publishing

// Buzzer beep pattern variables
bool buzzerActive = false;      // whether buzzer should be beeping
bool buzzerState = false;       // current on/off state
const long BEEP_ON_TIME = 400;  // ms buzzer is on
const long BEEP_OFF_TIME = 400; // ms buzzer is off (pause)
unsigned long lastBuzzerToggle = 0;

// RGB color variables
uint8_t ledRed = 0;
uint8_t ledGreen = 0;
uint8_t ledBlue = 0;

// Timing Configuration
const long reading_interval = 10000; // Read sensor every 10 seconds
unsigned long lastReadTime = 0;

// WiFi and MQTT Clients
WiFiClient espClient;
PubSubClient client(espClient);

// Function declarations
void setup_wifi();
void reconnect_mqtt();
void mqtt_callback(char *topic, byte *payload, unsigned int length);
void read_and_publish_sensor_data();
void handle_motor_command(String command);
void motor_start(long steps);
void motor_stop();
void update_motor();
void setRandomColor();
void setLEDColor(uint8_t r, uint8_t g, uint8_t b);
void buzzer_on();
void buzzer_off();
void update_buzzer();

void setup()
{
  Serial.begin(115200);
  delay(100);

  Serial.println("\n\nESP32 Temperature & Humidity MQTT Publisher");
  Serial.println("===========================================");

  // Initialize DHT sensor
  dht.begin();
  Serial.println("DHT sensor initialized");

  // Initialize Buzzer (active buzzer B27 - digital on/off)
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  Serial.println("Buzzer initialized");

  // Initialize RGB LED
  pinMode(LED_RED_PIN, OUTPUT);
  pinMode(LED_GREEN_PIN, OUTPUT);
  pinMode(LED_BLUE_PIN, OUTPUT);
    setLEDColor(0, 0, 0);
  Serial.println("RGB LED initialized");

  // Initialize Motion Sensor
  pinMode(MOTION_PIN, INPUT_PULLDOWN);
  Serial.println("Motion sensor initialized");

  // Initialize Stepper Motor
  stepper.setMaxSpeed(1000);    // Max speed in steps/second
  stepper.setAcceleration(500); // Acceleration in steps/second²
  stepper.setSpeed(1000);       // Speed in steps/second
  Serial.println("Stepper motor initialized");
  Serial.print("Steps per revolution: ");
  Serial.println(STEPS_PER_REVOLUTION);

  // Connect to WiFi
  setup_wifi();

  // Configure MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqtt_callback);

  Serial.println("Setup complete!");
}

void loop()
{
  // Ensure MQTT connection
  if (!client.connected())
  {
    reconnect_mqtt();
  }
  client.loop();

  // Check motion sensor and publish raw state for debugging
  bool motionNow = digitalRead(MOTION_PIN) == HIGH;
  if (motionNow != lastMotionState)
  {
    lastMotionState = motionNow;
    client.publish(topic_motion_status, motionNow ? "detected" : "clear", true);
    Serial.print("Motion pin state: ");
    Serial.println(motionNow ? "HIGH" : "LOW");
  }

  // Trigger motor when motion detected (with cooldown)
  if (motionNow && !motorRunning &&
      (millis() - lastMotionTime >= MOTION_COOLDOWN))
  {
    lastMotionTime = millis();
    Serial.println("Motion detected! Starting motor.");
    motor_start(STEPS_PER_REVOLUTION);
    client.publish(topic_motor_status, "running");
    client.publish(topic_debug, "Motion detected - motor started");
  }

  // Update motor and buzzer (must be called frequently)
  update_motor();
  update_buzzer();

  // Read and publish sensor data at specified interval
  unsigned long currentTime = millis();
  if (currentTime - lastReadTime >= reading_interval)
  {
    lastReadTime = currentTime;
    read_and_publish_sensor_data();
  }
}

void setup_wifi()
{
  delay(10);
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30)
  {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal strength (RSSI): ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");

    // Note: Can't publish to MQTT yet as it's not connected
    // WiFi info will be sent after MQTT connects
  }
  else
  {
    Serial.println("\nWiFi connection failed!");
    Serial.println("Restarting ESP32...");
    delay(3000);
    ESP.restart();
  }
}

void reconnect_mqtt()
{
  // Loop until we're reconnected
  while (!client.connected())
  {
    Serial.print("Attempting MQTT connection...");

    // Attempt to connect
    bool connected;
    if (strlen(mqtt_user) > 0)
    {
      // Connect with authentication
      connected = client.connect(mqtt_client_id, mqtt_user, mqtt_password);
    }
    else
    {
      // Connect without authentication
      connected = client.connect(mqtt_client_id);
    }

    if (connected)
    {
      Serial.println("connected!");
      // Publish connection status
      client.publish(topic_status, "online", true);
      client.publish(topic_debug, "ESP32 connected to MQTT broker", true);

      // Publish initial values
      client.publish(topic_temperature, "0", true);
      client.publish(topic_humidity, "0", true);
      client.publish(topic_temperature_f, "32", true);
      client.publish(topic_heat_index, "0", true);

      // Send startup message with sensor info
      String startup_msg = "DHT11 sensor initialized on GPIO ";
      startup_msg += DHTPIN;
      client.publish(topic_debug, startup_msg.c_str());

      // Send WiFi connection info
      String wifi_info = "WiFi: " + String(ssid) + " | IP: " + WiFi.localIP().toString() + " | RSSI: " + String(WiFi.RSSI()) + "dBm";
      client.publish(topic_debug, wifi_info.c_str());

      // Publish initial motor and buzzer status
      client.publish(topic_motor_status, "stopped", true);
      client.publish(topic_buzzer_status, "off", true);

      // Subscribe to command topics
      client.subscribe(topic_motor_command);
      client.subscribe(topic_buzzer_command);
      Serial.print("Subscribed to: ");
      Serial.println(topic_motor_command);
      Serial.println(topic_buzzer_command);
    }
    else
    {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 5 seconds");
      delay(5000);
    }
  }
}

void mqtt_callback(char *topic, byte *payload, unsigned int length)
{
  // Handle incoming MQTT messages
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("]: ");

  String message;
  for (unsigned int i = 0; i < length; i++)
  {
    message += (char)payload[i];
  }
  Serial.println(message);

  if (String(topic) == topic_motor_command)
  {
    handle_motor_command(message);
  }
  else if (String(topic) == topic_buzzer_command)
  {
    message.toLowerCase();
    message.trim();
    if (message == "on")
    {
      buzzer_on();
      client.publish(topic_buzzer_status, "on", true);
    }
    else if (message == "off")
    {
      buzzer_off();
      client.publish(topic_buzzer_status, "off", true);
    }
  }
}

void read_and_publish_sensor_data()
{
  // Send debug message that reading is starting
  client.publish(topic_debug, "Reading sensor data...");

  // Reading temperature or humidity takes about 250 milliseconds!
  // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)

  // Read humidity
  float h = dht.readHumidity();
  // Read temperature as Celsius (the default)
  float t = dht.readTemperature();
  // Read temperature as Fahrenheit (isFahrenheit = true)
  float f = dht.readTemperature(true);

  // Check if any reads failed and exit early (to try again)
  if (isnan(h) || isnan(t) || isnan(f))
  {
    String error_msg = "Failed to read from DHT sensor! Check wiring and connections.";
    Serial.println(error_msg);

    // Publish error to MQTT
    client.publish(topic_error, error_msg.c_str());
    client.publish(topic_status, "error");

    return;
  }

  // Compute heat index in Fahrenheit (the default)
  float hif = dht.computeHeatIndex(f, h);
  // Compute heat index in Celsius (isFahrenheit = false)
  float hic = dht.computeHeatIndex(t, h, false);

  // Display readings to Serial (detailed format like example)
  Serial.println("\n========================================");
  Serial.println("--- DHT11 Sensor Reading ---");
  Serial.print("Humidity: ");
  Serial.print(h);
  Serial.print("%  Temperature: ");
  Serial.print(t);
  Serial.print("°C / ");
  Serial.print(f);
  Serial.println("°F");
  Serial.print("Heat index: ");
  Serial.print(hic);
  Serial.print("°C / ");
  Serial.print(hif);
  Serial.println("°F");
  Serial.println("========================================");

  // Convert to strings for MQTT publishing
  char temp_c_str[8];
  char temp_f_str[8];
  char hum_str[8];
  char heat_index_str[8];

  dtostrf(t, 6, 2, temp_c_str);
  dtostrf(f, 6, 2, temp_f_str);
  dtostrf(h, 6, 2, hum_str);
  dtostrf(hic, 6, 2, heat_index_str);

  // Publish all data to MQTT
  bool temp_c_published = client.publish(topic_temperature, temp_c_str);
  bool temp_f_published = client.publish(topic_temperature_f, temp_f_str);
  bool hum_published = client.publish(topic_humidity, hum_str);
  bool heat_published = client.publish(topic_heat_index, heat_index_str);

  // Check if all publishes succeeded
  if (temp_c_published && temp_f_published && hum_published && heat_published)
  {
    Serial.println("✓ All data published successfully to MQTT!");
    client.publish(topic_status, "online");

    // Send detailed debug message
    String debug_msg = "Published: Temp=" + String(t) + "°C/" + String(f) + "°F, Humidity=" + String(h) + "%, HeatIndex=" + String(hic) + "°C";
    client.publish(topic_debug, debug_msg.c_str());
  }
  else
  {
    Serial.println("✗ Failed to publish some data to MQTT!");

    // Publish specific error
    String error_msg = "MQTT publish failed - ";
    if (!temp_c_published)
      error_msg += "temp_c ";
    if (!temp_f_published)
      error_msg += "temp_f ";
    if (!hum_published)
      error_msg += "humidity ";
    if (!heat_published)
      error_msg += "heat_index";

    client.publish(topic_error, error_msg.c_str());
  }

  // Optional: Publish as JSON (single topic with all data)
  /*
  String json_payload = "{";
  json_payload += "\"temperature_c\":" + String(t) + ",";
  json_payload += "\"temperature_f\":" + String(f) + ",";
  json_payload += "\"humidity\":" + String(h) + ",";
  json_payload += "\"heat_index_c\":" + String(hic) + ",";
  json_payload += "\"heat_index_f\":" + String(hif);
  json_payload += "}";
  client.publish("home/sensor/data", json_payload.c_str());
  Serial.println("JSON: " + json_payload);
  */
}

// ========================================
// STEPPER MOTOR CONTROL FUNCTIONS
// ========================================

void handle_motor_command(String command)
{
  Serial.println("Processing motor command: " + command);
  command.toLowerCase();
  command.trim();

  if (command == "start")
  {
    // Start motor - one full revolution
    motor_start(STEPS_PER_REVOLUTION);
    client.publish(topic_motor_status, "running");
    client.publish(topic_debug, "Motor started - 1 revolution");
  }
  else if (command == "stop")
  {
    // Stop motor immediately
    motor_stop();
    client.publish(topic_motor_status, "stopped");
    client.publish(topic_debug, "Motor stopped");
  }
  else if (command.startsWith("steps:"))
  {
    // Run specific number of steps: "steps:1000"
    String stepsStr = command.substring(6);
    long steps = stepsStr.toInt();
    motor_start(steps);

    String msg = "Motor started - " + String(steps) + " steps";
    client.publish(topic_motor_status, "running");
    client.publish(topic_debug, msg.c_str());
  }
  else if (command.startsWith("rotate:"))
  {
    // Rotate specific degrees: "rotate:360" or "rotate:-180"
    String degreesStr = command.substring(7);
    float degrees = degreesStr.toFloat();
    long steps = (long)(degrees * STEPS_PER_REVOLUTION / 360.0);
    motor_start(steps);

    String msg = "Motor rotating " + String(degrees) + "° (" + String(steps) + " steps)";
    client.publish(topic_motor_status, "running");
    client.publish(topic_debug, msg.c_str());
  }
  else if (command.startsWith("revolutions:"))
  {
    // Run specific number of revolutions: "revolutions:5" or "revolutions:-2"
    String revsStr = command.substring(12);
    float revs = revsStr.toFloat();
    long steps = (long)(revs * STEPS_PER_REVOLUTION);
    motor_start(steps);

    String msg = "Motor started - " + String(revs) + " revolutions (" + String(steps) + " steps)";
    client.publish(topic_motor_status, "running");
    client.publish(topic_debug, msg.c_str());
  }
  else if (command.startsWith("speed:"))
  {
    // Set motor speed: "speed:500"
    String speedStr = command.substring(6);
    int speed = speedStr.toInt();
    if (speed > 0 && speed <= 2000)
    {
      stepper.setMaxSpeed(speed);
      stepper.setSpeed(speed);

      String msg = "Motor speed set to " + String(speed) + " steps/sec";
      client.publish(topic_debug, msg.c_str());
    }
    else
    {
      client.publish(topic_error, "Invalid speed. Use 1-2000");
    }
  }
  else if (command == "status")
  {
    // Report current motor status
    String status = "Motor ";
    status += motorRunning ? "running" : "stopped";
    status += " | Position: " + String(stepper.currentPosition());
    status += " | Target: " + String(targetSteps);
    status += " | Speed: " + String(stepper.maxSpeed());
    client.publish(topic_debug, status.c_str());
  }
  else
  {
    // Unknown command
    String error_msg = "Unknown motor command: " + command;
    client.publish(topic_error, error_msg.c_str());

    // Send help message
    String help = "Valid commands: start, stop, steps:N, rotate:N, revolutions:N, speed:N, status";
    client.publish(topic_debug, help.c_str());
  }
}

void motor_start(long steps)
{
  targetSteps = steps;
  motorRunning = true;
  stepper.moveTo(stepper.currentPosition() + steps);
  buzzer_on();
  client.publish(topic_buzzer_status, "on", true);

  Serial.println("=== Motor Started ===");
  Serial.print("Steps: ");
  Serial.println(steps);
  Serial.print("From position: ");
  Serial.print(stepper.currentPosition());
  Serial.print(" to ");
  Serial.println(stepper.currentPosition() + steps);
  Serial.println("====================");
}

void motor_stop()
{
  motorRunning = false;
  buzzer_off();
  client.publish(topic_buzzer_status, "off", true);
  stepper.stop();
  stepper.setCurrentPosition(0); // Reset position counter

  Serial.println("=== Motor Stopped ===");
  Serial.print("Final position: ");
  Serial.println(stepper.currentPosition());
  Serial.println("=====================");
}

void update_motor()
{
  if (motorRunning)
  {
    // Run the motor (this must be called frequently)
    stepper.run();

    // Check if we've reached the target
    if (stepper.distanceToGo() == 0)
    {
      motorRunning = false;
      buzzer_off();
      client.publish(topic_buzzer_status, "off", true);

      Serial.println("=== Motor Completed ===");
      Serial.print("Final position: ");
      Serial.println(stepper.currentPosition());
      Serial.println("=======================");

      client.publish(topic_motor_status, "stopped");

      String msg = "Motor completed - Final position: " + String(stepper.currentPosition());
      client.publish(topic_debug, msg.c_str());

      // Reset position counter for next run
      stepper.setCurrentPosition(0);
    }
  }
}

// ========================================
// BUZZER CONTROL FUNCTIONS
// ========================================

void buzzer_on()
{
  buzzerActive = true;
  buzzerState = true;
  digitalWrite(BUZZER_PIN, HIGH);
  setRandomColor();
  lastBuzzerToggle = millis();
}

void buzzer_off()
{
  buzzerActive = false;
  buzzerState = false;
  digitalWrite(BUZZER_PIN, LOW);
  setLEDColor(0, 0, 0);
}

void setRandomColor()
{
  ledRed = random(0, 256);
  ledGreen = random(0, 256);
  ledBlue = random(0, 256);
  setLEDColor(ledRed, ledGreen, ledBlue);
}

void setLEDColor(uint8_t r, uint8_t g, uint8_t b)
{
  analogWrite(LED_RED_PIN, r);
  analogWrite(LED_GREEN_PIN, g);
  analogWrite(LED_BLUE_PIN, b);
}

void update_buzzer()
{
  if (!buzzerActive)
    return;

  unsigned long now = millis();
  unsigned long elapsed = now - lastBuzzerToggle;

  if (buzzerState && elapsed >= BEEP_ON_TIME)
  {
    buzzerState = false;
    digitalWrite(BUZZER_PIN, LOW);
    setLEDColor(0, 0, 0);
    lastBuzzerToggle = now;
  }
  else if (!buzzerState && elapsed >= BEEP_OFF_TIME)
  {
    buzzerState = true;
    digitalWrite(BUZZER_PIN, HIGH);
    setRandomColor();
    lastBuzzerToggle = now;
  }
}