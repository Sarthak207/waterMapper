#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// ---------- Wi-Fi + MQTT ----------
const char* ssid = "Ghatiya_clg";
const char* password = "1234Sart";
const char* mqtt_server = "192.168.243.34";

WiFiClient espClient;
PubSubClient client(espClient);

// ---------- Sensors ----------
#define FLOW_PIN 4      // D2
#define TRIG_PIN 14     // D5
#define ECHO_PIN 12     // D6
#define TDS_PIN A0

volatile int pulseCount = 0;
unsigned long lastSend = 0;

// YF-S401 approx (must calibrate)
const int pulsesPerLiter = 450;

// Interrupt handler
void IRAM_ATTR pulseCounter() {
  pulseCount++;
}

// ---------- Setup ----------
void setup() {
  Serial.begin(115200);

  pinMode(FLOW_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(FLOW_PIN), pulseCounter, FALLING);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  setup_wifi();
  client.setServer(mqtt_server, 1883);
}

void setup_wifi() {
  delay(10);
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

// ---------- Distance ----------
float getDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 50000);
  if (duration == 0) return -1;
  return duration * 0.0343 / 2.0;
}

// ---------- Flow ----------
float getFlowRate(unsigned long intervalMs) {
  noInterrupts();
  int count = pulseCount;
  pulseCount = 0;
  interrupts();

  float liters = count / (float)pulsesPerLiter;
  float rate = liters * (60000.0 / intervalMs);  // L/min
  return rate;
}

// ---------- Loop ----------
void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  unsigned long now = millis();
  if (now - lastSend > 5000) {
    lastSend = now;

    float dist = getDistance();
    float flow = getFlowRate(5000);

    String payload = "{\"distance_cm\":";
    payload += dist;
    payload += ",\"flow_lpm\":";
    payload += flow;
    payload += "}";

    Serial.println(payload);
    client.publish("water/telemetry", payload.c_str());
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP8266Node")) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      delay(5000);
    }
  }
}
