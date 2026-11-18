"""Análisis de las mediciones del nodo para la sección de resultados.

Entradas (en esta carpeta):
  reposo.jsonl  instantáneas del nodo con la puerta en reposo (firmware final)
  sesion.jsonl  sesión grabada con captura.py (opcional)
Salidas (en la carpeta de figuras del informe):
  resultados.tex             macros con las cifras que cita el texto
  resultados-vibracion.png   ruido del acelerómetro en reposo frente al umbral
  resultados-latencia.png    latencia de extremo a extremo y de comandos
  resultados-sesion.png      línea de tiempo de una sesión con eventos
"""
import json, sys, statistics as st
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AQUI = Path(__file__).parent
FIG = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI
ETA = 40
AZUL, NARANJA, AQUA, AMARILLO = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
TINTA, TINTA2, GRILLA = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": TINTA2,
                     "axes.labelcolor": TINTA, "xtick.color": TINTA2, "ytick.color": TINTA2,
                     "axes.spines.top": False, "axes.spines.right": False})

def pct(v, p):
    v = sorted(v); k = (len(v) - 1) * p / 100; i = int(k)
    return v[i] if i + 1 >= len(v) else v[i] + (v[i + 1] - v[i]) * (k - i)

def num(x, dec=0):
    return f"{x:.{dec}f}".replace(".", "{,}")

macros = {}

# ---------- 1. Ruido del acelerómetro en reposo ----------
reposo = [json.loads(l) for l in open(AQUI / "reposo.jsonl") if l.strip().startswith("{")]
d_rep = [r["d"] for r in reposo]
macros.update(RdN=str(len(d_rep)), RdMax=str(max(d_rep)), RdMed=num(st.mean(d_rep), 1),
              RdPnn=num(pct(d_rep, 95), 0), RdMargen=num(ETA / max(d_rep), 1))
fig, ax = plt.subplots(figsize=(6.4, 2.6), dpi=200)
t0 = reposo[0]["t"]
ts = [(r["t"] - t0) / 1000 for r in reposo]
ax.plot(ts, d_rep, color=AZUL, lw=1.6, label="d máx. por ventana de 250 ms (con filtro)")
ax.axhline(ETA, color=NARANJA, lw=1.6, ls=(0, (5, 3)), label=f"umbral η = {ETA}")
ax.axhline(45, color=TINTA2, lw=1, ls=(0, (1, 2)), label="máx. sin filtro (45)")
ax.set_xlabel("tiempo (s)"); ax.set_ylabel("d (cuentas del ADC)")
ax.set_ylim(0, 60); ax.grid(axis="y", color=GRILLA, lw=0.6); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=7.5, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, handlelength=2.2)
fig.tight_layout(); fig.savefig(FIG / "resultados-vibracion.png", facecolor="white"); fig.savefig(FIG / "resultados-vibracion.pdf", facecolor="white"); plt.close(fig)

# ---------- 2. Sesión: latencias, comandos y línea de tiempo ----------
sesion_f = AQUI / "sesion.jsonl"
hay_sesion = sesion_f.exists() and sesion_f.stat().st_size > 0
macros["RhaySesion"] = "1" if hay_sesion else "0"
if hay_sesion:
    filas = [json.loads(l) for l in open(sesion_f) if l.strip()]
    fotos, eventos, pings = [], [], []
    for f in filas:
        if f["topic"] == "local/ping_enviado":
            pings.append(f["llegada"]); continue
        try: p = json.loads(f["payload"])
        except Exception: continue
        if f["topic"] == "iot/seguridad/sensores": fotos.append((f["llegada"], p))
        elif f["topic"] == "casa/nodo1/evento": eventos.append((f["llegada"], p))
    lat = [ll - p["t"] for ll, p in fotos if p.get("t", 0) > 1.7e12]
    # ida y vuelta de comandos: cada ping contra la primera respuesta "desconocido" posterior
    resp = [ll for ll, p in eventos if p.get("detalle") == "desconocido"]
    rtt = []
    for i, tp in enumerate(pings):
        lim = pings[i + 1] if i + 1 < len(pings) else tp + 5000
        r = [x for x in resp if tp <= x < lim]
        if r: rtt.append(r[0] - tp)
    dur = (fotos[-1][0] - fotos[0][0]) / 1000
    seg = {int((ll - fotos[0][0]) // 1000) for ll, _ in fotos}
    cuenta = {c: sum(1 for _, p in eventos if p.get("canal") == c) for c in ("pir", "puerta", "vibracion")}
    macros.update(RlatN=str(len(lat)), RlatMed=num(st.median(lat)), RlatPnn=num(pct(lat, 95)),
                  RlatMin=num(min(lat)), RlatMax=num(max(lat)),
                  RrttN=str(len(rtt)), RrttEnv=str(len(pings)),
                  RrttMed=num(st.median(rtt)) if rtt else "--", RrttPnn=num(pct(rtt, 95)) if rtt else "--",
                  Rdur=num(dur), RfotosN=str(len(fotos)), RtasaFotos=num(len(fotos) / dur, 1),
                  RdispPct=num(100 * len(seg) / (int(dur) + 1), 1),
                  RnP=str(cuenta["pir"]), RnR=str(cuenta["puerta"]), RnV=str(cuenta["vibracion"]),
                  RnEstados=str(sum(1 for _, p in eventos if p.get("canal") == "sistema")))

    fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.5), dpi=200, gridspec_kw={"width_ratios": [1.5, 1]})
    ax = axs[0]
    ax.hist(lat, bins=30, color=AZUL, edgecolor="white", linewidth=0.6)
    ax.axvline(st.median(lat), color=TINTA, lw=1.2)
    ax.text(st.median(lat), ax.get_ylim()[1] * 0.95, f" mediana {st.median(lat):.0f} ms", va="top", fontsize=8, color=TINTA)
    ax.axvline(pct(lat, 95), color=TINTA2, lw=1, ls=(0, (3, 2)))
    ax.text(pct(lat, 95), ax.get_ylim()[1] * 0.78, f" p95 {pct(lat, 95):.0f} ms", va="top", fontsize=8, color=TINTA2)
    ax.set_xlabel("latencia nodo → tablero (ms)"); ax.set_ylabel("instantáneas")
    ax.set_title(f"a) Instantáneas (n = {len(lat)})", fontsize=9, loc="left", color=TINTA)
    ax.grid(axis="y", color=GRILLA, lw=0.6); ax.set_axisbelow(True)
    ax = axs[1]
    if rtt:
        ax.hist(rtt, bins=12, color=AQUA, edgecolor="white", linewidth=0.6)
        ax.axvline(st.median(rtt), color=TINTA, lw=1.2)
        ax.text(st.median(rtt), ax.get_ylim()[1] * 0.95, f" mediana\n {st.median(rtt):.0f} ms", va="top", fontsize=8, color=TINTA)
    ax.set_xlabel("ida y vuelta de un comando (ms)"); ax.set_ylabel("comandos")
    ax.set_title(f"b) Comandos (n = {len(rtt)})", fontsize=9, loc="left", color=TINTA)
    ax.grid(axis="y", color=GRILLA, lw=0.6); ax.set_axisbelow(True)
    fig.tight_layout(); fig.savefig(FIG / "resultados-latencia.png", facecolor="white"); plt.close(fig)

    # línea de tiempo
    t0 = fotos[0][0]
    T = [(ll - t0) / 1000 for ll, _ in fotos]
    fig, axs = plt.subplots(2, 1, figsize=(6.6, 3.4), dpi=200, sharex=True, gridspec_kw={"height_ratios": [1.6, 1]})
    ax = axs[0]
    ax.plot(T, [p["d"] for _, p in fotos], color=AZUL, lw=1.2, label="desviación d")
    ax.axhline(ETA, color=NARANJA, lw=1.4, ls=(0, (5, 3)), label=f"umbral η = {ETA}")
    ax.set_ylabel("d (cuentas)"); ax.grid(axis="y", color=GRILLA, lw=0.6); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, loc="upper right", ncol=2)
    ax = axs[1]
    filas_d = [("PIR", "pir", AMARILLO), ("Puerta abierta", "puerta_abierta", NARANJA),
               ("Vibración", "vib", AZUL), ("Sirena", "sirena", "#e34948")]
    for k, (nombre, campo, col) in enumerate(filas_d):
        y0 = len(filas_d) - 1 - k
        on = None
        for (ll, p), t in zip(fotos, T):
            v = bool(p.get(campo))
            if v and on is None: on = t
            if not v and on is not None:
                ax.broken_barh([(on, max(t - on, 0.15))], (y0 + 0.15, 0.7), color=col); on = None
        if on is not None: ax.broken_barh([(on, T[-1] - on)], (y0 + 0.15, 0.7), color=col)
    ax.set_yticks([len(filas_d) - 1 - k + 0.5 for k in range(len(filas_d))])
    ax.set_yticklabels([f[0] for f in filas_d], fontsize=8)
    ax.set_ylim(0, len(filas_d)); ax.set_xlabel("tiempo (s)")
    ax.grid(axis="x", color=GRILLA, lw=0.6); ax.set_axisbelow(True)
    fig.tight_layout(); fig.savefig(FIG / "resultados-sesion.png", facecolor="white"); plt.close(fig)

if not hay_sesion:
    # sin sesión grabada: mediana que mostraba el tablero (últimas 40 instantáneas, 11-nov-2026)
    macros["RlatMed"] = "357"

with open(FIG / "resultados.tex", "w") as f:
    f.write("% Generado por datos/analisis.py; no editar a mano.\n")
    for k, v in macros.items():
        f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(json.dumps(macros, ensure_ascii=False, indent=1))
