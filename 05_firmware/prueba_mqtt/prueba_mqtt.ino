// Prueba de conexión ESP32 -> Wi-Fi -> broker MQTT
// Proyecto IoT: Sistema de seguridad residencial (nodo1)
//
// Abre el Monitor Serie a 115200 baudios: ahí se ve cada paso.

#include <WiFi.h>
#include <PubSubClient.h>

// ---------- Configuración ----------
#include "secrets.h"   // WIFI_SSID y WIFI_PASS: copiar secrets.example.h como secrets.h
const char* BROKER    = "broker.hivemq.com"; // o la IP de la laptop con Mosquitto
const int   PUERTO    = 1883;
const char* NODO      = "nodo1";
// -----------------------------------

const char* T_EVENTO = "casa/nodo1/evento";
const char* T_ESTADO = "casa/nodo1/estado";
const char* T_CMD    = "casa/nodo1/cmd";
const char* T_LWT    = "casa/nodo1/lwt";

WiFiClient net;
PubSubClient mqtt(net);

void onCmd(char* topic, byte* payload, unsigned int len) {
  String cmd;
  for (unsigned int i = 0; i < len; i++) cmd += (char)payload[i];
  Serial.printf("[CMD] %s -> %s\n", topic, cmd.c_str());
  String ack = "{\"nodo\":\"" + String(NODO) + "\",\"ack\":\"" + cmd + "\"}";
  mqtt.publish(T_EVENTO, ack.c_str());
}

void conectarWifi() {
  Serial.printf("[WiFi] Conectando a \"%s\"", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (millis() - t0 > 20000) {
      Serial.printf("\n[WiFi] No conecta (estado %d). Revisa nombre, clave y que la red sea de 2,4 GHz.\n",
                    WiFi.status());
      t0 = millis();
      WiFi.begin(WIFI_SSID, WIFI_PASS);
    }
  }
  Serial.printf("\n[WiFi] OK. IP: %s  RSSI: %d dBm\n",
                WiFi.localIP().toString().c_str(), WiFi.RSSI());
}

void conectarMqtt() {
  // ID único para no chocar con otros clientes en un broker público
  String id = String("utec-") + NODO + "-" + String((uint32_t)ESP.getEfuseMac(), HEX);
  while (!mqtt.connected()) {
    Serial.printf("[MQTT] Conectando a %s:%d ... ", BROKER, PUERTO);
    // Last Will: si el nodo se cae, el broker publica "offline" retenido
    if (mqtt.connect(id.c_str(), T_LWT, 1, true, "offline")) {
      Serial.println("OK");
      mqtt.publish(T_LWT, "online", true);
      mqtt.subscribe(T_CMD, 1);
      Serial.printf("[MQTT] Suscrito a %s\n", T_CMD);
    } else {
      // -2: no llega al broker (IP, puerto o red bloquea); -4: tiempo agotado
      Serial.printf("falló (código %d). Reintento en 3 s\n", mqtt.state());
      delay(3000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== Prueba MQTT nodo1 ===");
  conectarWifi();
  mqtt.setServer(BROKER, PUERTO);
  mqtt.setCallback(onCmd);
}

unsigned long ultimoLatido = 0;

void loop() {
  if (WiFi.status() != WL_CONNECTED) conectarWifi();
  if (!mqtt.connected()) conectarMqtt();
  mqtt.loop();

  if (millis() - ultimoLatido >= 5000) {   // latido cada 5 s
    ultimoLatido = millis();
    String s = "{\"nodo\":\"" + String(NODO) + "\",\"rssi\":" + String(WiFi.RSSI()) +
               ",\"uptime_s\":" + String(millis() / 1000) + "}";
    mqtt.publish(T_ESTADO, s.c_str());
    Serial.printf("[MQTT] -> %s %s\n", T_ESTADO, s.c_str());
  }
}
