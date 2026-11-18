"""Graba una sesión del nodo para la sección de resultados del informe.
Espera a que el nodo publique, graba DURACION s de todos los topics con la hora
de llegada, y mide el tiempo de ida y vuelta de comandos con un comando
inocuo ('ping': el nodo responde 'desconocido' sin tocar actuadores)."""
import json, subprocess, sys, threading, time
BROKER = "broker.hivemq.com"
DURACION = int(sys.argv[1]) if len(sys.argv) > 1 else 300
OUT = sys.argv[2] if len(sys.argv) > 2 else "sesion.jsonl"
N_PING = 30

def espera_nodo(max_s=3600):
    t0 = time.time()
    while time.time() - t0 < max_s:
        r = subprocess.run(["mosquitto_sub", "-h", BROKER, "-t", "iot/seguridad/sensores", "-C", "1", "-W", "10"],
                           capture_output=True, text=True)
        if r.stdout.strip():
            return True
    return False

if not espera_nodo():
    print("el nodo no se conectó"); sys.exit(1)
print("nodo en línea, grabando", DURACION, "s", flush=True)
p = subprocess.Popen(["mosquitto_sub", "-h", BROKER, "-v", "-t", "iot/seguridad/sensores",
                      "-t", "casa/nodo1/evento", "-t", "casa/nodo1/lwt", "-t", "casa/nodo1/cmd"],
                     stdout=subprocess.PIPE, text=True, bufsize=1)
f = open(OUT, "w")
def lector():
    for linea in p.stdout:
        top, _, pay = linea.rstrip("\n").partition(" ")
        f.write(json.dumps({"llegada": time.time() * 1000, "topic": top, "payload": pay}) + "\n"); f.flush()
threading.Thread(target=lector, daemon=True).start()
time.sleep(5)
for i in range(N_PING):   # pings al inicio: el resto de la sesión queda para eventos reales
    f.write(json.dumps({"llegada": time.time() * 1000, "topic": "local/ping_enviado", "payload": str(i)}) + "\n"); f.flush()
    subprocess.run(["mosquitto_pub", "-h", BROKER, "-t", "casa/nodo1/cmd", "-q", "1", "-m", "ping"])
    time.sleep(1.5)
time.sleep(max(0, DURACION - 5 - N_PING * 1.5))
p.terminate(); f.close()
print("listo:", OUT)
