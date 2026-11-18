// Nodo de seguridad residencial · ESP32 DevKit V1
//
// Sensores: PIR (D27), MC-38 (D26), ADXL335 (D34/D35/D32)
// Relé:     CH1 cerradura (D25), CH2 sirena (D33)
//
// Latencia: el PIR y la puerta se revisan en cada vuelta del loop y cualquier
// cambio se publica al instante; el acelerómetro se muestrea a 200 Hz y el
// golpe se detecta en la placa. Además se envía una "foto" cada 250 ms.
//
// Lógica de alarma (informe §5.5): desarmado → saliendo (30 s) → armado →
// sospecha (primer evento) → alarma (2 de 3 sensores distintos en 10 s).

#include <WiFi.h>
#include <PubSubClient.h>
#include <time.h>
#include <sys/time.h>

// ---------- Red ----------
#include "secrets.h"   // WIFI_SSID y WIFI_PASS: copiar secrets.example.h como secrets.h
const char* MQTT_HOST = "broker.hivemq.com";
const uint16_t MQTT_PORT = 1883;

const char* T_SENSORES = "iot/seguridad/sensores";  // foto rápida para el tablero
const char* T_EVENTO   = "casa/nodo1/evento";
const char* T_CMD      = "casa/nodo1/cmd";
const char* T_LWT      = "casa/nodo1/lwt";

// ---------- Pines ----------
const uint8_t PIN_PIR = 27;
const uint8_t PIN_PUERTA = 26;
const uint8_t PIN_X = 34, PIN_Y = 35, PIN_Z = 32;
const uint8_t PIN_RELE_CERRADURA = 25;   // CH1
const uint8_t PIN_RELE_SIRENA = 33;      // CH2
const bool RELE_ACTIVO_EN_BAJO = true;   // módulo típico: IN en LOW = relé encendido

// ---------- Parámetros ----------
const uint32_t PIR_CALENTAMIENTO_MS = 60000;
const uint32_t PUERTA_REBOTE_MS = 30;
const uint32_t PERIODO_ADC_US = 5000;    // 200 Hz
const float    ALFA = 0.25f;             // filtro de cada eje
const float    ETA = 40;                 // umbral de vibración (cuentas del ADC)
const uint8_t  NV = 3;                   // muestras seguidas sobre el umbral
const uint32_t VIB_FIN_MS = 300;         // tiempo sin vibración para cerrar el evento
const uint32_t VENTANA_W_MS = 10000;     // regla 2 de 3
const uint32_t SALIDA_MS = 30000;        // retardo de salida al armar
const uint32_t SIRENA_MAX_MS = 60000;    // la sirena se apaga sola
const uint32_t SIRENA_PRUEBA_MS = 500;   // prueba manual: pitido corto de 0.5 s
const uint32_t FOTO_MS = 250;            // envío periódico (4 por segundo)
const uint32_t FOTO_MIN_MS = 40;         // separación mínima entre envíos

enum Estado { DESARMADO, SALIENDO, ARMADO, SOSPECHA, ALARMA };
const char* NOMBRE_ESTADO[] = { "desarmado", "saliendo", "armado", "sospecha", "alarma" };

WiFiClient net;
PubSubClient mqtt(net);

Estado estado = DESARMADO;
uint32_t tEstado = 0;

// sensores
int pir = 0, puerta = 0, puertaCruda = 0;
uint32_t tPuertaCruda = 0;
int ax = 0, ay = 0, az = 0;
float fx = 0, fy = 0, fz = 0;            // ejes filtrados
float bx = 0, by = 0, bz = 0;            // posición de reposo
uint16_t muestrasBase = 0;
float sumX = 0, sumY = 0, sumZ = 0;
float dMax = 0;                          // mayor desviación desde el último envío
uint8_t sobreUmbral = 0;
bool vib = false;
uint32_t tUltimaVib = 0;
uint32_t tMuestra = 0;

// alarma
uint32_t tP = 0, tR = 0, tV = 0;         // último evento de cada canal (0 = ninguno)
bool sirena = false, cerradura = false, sirenaManual = false, cerraduraManual = false;
uint32_t tSirena = 0, tSirenaManual = 0;

// envío
bool cambio = true;
uint32_t tFoto = 0, tWifi = 0, tMqtt = 0;

void rele(uint8_t pin, bool on) {
  digitalWrite(pin, (on != RELE_ACTIVO_EN_BAJO) ? HIGH : LOW);
}

void aplicarActuadores() {
  rele(PIN_RELE_SIRENA, sirena || sirenaManual);
  rele(PIN_RELE_CERRADURA, cerradura || cerraduraManual);
}

uint64_t epochMs() {
  struct timeval tv;
  gettimeofday(&tv, nullptr);
  if (tv.tv_sec < 1700000000) return 0;  // todavía sin hora de NTP
  return (uint64_t)tv.tv_sec * 1000ULL + tv.tv_usec / 1000;
}

bool pirCalentando() { return millis() < PIR_CALENTAMIENTO_MS; }

void publicarEvento(const char* canal, const char* detalle) {
  char m[200];
  snprintf(m, sizeof(m), "{\"nodo\":\"nodo1\",\"t\":%llu,\"canal\":\"%s\",\"detalle\":\"%s\",\"estado\":\"%s\"}",
           epochMs(), canal, detalle, NOMBRE_ESTADO[estado]);
  Serial.printf("[EVENTO] %s\n", m);
  if (mqtt.connected()) mqtt.publish(T_EVENTO, m);
}

void cambiarEstado(Estado e) {
  if (e == estado) return;
  estado = e;
  tEstado = millis();
  cambio = true;
  publicarEvento("sistema", NOMBRE_ESTADO[e]);
}

uint8_t canalesEnVentana(uint32_t ahora) {
  uint8_t n = 0;
  if (tP && ahora - tP <= VENTANA_W_MS) n++;
  if (tR && ahora - tR <= VENTANA_W_MS) n++;
  if (tV && ahora - tV <= VENTANA_W_MS) n++;
  return n;
}

// Evento de un sensor: lo registra y avanza la máquina de estados
void eventoSensor(char canal, const char* nombre, const char* detalle) {
  uint32_t ahora = millis();
  cambio = true;
  publicarEvento(nombre, detalle);
  if (estado != ARMADO && estado != SOSPECHA) return;

  if (canal == 'P') tP = ahora;
  if (canal == 'R') tR = ahora;
  if (canal == 'V') tV = ahora;

  if (estado == ARMADO) {
    cambiarEstado(SOSPECHA);
    if (canal == 'V') { cerradura = true; aplicarActuadores(); }   // bloqueo preventivo
  }
  if (estado == SOSPECHA && canalesEnVentana(ahora) >= 2) {
    sirena = true;
    cerradura = true;
    tSirena = ahora;
    aplicarActuadores();
    cambiarEstado(ALARMA);
  }
}

void leerSensoresDigitales() {
  uint32_t ahora = millis();

  int p = digitalRead(PIN_PIR);
  if (p != pir) {
    pir = p;
    cambio = true;
    if (p && !pirCalentando()) eventoSensor('P', "pir", "movimiento");
  }

  int r = digitalRead(PIN_PUERTA);       // INPUT_PULLUP: 1 = abierta
  if (r != puertaCruda) { puertaCruda = r; tPuertaCruda = ahora; }
  if (puertaCruda != puerta && ahora - tPuertaCruda >= PUERTA_REBOTE_MS) {
    puerta = puertaCruda;
    eventoSensor('R', "puerta", puerta ? "abierta" : "cerrada");
  }
}

void muestrearAcelerometro() {
  uint32_t ahoraUs = micros();
  if (ahoraUs - tMuestra < PERIODO_ADC_US) return;
  tMuestra = (ahoraUs - tMuestra > 10 * PERIODO_ADC_US) ? ahoraUs : tMuestra + PERIODO_ADC_US;

  int rx = analogRead(PIN_X), ry = analogRead(PIN_Y), rz = analogRead(PIN_Z);

  // filtro pasa bajos (constante ≈ 17 ms): quita el ruido del ADC sin perder los golpes
  if (muestrasBase == 0) { fx = rx; fy = ry; fz = rz; }
  fx += ALFA * (rx - fx); fy += ALFA * (ry - fy); fz += ALFA * (rz - fz);
  ax = (int)fx; ay = (int)fy; az = (int)fz;

  if (muestrasBase < 200) {               // primer segundo: promedio de reposo
    sumX += fx; sumY += fy; sumZ += fz;
    if (++muestrasBase == 200) { bx = sumX / 200; by = sumY / 200; bz = sumZ / 200; }
    return;
  }

  float d = sqrtf((fx - bx) * (fx - bx) + (fy - by) * (fy - by) + (fz - bz) * (fz - bz));
  if (d > dMax) dMax = d;

  uint32_t ahora = millis();
  if (d > ETA) {
    tUltimaVib = ahora;
    if (sobreUmbral < 255) sobreUmbral++;
    if (sobreUmbral >= NV && !vib) {
      vib = true;
      eventoSensor('V', "vibracion", "golpe");
    }
  } else {
    sobreUmbral = 0;
    // el reposo sigue lentamente al sensor (por si queda inclinado)
    bx += 0.002f * (fx - bx); by += 0.002f * (fy - by); bz += 0.002f * (fz - bz);
  }
  if (vib && ahora - tUltimaVib > VIB_FIN_MS) { vib = false; cambio = true; }
}

void actualizarEstado() {
  uint32_t ahora = millis();
  if (estado == SALIENDO && ahora - tEstado >= SALIDA_MS) {
    tP = tR = tV = 0;
    cambiarEstado(ARMADO);
  }
  if (estado == SOSPECHA && canalesEnVentana(ahora) == 0) {
    cerradura = false;
    aplicarActuadores();
    cambiarEstado(ARMADO);
  }
  if (sirena && ahora - tSirena >= SIRENA_MAX_MS) {
    sirena = false;
    aplicarActuadores();
    cambio = true;
    publicarEvento("sirena", "tiempo maximo");
  }
  if (sirenaManual && ahora - tSirenaManual >= SIRENA_PRUEBA_MS) {
    sirenaManual = false;
    aplicarActuadores();
    cambio = true;
    publicarEvento("sirena", "fin de prueba");
  }
}

void enviarFoto() {
  uint32_t ahora = millis();
  if (!mqtt.connected()) return;
  if (ahora - tFoto < FOTO_MIN_MS) return;
  if (!cambio && ahora - tFoto < FOTO_MS) return;
  tFoto = ahora;
  cambio = false;

  int32_t salida = (estado == SALIENDO) ? (int32_t)((SALIDA_MS - (ahora - tEstado) + 999) / 1000) : 0;
  char m[320];
  snprintf(m, sizeof(m),
           "{\"t\":%llu,\"estado\":\"%s\",\"pir\":%d,\"puerta_abierta\":%d,\"x\":%d,\"y\":%d,\"z\":%d,"
           "\"vib\":%d,\"d\":%d,\"sirena\":%d,\"cerradura\":%d,\"pir_calibrando\":%s,\"salida_s\":%ld,\"rssi\":%d}",
           epochMs(), NOMBRE_ESTADO[estado], pir, puerta, ax, ay, az, vib ? 1 : 0, (int)dMax,
           (sirena || sirenaManual) ? 1 : 0, (cerradura || cerraduraManual) ? 1 : 0,
           pirCalentando() ? "true" : "false", (long)salida, WiFi.RSSI());
  dMax = 0;
  mqtt.publish(T_SENSORES, m);
}

void onCmd(char* topic, byte* payload, unsigned int len) {
  String c;
  for (unsigned int i = 0; i < len; i++) c += (char)payload[i];
  c.trim();
  Serial.printf("[CMD] %s\n", c.c_str());

  if (c == "armar") {
    if (estado == DESARMADO) { tP = tR = tV = 0; cambiarEstado(SALIENDO); }
  } else if (c == "desarmar") {
    sirena = cerradura = sirenaManual = cerraduraManual = false;
    tP = tR = tV = 0;
    cambiarEstado(DESARMADO);
  } else if (c == "silenciar") {
    sirena = sirenaManual = false;
  } else if (c == "sirena_on") {
    sirenaManual = true;
    tSirenaManual = millis();
  } else if (c == "sirena_off") {
    sirenaManual = false;
    sirena = false;
  } else if (c == "cerradura_on") {
    cerraduraManual = true;
  } else if (c == "cerradura_off") {
    cerraduraManual = false;
    if (estado != ALARMA && estado != SOSPECHA) cerradura = false;
  } else {
    publicarEvento("cmd", "desconocido");
    return;
  }
  aplicarActuadores();
  cambio = true;
  char ack[96];
  snprintf(ack, sizeof(ack), "{\"nodo\":\"nodo1\",\"ack\":\"%s\",\"estado\":\"%s\"}", c.c_str(), NOMBRE_ESTADO[estado]);
  mqtt.publish(T_EVENTO, ack);
}

void mantenerConexion() {
  uint32_t ahora = millis();
  if (WiFi.status() != WL_CONNECTED) {
    if (ahora - tWifi > 10000) { tWifi = ahora; Serial.println("[WiFi] reintentando..."); WiFi.reconnect(); }
    return;
  }
  if (mqtt.connected()) return;
  if (tMqtt && ahora - tMqtt < 5000) return;
  tMqtt = ahora;
  String id = "utec-nodo1-" + String((uint32_t)ESP.getEfuseMac(), HEX);
  Serial.print("[MQTT] conectando... ");
  if (mqtt.connect(id.c_str(), T_LWT, 1, true, "offline")) {
    Serial.println("OK");
    mqtt.publish(T_LWT, "online", true);
    mqtt.subscribe(T_CMD, 1);
    cambio = true;
  } else {
    Serial.printf("falló (%d)\n", mqtt.state());
  }
}

void setup() {
  // relés apagados antes de configurar los pines como salida (sin pulsos al arrancar)
  rele(PIN_RELE_SIRENA, false);
  rele(PIN_RELE_CERRADURA, false);
  pinMode(PIN_RELE_SIRENA, OUTPUT);
  pinMode(PIN_RELE_CERRADURA, OUTPUT);

  Serial.begin(115200);
  delay(200);
  Serial.println("\n=== Nodo de seguridad · nodo1 ===");

  pinMode(PIN_PIR, INPUT);
  pinMode(PIN_PUERTA, INPUT_PULLUP);
  pir = digitalRead(PIN_PIR);
  puerta = puertaCruda = digitalRead(PIN_PUERTA);

  analogReadResolution(12);
  analogSetPinAttenuation(PIN_X, ADC_11db);
  analogSetPinAttenuation(PIN_Y, ADC_11db);
  analogSetPinAttenuation(PIN_Z, ADC_11db);

  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  configTime(-5 * 3600, 0, "pool.ntp.org", "time.google.com");   // hora de Lima, para medir latencia

  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onCmd);
  mqtt.setBufferSize(512);
  tMuestra = micros();
}

void loop() {
  mantenerConexion();
  if (mqtt.connected()) mqtt.loop();

  leerSensoresDigitales();
  muestrearAcelerometro();
  actualizarEstado();
  enviarFoto();
}
