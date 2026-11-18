"""Diagrama de conexiones del nodo autónomo (diseño final del informe P2).

Todo se alimenta de la fuente de 12 V: el LM2596 baja a 5 V para el ESP32 (VIN),
la bobina del relé (puente JD-VCC↔VCC puesto) y el PIR. GND común.

Uso: python conexiones.py [salida.png]
"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Polygon, Arc

OUT = sys.argv[1] if len(sys.argv) > 1 else "conexiones_sistema.png"

W, H = 220, 152
fig = plt.figure(figsize=(W / 10, H / 10), dpi=150)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
fig.patch.set_facecolor("white")

C = dict(v12="#d62728", v5="#ef7d00", v33="#c9a400", gnd="#111111",
         x="#2ca02c", y="#1f77b4", z="#8c564b", mc="#17becf", pir="#e377c2",
         in1="#7b3fa0", in2="#b8860b", load="#d62728")
LW = 2.2

# ---------------------------------------------------------------- utilidades
segs = []      # (x1, y1, x2, y2, color, net, lw)
dots = []


def wire(pts, color, net, lw=LW):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        segs.append((x1, y1, x2, y2, color, net, lw))


def dot(x, y, color):
    dots.append((x, y, color))


def box(x, y, w, h, fc, ec="#333", lw=1.4, r=0.8, z=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, zorder=z))


def txt(x, y, s, size=9, **kw):
    kw.setdefault("ha", "center"); kw.setdefault("va", "center"); kw.setdefault("zorder", 6)
    ax.text(x, y, s, fontsize=size, **kw)


def pin(x, y, label, side, color="#333"):
    ax.plot([x], [y], "o", ms=4, color=color, zorder=7)
    if side == "r":
        txt(x - 1.0, y, label, 8, ha="right")
    else:
        txt(x + 1.0, y, label, 8, ha="left")


def draw_wires():
    hop = 0.9
    vert = [s for s in segs if abs(s[0] - s[2]) < 1e-6]
    for x1, y1, x2, y2, col, net, lw in segs:
        if abs(y1 - y2) < 1e-6:                     # horizontal: saltos sobre verticales
            y = y1; a, b = sorted((x1, x2))
            xs = sorted(v[0] for v in vert if v[5] != net and a + hop < v[0] < b - hop
                        and min(v[1], v[3]) + 0.05 < y < max(v[1], v[3]) - 0.05)
            cur = a
            for xc in xs:
                ax.plot([cur, xc - hop], [y, y], color=col, lw=lw, zorder=4, solid_capstyle="round")
                ax.add_patch(Arc((xc, y), 2 * hop, 2 * hop, theta1=0, theta2=180, color=col, lw=lw, zorder=4))
                cur = xc + hop
            ax.plot([cur, b], [y, y], color=col, lw=lw, zorder=4, solid_capstyle="round")
        else:
            ax.plot([x1, x2], [y1, y2], color=col, lw=lw, zorder=3, solid_capstyle="round")
    for x, y, c in dots:
        ax.plot([x], [y], "o", ms=6.5, color=c, zorder=8)


# ---------------------------------------------------------------- título
txt(4, 148.5, "Cómo va todo conectado · nodo autónomo (sin laptop)", 20, ha="left", weight="bold")
txt(4, 144.6, "Una sola fuente de 12 V alimenta todo: el LM2596 baja a 5 V para el ESP32, el relé y el PIR. "
    "GND común. El USB-C del ESP32 queda solo para programar.", 11, ha="left", color="#444")

# ---------------------------------------------------------------- zonas
ax.add_patch(Rectangle((2.5, 81), 35.5, 50, fc="#eef4ff", ec="#5b7fbf", ls="--", lw=1.2, zorder=0))
txt(4, 129, "EN LA PUERTA · cable UTP", 9, ha="left", weight="bold", color="#3b5ea8")
ax.add_patch(Rectangle((61, 66), 82, 75.5, fc="#f4f7f2", ec="#6a8f5a", ls="--", lw=1.2, zorder=0))
txt(139, 67.6, "DENTRO DE LA CARCASA 3D", 9, ha="right", weight="bold", color="#4f7341")
ax.add_patch(Rectangle((163, 88), 39, 46.5, fc="#fff3ee", ec="#c0603a", ls="--", lw=1.2, zorder=0))
txt(164.5, 90, "CARGAS 12 V", 9, ha="left", weight="bold", color="#a8502f")

# ---------------------------------------------------------------- sensores
box(8, 105, 27, 22, "#e3ecff")
txt(10, 120, "ADXL335\n(GY-61)\nvibración", 10, ha="left", weight="bold")
for lab, y in [("VCC", 123), ("X", 119), ("Y", 115), ("Z", 111), ("GND", 107)]:
    pin(35, y, lab, "r")

box(8, 97.5, 27, 6, "#e3ecff")
txt(10, 100.5, "MC-38\napertura", 9, ha="left", weight="bold")
pin(35, 102, "cable 2", "r"); pin(35, 99, "cable 1", "r")

box(8, 84, 27, 12.5, "#e3ecff")
txt(10, 90.5, "PIR\nHC-SR501\nmovimiento", 9.5, ha="left", weight="bold")
for lab, y in [("OUT", 95), ("GND", 91), ("VCC", 87)]:
    pin(35, y, lab, "r")

# ---------------------------------------------------------------- ESP32
box(75, 71, 20, 63, "#1f3b5c", ec="#0e1e30", r=1.2)
L = ["EN", "VP", "VN", "D34", "D35", "D32", "D33", "D25", "D26", "D27", "D14", "D12", "D13", "GND", "VIN"]
R = ["D23", "D22", "TX0", "RX0", "D21", "D19", "D18", "D5", "TX2", "RX2", "D4", "D2", "D15", "GND", "3V3"]
used = {"D34", "D35", "D32", "D33", "D25", "D26", "D27", "GND", "VIN", "3V3"}
P = {}
for i, (l, r) in enumerate(zip(L, R)):
    y = 131 - 4 * i
    for name, x, side in [(l, 75, "l"), (r, 95, "r")]:
        u = name in used and not (name == "GND" and side == "r")
        ax.plot([x], [y], "o", ms=4.5, color="#f5c542" if u else "#8796a8", zorder=7)
        txt(x + (1.2 if side == "l" else -1.2), y, name, 8, ha="left" if side == "l" else "right",
            color="white" if u else "#9fb0c4", weight="bold" if u else "normal")
        P[(name, side)] = (x, y)
txt(85, 103, "ESP32 DevKit V1 · 30 pines", 12, rotation=90, color="white", weight="bold")
ax.add_patch(Rectangle((82.5, 68.6), 5, 2.4, fc="#b0b0b0", ec="#555", zorder=5))
txt(85, 67.2, "USB-C: solo para programar", 7.5, color="#555")

# ---------------------------------------------------------------- relé
box(115, 92, 25, 34, "#e9f3e6")
txt(127.5, 123.5, "Módulo relé 2 canales\nSRD-05VDC", 9, weight="bold")
for lab, y in [("VCC", 120), ("IN1", 116), ("IN2", 112), ("GND", 108)]:
    pin(115, y, lab, "l")
for lab, y in [("NO1", 121), ("COM1", 117), ("NC1", 113), ("NO2", 103), ("COM2", 99), ("NC2", 95)]:
    pin(140, y, lab, "r")
txt(131, 108.5, "Relé 1\ncerradura", 7.5, color="#555")
txt(131, 97.5, "Relé 2\nsirena", 7.5, color="#555")
box(116.5, 93, 12.5, 4.6, "#c9f0c4", ec="#2e7d32", lw=1.2, r=0.4, z=5)
txt(122.75, 95.3, "puente JD-VCC↔VCC\nPUESTO", 6.8, color="#1b5e20", weight="bold")
txt(143, 113, "libre", 7, ha="left", color="#999"); txt(143, 95, "libre", 7, ha="left", color="#999")

# ---------------------------------------------------------------- LM2596
box(115, 70, 20, 14, "#fff4cc")
txt(125, 77, "LM2596\n12 V → 5,0 V", 9.5, weight="bold")
pin(115, 80, "OUT+", "l"); pin(115, 73, "OUT−", "l")
pin(135, 80, "IN+", "r"); pin(135, 73, "IN−", "r")

# ---------------------------------------------------------------- fuente
box(172, 66, 26, 18, "#dfe3e8")
txt(185, 75.5, "Fuente\n12 V · 3 A", 11, weight="bold")
txt(185, 69, "enchufe 220 V", 8, color="#555")
pin(172, 80, "+V", "l"); pin(172, 72, "−V", "l")
# fusible
ax.add_patch(Rectangle((155, 78.8), 9, 2.4, fc="white", ec=C["v12"], lw=1.6, zorder=6))
txt(159.5, 83.2, "fusible 4 A", 8, color=C["v12"], weight="bold")

# ---------------------------------------------------------------- cargas
box(170, 116, 22, 10, "#f2f2f2")
txt(181, 121, "Cerradura\nLM-1805 12 V", 9, weight="bold")
pin(170, 121, "+", "l"); pin(192, 121, "−", "r")
box(170, 98, 22, 10, "#f2f2f2")
txt(181, 103, "Sirena\nGP-04 12 V", 9, weight="bold")
pin(170, 103, "+", "l"); pin(192, 103, "−", "r")


def diode(x1, x2, y, ylo):
    """1N4007 en antiparalelo: franja (cátodo) hacia el + de la carga."""
    xm = (x1 + x2) / 2
    wire([(x1, ylo), (x1, y), (xm - 2, y)], C["gnd"], f"d{y}a", 1.6)
    wire([(xm + 2, y), (x2, y), (x2, ylo)], C["gnd"], f"d{y}b", 1.6)
    ax.add_patch(Polygon([[xm + 2, y + 1.6], [xm + 2, y - 1.6], [xm - 2, y]], closed=True,
                         fc="#444", ec="#111", zorder=6))
    ax.plot([xm - 2, xm - 2], [y - 1.7, y + 1.7], color="#111", lw=3, zorder=6)
    txt(xm, y + 2.6, "1N4007 · franja hacia +", 7.5, color="#333")


# interruptor manual en NO1
ax.plot([152, 157.5], [121, 124], color=C["v12"], lw=2.2, zorder=6)
ax.plot([152], [121], "o", ms=5, mfc="white", mec=C["v12"], zorder=7)
ax.plot([158], [121], "o", ms=5, mfc="white", mec=C["v12"], zorder=7)
txt(155, 126, "interruptor 3 A\n(liberación manual)", 7.5, color=C["v12"])

# ================================================================ CABLES
# buses
wire([(42, 60), (200, 60)], C["gnd"], "gnd", 3)
wire([(46, 64), (110, 64)], C["v5"], "v5", 3)
txt(48, 61.6, "GND común", 8.5, ha="left", color=C["gnd"], weight="bold")
txt(48, 65.6, "bus 5 V", 8.5, ha="left", color=C["v5"], weight="bold")

# sensores -> ESP32
wire([(35, 119), (75, 119)], C["x"], "x"); wire([(35, 115), (75, 115)], C["y"], "y")
wire([(35, 111), (75, 111)], C["z"], "z")
wire([(35, 99), (75, 99)], C["mc"], "mc")
wire([(35, 95), (75, 95)], C["pir"], "pir")
# GND de sensores
wire([(35, 107), (42, 107), (42, 60)], C["gnd"], "gnd")
wire([(35, 102), (42, 102)], C["gnd"], "gnd"); dot(42, 102, C["gnd"])
wire([(35, 91), (42, 91)], C["gnd"], "gnd"); dot(42, 91, C["gnd"])
dot(42, 60, C["gnd"])
# PIR VCC a 5 V
wire([(35, 87), (46, 87), (46, 64)], C["v5"], "v5")
# 3V3 -> ADXL VCC
wire([(95, 75), (100, 75), (100, 142), (38, 142), (38, 123), (35, 123)], C["v33"], "v33")
txt(39.5, 140.6, "3V3 → VCC del ADXL335 (no a 5 V)", 7.5, ha="left", color="#8a7000", weight="bold")
# ESP32 VIN y GND
wire([(75, 75), (68, 75), (68, 64)], C["v5"], "v5"); dot(68, 64, C["v5"])
wire([(75, 79), (66, 79), (66, 60)], C["gnd"], "gnd"); dot(66, 60, C["gnd"])
# GPIO -> relé
wire([(75, 103), (70, 103), (70, 139), (110, 139), (110, 116), (115, 116)], C["in1"], "in1")
wire([(75, 107), (72, 107), (72, 137), (108, 137), (108, 112), (115, 112)], C["in2"], "in2")
txt(90, 140.3, "D25 → IN1 (cerradura)", 7.5, color=C["in1"], weight="bold")
txt(90, 135.6, "D33 → IN2 (sirena)", 7.5, color=C["in2"], weight="bold")
# relé VCC / GND
wire([(115, 120), (104, 120), (104, 64)], C["v5"], "v5"); dot(104, 64, C["v5"])
wire([(115, 108), (106, 108), (106, 60)], C["gnd"], "gnd"); dot(106, 60, C["gnd"])
# LM2596 salida
wire([(115, 80), (110, 80), (110, 64)], C["v5"], "v5")
wire([(115, 73), (113, 73), (113, 60)], C["gnd"], "gnd"); dot(113, 60, C["gnd"])
# 12 V: fuente -> fusible -> nodo 146
wire([(172, 80), (164, 80)], C["v12"], "v12"); wire([(155, 80), (146, 80)], C["v12"], "v12")
wire([(146, 80), (135, 80)], C["v12"], "v12")
wire([(146, 80), (146, 117), (140, 117)], C["v12"], "v12")
wire([(146, 99), (140, 99)], C["v12"], "v12")
dot(146, 80, C["v12"]); dot(146, 99, C["v12"])
txt(147, 89, "+12 V\n(tras el fusible)", 7.5, ha="left", color=C["v12"], weight="bold")
# GND de fuente y LM2596 IN−
wire([(172, 72), (166, 72), (166, 60)], C["gnd"], "gnd"); dot(166, 60, C["gnd"])
wire([(135, 73), (140, 73), (140, 60)], C["gnd"], "gnd"); dot(140, 60, C["gnd"])
# salidas del relé a las cargas
wire([(140, 121), (152, 121)], C["load"], "no1"); wire([(158, 121), (170, 121)], C["load"], "no1")
wire([(140, 103), (170, 103)], C["load"], "no2")
dot(165, 121, C["load"]); dot(165, 103, C["load"])
# negativos de las cargas
wire([(192, 121), (200, 121), (200, 60)], C["gnd"], "gnd")
wire([(192, 103), (200, 103)], C["gnd"], "gnd"); dot(200, 103, C["gnd"])
dot(197, 121, C["gnd"]); dot(197, 103, C["gnd"])
diode(165, 197, 129.5, 121)
diode(165, 197, 111.5, 103)

draw_wires()

# leyenda de colores
lx, ly = 4, 76
txt(lx, ly, "Colores", 9, ha="left", weight="bold")
for i, (c, s) in enumerate([(C["v12"], "+12 V"), (C["v5"], "5 V"), (C["v33"], "3,3 V"), (C["gnd"], "GND"),
                             ("#888", "señales")]):
    yy = ly - 2.6 * (i + 1)
    ax.plot([lx, lx + 4], [yy, yy], color=c, lw=3)
    txt(lx + 5, yy, s, 8.5, ha="left")
txt(lx, ly - 17.5, "Cruce con salto = no se tocan.\nPunto = unión.", 8, ha="left", color="#444")

# ================================================================ TABLAS
def table(x0, y0, title, rows, widths, head, hc):
    txt(x0, y0, title, 11, ha="left", weight="bold")
    y = y0 - 3
    rh = 2.45
    xs = [x0]
    for w in widths:
        xs.append(xs[-1] + w)
    ax.add_patch(Rectangle((x0, y - rh / 2), sum(widths), rh, fc=hc, ec="#bbb", lw=0.6))
    for i, h in enumerate(head):
        txt(xs[i] + 1, y, h, 8.5, ha="left", weight="bold")
    for r_i, row in enumerate(rows):
        y -= rh
        ax.add_patch(Rectangle((x0, y - rh / 2), sum(widths), rh,
                               fc="white" if r_i % 2 == 0 else "#f6f7f9", ec="#ddd", lw=0.5))
        for i, cell in enumerate(row):
            bold = cell.startswith("!")
            txt(xs[i] + 1, y, cell.lstrip("!"), 8, ha="left",
                color="#b00020" if bold else "#222", weight="bold" if bold else "normal")


logico = [
    ("PIR VCC", "bus 5 V", "UTP · el PIR pide 4,5–20 V"),
    ("PIR OUT", "D27 (GPIO27)", "UTP"),
    ("PIR GND", "GND común", "UTP"),
    ("MC-38 cable 1", "D26 (GPIO26)", "pull-up interno"),
    ("MC-38 cable 2", "GND común", "UTP"),
    ("ADXL335 VCC", "!3V3 del ESP32", "!nunca a 5 V"),
    ("ADXL335 X / Y / Z", "D34 / D35 / D32", "ADC1 (funciona con Wi-Fi)"),
    ("ADXL335 GND", "GND común", "UTP"),
    ("Relé IN1", "D25 (GPIO25)", "cerradura · activo en bajo"),
    ("Relé IN2", "D33 (GPIO33)", "sirena · activo en bajo"),
    ("Relé VCC", "bus 5 V", "jumper H-H"),
    ("Relé GND", "GND común", "jumper H-H"),
    ("ESP32 VIN", "bus 5 V", "ya no por USB"),
    ("ESP32 GND", "GND común", ""),
]
potencia = [
    ("Fuente +V", "fusible 4 A → +12 V", "cable rojo grueso"),
    ("Fuente −V", "GND común", "cable negro grueso"),
    ("LM2596 IN+ / IN−", "+12 V / GND", ""),
    ("LM2596 OUT+", "bus 5 V", "!ajustar a 5,0 V antes"),
    ("LM2596 OUT−", "GND común", ""),
    ("Puente JD-VCC↔VCC", "!PUESTO", "sin él el relé no conmuta"),
    ("Relé COM1 y COM2", "+12 V", ""),
    ("Relé NO1", "interruptor → cerradura +", ""),
    ("Cerradura −", "GND común", ""),
    ("Relé NO2", "sirena +", ""),
    ("Sirena −", "GND común", ""),
    ("1N4007 ×2", "en paralelo a cada carga", "franja hacia el +"),
    ("Relé NC1 / NC2", "no se usan", ""),
]
table(4, 53, "Lado lógico (sensores, ESP32, entradas del relé)", logico, [24, 22, 33],
      ["Desde", "Hacia", "Nota"], "#d6e4f5")
table(87, 53, "Lado de potencia (12 V)", potencia, [26, 30, 26], ["Desde", "Hacia", "Nota"], "#f7dcc8")

# checklist
cx = 173
txt(cx, 53, "Antes de enchufar", 11, ha="left", weight="bold")
pasos = [
    "1. Con el multímetro, ajusta la\n    salida del LM2596 a 5,0 V\n    SIN nada conectado.",
    "2. Revisa que todas las GND\n    estén unidas (continuidad).",
    "3. No conectes el USB y el VIN\n    a la vez; para ver el serial,\n    desconecta antes el VIN.",
    "4. Si el ESP32 se reinicia al\n    sonar la sirena: condensador\n    de 470–1000 µF en la salida\n    del LM2596.",
    "5. Interruptor abierto = la\n    cerradura queda liberada.",
]
yy = 49
for p_ in pasos:
    n = p_.count("\n") + 1
    txt(cx, yy, p_, 8.3, ha="left", va="top", linespacing=1.25)
    yy -= 2.0 * n + 1.6

txt(cx, 6.5, "Cambia respecto a la versión anterior:\nsin cargador USB, puente puesto,\n"
    "GND común, relé y PIR a 5 V del LM2596.", 7.8, ha="left", va="center", color="#8a2b00", style="italic")

fig.savefig(OUT, dpi=150, facecolor="white")
print("ok", OUT)
