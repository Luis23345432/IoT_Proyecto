#include <WiFi.h>
#include <PubSubClient.h>

// CAMBIAR ESTOS DATOS
// (original del equipo: "HONOR X8d" + Mosquitto en 10.100.241.236;
//  aquí se usa el hotspot y el broker público con los que ya se probó la conexión)
#include "secrets.h"   // WIFI_SSID y WIFI_PASS: copiar secrets.example.h como secrets.h
const char* MQTT_HOST = "broker.hivemq.com";
const uint16_t MQTT_PORT = 1883;
const char* MQTT_TOPIC = "iot/seguridad/sensores";

// Dejar vacios si Mosquitto permite acceso anonimo
const char* MQTT_USER = "";
const char* MQTT_PASS = "";

// Pines ESP32
const uint8_t PIN_PIR = 27;
const uint8_t PIN_PUERTA = 26;
const uint8_t PIN_X = 34;
const uint8_t PIN_Y = 35;
const uint8_t PIN_Z = 32;

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

unsigned long ultimoWiFi = 0;
unsigned long ultimoMQTT = 0;
unsigned long ultimaLectura = 0;

void conectarWiFiSiHaceFalta() {
  if (WiFi.status() == WL_CONNECTED) return;
  if (millis() - ultimoWiFi < 10000UL) return;

  ultimoWiFi = millis();
  Serial.println("WiFi desconectado: reintentando...");
  WiFi.reconnect();
}

void conectarMQTTSiHaceFalta() {
  if (WiFi.status() != WL_CONNECTED || mqtt.connected()) return;
  if (ultimoMQTT != 0 && millis() - ultimoMQTT < 5000UL) return;

  ultimoMQTT = millis();

  String clienteID = "esp32-sensores-" +
                      String((uint32_t)ESP.getEfuseMac(), HEX);

  Serial.print("Conectando a Mosquitto...");

  bool ok = false;

  if (strlen(MQTT_USER) > 0) {
    ok = mqtt.connect(clienteID.c_str(), MQTT_USER, MQTT_PASS);
  } else {
    ok = mqtt.connect(clienteID.c_str());
  }

  if (ok) {
    Serial.println(" conectado!");
  } else {
    Serial.print(" error, estado MQTT = ");
    Serial.println(mqtt.state());
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n=== PRUEBA SENSORES ESP32 ===");

  pinMode(PIN_PIR, INPUT);
  pinMode(PIN_PUERTA, INPUT_PULLUP);

  analogReadResolution(12);
  analogSetPinAttenuation(PIN_X, ADC_11db);
  analogSetPinAttenuation(PIN_Y, ADC_11db);
  analogSetPinAttenuation(PIN_Z, ADC_11db);

  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setBufferSize(512);

  Serial.println("Esperar 60 segundos para el PIR.");
}

void loop() {
  conectarWiFiSiHaceFalta();
  conectarMQTTSiHaceFalta();

  if (mqtt.connected()) mqtt.loop();

  if (millis() - ultimaLectura >= 1000UL) {
    ultimaLectura = millis();

    int pir = digitalRead(PIN_PIR);
    int puertaAbierta = digitalRead(PIN_PUERTA);

    int x = analogRead(PIN_X);
    int y = analogRead(PIN_Y);
    int z = analogRead(PIN_Z);

    bool pirCalibrando = millis() < 60000UL;

    char mensaje[220];

    snprintf(
      mensaje, sizeof(mensaje),
      "{\"pir\":%d,\"puerta_abierta\":%d,"
      "\"x\":%d,\"y\":%d,\"z\":%d,"
      "\"pir_calibrando\":%s}",
      pir, puertaAbierta, x, y, z,
      pirCalibrando ? "true" : "false"
    );

    Serial.print("WiFi: ");
    if (WiFi.status() == WL_CONNECTED) {
      Serial.print(WiFi.localIP());
    } else {
      Serial.print("SIN CONEXION");
    }

    Serial.print(" | MQTT: ");
    Serial.print(mqtt.connected() ? "conectado" : "desconectado");

    Serial.print(" | Lectura: ");
    Serial.println(mensaje);

    if (mqtt.connected()) {
      if (!mqtt.publish(MQTT_TOPIC, mensaje)) {
        Serial.println("Error publicando MQTT");
      }
    }
  }
}
