"""Maqueta de puerta (triplay 18 mm) con todos los componentes en su lugar final.

Coordenadas en cm: x a lo ancho (0-54), y en profundidad (negativo = frente,
lado del electroimán y de la electrónica), z en altura sobre la mesa.
"""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Wedge, Arc, FancyArrowPatch

K, A = 0.5, math.radians(35)


def P(x, y, z):
    return (x + K * y * math.cos(A), z + K * y * math.sin(A))


def shade(c, f):
    return tuple(min(1, max(0, v * f)) for v in c)


def box(ax, x0, x1, y0, y1, z0, z1, color, ec=(0.25, 0.18, 0.1), lw=0.8, z=1):
    front = [P(x0, y0, z0), P(x1, y0, z0), P(x1, y0, z1), P(x0, y0, z1)]
    top = [P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)]
    right = [P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1)]
    for pts, f in ((right, 0.78), (top, 1.12), (front, 1.0)):
        ax.add_patch(Polygon(pts, closed=True, fc=shade(color, f), ec=ec, lw=lw, zorder=z))


def cable(ax, pts, color="#2b2b2b", z=6, lw=1.3):
    xy = [P(*p) for p in pts]
    ax.plot([p[0] for p in xy], [p[1] for p in xy], color=color, lw=lw, zorder=z,
            solid_capstyle="round", solid_joinstyle="round")


def label(ax, xy, txt, xytext, z=50, fs=10.5):
    ax.annotate(txt, xy=xy, xytext=xytext, fontsize=fs, zorder=z,
                ha="left" if xytext[0] > xy[0] else "right", va="center",
                arrowprops=dict(arrowstyle="-", color="#333", lw=0.9, shrinkA=0, shrinkB=0),
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#999", lw=0.6))


WOOD_BASE = (0.72, 0.53, 0.33)
WOOD_FRAME = (0.84, 0.66, 0.44)
WOOD_DOOR = (0.93, 0.79, 0.58)
METAL = (0.70, 0.72, 0.75)
STEEL = (0.55, 0.57, 0.60)
WHITE = (0.97, 0.97, 0.96)
C_ESP = (0.16, 0.20, 0.30)
C_RELE = (0.20, 0.42, 0.80)
C_LM = (0.18, 0.55, 0.45)
C_ADXL = (0.50, 0.32, 0.72)
C_SIRENA = (0.18, 0.18, 0.20)
C_PIR = (0.25, 0.55, 0.30)

fig = plt.figure(figsize=(22, 10), dpi=150)
ax = fig.add_axes([0.0, 0.02, 0.46, 0.86])
ax2 = fig.add_axes([0.475, 0.07, 0.24, 0.78])
ax3 = fig.add_axes([0.745, 0.07, 0.235, 0.78])
fig.text(0.02, 0.95, "Maqueta de puerta · resultado final", fontsize=21, weight="bold")
fig.text(0.02, 0.915, "Vista frontal (lado protegido: electroimán y electrónica). "
         "La puerta abre hacia atrás, alejándose del electroimán. Triplay de 18 mm, medidas en cm.",
         fontsize=11.5, color="#444")

T = 1.8
BH = T
PH = 61
top = BH + PH

# ---------------- estructura ----------------
box(ax, 0, 54, -12, 13, 0, BH, WOOD_BASE, z=1)                       # base 25 x 54
box(ax, 0, 7, 0, T, BH, BH + PH, WOOD_FRAME, z=2)                    # lado izquierdo
for zb in (12, 48):                                                  # bisagras (detrás)
    box(ax, 6.4, 7.6, -0.2, 0, BH + zb, BH + zb + 6, (0.35, 0.35, 0.38), lw=0.5, z=4)
dx0, dx1 = 7.25, 46.75
dz0, dz1 = BH + 0.4, BH + 0.4 + 60
box(ax, dx0, dx1, 0, T, dz0, dz1, WOOD_DOOR, z=3)                    # puerta 39,5 x 60

# ADXL335 en la puerta, cerca de las bisagras para que el cable flexione poco
ax_x, ax_z = 12.0, 34.0
box(ax, ax_x, ax_x + 2.0, -0.35, 0, ax_z, ax_z + 1.8, C_ADXL, lw=0.5, z=5)
# placa de anclaje
box(ax, 17.75, 36.25, -1.25, 0, dz1 - 6.1, dz1, STEEL, z=5)
# MC-38: imán en el canto de la puerta
box(ax, 44.6, 46.0, -1.0, 0, 34, 37, WHITE, ec="#555", lw=0.6, z=5)

# lado derecho
box(ax, 47, 54, 0, T, BH, BH + PH, WOOD_FRAME, z=6)
box(ax, 48.0, 49.6, -1.2, 0, 34, 37, WHITE, ec="#555", lw=0.6, z=7)   # MC-38 sensor

# PIR en el lado izquierdo, mirando al frente
box(ax, 2.0, 5.2, -0.4, 0, 47, 49.4, C_PIR, lw=0.5, z=7)
box(ax, 2.5, 4.7, -1.9, -0.4, 47.1, 49.3, WHITE, ec="#666", lw=0.5, z=8)

# escuadras inferiores
for xs in (1.5, 48.5):
    box(ax, xs, xs + 4, -3, 0, BH, BH + 0.3, METAL, lw=0.5, z=8)
    box(ax, xs, xs + 4, -0.3, 0, BH, BH + 3, METAL, lw=0.5, z=8)

# ---------------- cables (van pegados a la madera con grapas o precintos) ----------------
# PIR: baja por el lado izquierdo hasta la protoboard
cable(ax, [(3.6, -0.45, 47), (3.6, -0.45, BH + 3.5), (3.6, -4.5, BH + 0.05), (14, -4.5, BH + 0.05)])
# ADXL335: va hacia las bisagras, cruza con un bucle holgado y baja por el lado izquierdo
cable(ax, [(ax_x, -0.4, ax_z + 0.9), (8.2, -0.4, ax_z + 0.9), (7.0, -1.6, ax_z - 1.5),
           (5.8, -0.45, ax_z - 3), (5.8, -0.45, BH + 3.5), (5.8, -6.5, BH + 0.05), (14, -6.5, BH + 0.05)])
# MC-38: baja por el lado derecho hasta la protoboard
cable(ax, [(49.6, -1.25, 35.5), (50.5, -0.45, 35.5), (50.5, -0.45, BH + 3.5),
           (50.5, -9.8, BH + 0.05), (28, -9.8, BH + 0.05)])

# ---------------- electrónica sobre la base (franja delantera) ----------------
# jack DC de 12 V + LM2596
box(ax, 0.6, 2.4, -10.5, -8.5, BH, BH + 1.6, (0.12, 0.12, 0.12), lw=0.5, z=9)
box(ax, 6.5, 10.8, -10.5, -8.4, BH, BH + 1.2, C_LM, lw=0.5, z=9)
# protoboard con el ESP32
box(ax, 13, 29.5, -9.5, -4.0, BH, BH + 0.9, WHITE, ec="#777", lw=0.5, z=9)
box(ax, 15.5, 21.0, -8.2, -5.4, BH + 0.9, BH + 1.6, C_ESP, lw=0.5, z=10)
# relé de 2 canales
box(ax, 31, 36, -9.5, -5.6, BH, BH + 1.9, C_RELE, lw=0.5, z=9)
# sirena GP-04
box(ax, 39, 45, -9.5, -4.5, BH, BH + 4.2, C_SIRENA, lw=0.5, z=9)
# cables de alimentación y potencia sobre la base
cable(ax, [(2.4, -9.5, BH + 0.8), (6.5, -9.5, BH + 0.6)], color="#c0392b", z=11, lw=1.5)
cable(ax, [(10.8, -9.0, BH + 0.6), (13, -9.0, BH + 0.5)], color="#c0392b", z=11, lw=1.5)
cable(ax, [(29.5, -7.5, BH + 0.5), (31, -7.5, BH + 0.9)], z=11)
cable(ax, [(36, -8.0, BH + 1.0), (39, -8.0, BH + 1.5)], color="#c0392b", z=11, lw=1.5)
# adaptador 12 V hacia el enchufe
cable(ax, [(0.6, -9.5, BH + 0.8), (-3, -9.5, BH + 0.8), (-4.5, -9.5, -2.5)], color="#111", z=11, lw=2)

# electroimán bajo el dintel y su cable por el lado derecho hasta el relé
box(ax, 14.5, 39.5, -3.85, -1.25, top - 4.8, top, METAL, z=12)
cable(ax, [(39.5, -2.5, top - 2.4), (51.8, -2.5, top - 2.4), (51.8, -0.45, top - 4),
           (51.8, -0.45, BH + 3.5), (51.8, -11.0, BH + 0.05), (35, -11.0, BH + 0.05), (35, -9.5, BH + 1.9)],
      color="#c0392b", z=13, lw=1.5)
for xs in (1.5, 48.5):                                               # escuadras superiores
    box(ax, xs, xs + 4, -0.3, 0, top - 3, top, METAL, lw=0.5, z=12)
    box(ax, xs, xs + 4, -3, 0, top - 0.3, top, METAL, lw=0.5, z=12)
box(ax, 0, 54, -5.2, T, top, top + T, WOOD_FRAME, z=14)             # dintel 7 x 54

# ---------------- etiquetas ----------------
R = 68
Lx = -10
label(ax, P(27, -5.2, top + 1.2), "Dintel 7 × 54", P(Lx, -5.2, top + 9))
label(ax, P(6.4, -0.2, BH + 53), "Bisagras ×2 (por detrás)", P(Lx, -0.2, 63))
label(ax, P(3.6, -1.9, 48.2), "PIR HC-SR501\n(lado izq., h ≈ 47 cm,\nmirando al frente)", P(Lx, -1.9, 51))
label(ax, P(ax_x + 1, -0.35, ax_z + 0.9), "ADXL335\n(puerta, h ≈ 34 cm,\na 5 cm de la bisagra)", P(Lx, -0.35, 37))
label(ax, P(3.5, 0, 22), "Lado 7 × 61", P(Lx, 0, 25))
label(ax, P(18, -6.8, BH + 1.6), "ESP32 en protoboard", P(Lx, -6.8, 15))
label(ax, P(8.6, -9.5, BH + 1.2), "LM2596 (12 V → 5 V)", P(Lx, -9.5, 8))
label(ax, P(1.5, -9.5, BH + 1.6), "Jack DC 12 V\n← adaptador 12 V 3 A", P(Lx, -9.5, 0))

label(ax, P(27, -2.5, top - 2.4), "Electroimán 12 V\n(bajo el dintel)", P(R, -2.5, top + 6))
label(ax, P(33, -1.25, dz1 - 4), "Placa de anclaje\n(atornillada a la puerta)", P(R, -1.2, dz1 - 8.5))
label(ax, P(49.6, -1.2, 35.5), "MC-38 (h ≈ 35 cm)\nsensor en el marco,\nimán en la puerta", P(R, -1, 40))
label(ax, P(30, 0, 22), "Puerta 39,5 × 60", P(R, 0, 27))
label(ax, P(42, -9.5, BH + 4.2), "Sirena GP-04", P(R, -9.5, 17))
label(ax, P(33.5, -9.5, BH + 1.9), "Relé 2 canales\n(CH1 cerradura, CH2 sirena)", P(R, -9.5, 9.5))
label(ax, P(48, -12, 0.9), "Base 25 × 54", P(R, -12, -1))

ax.set_xlim(-36, 96)
ax.set_ylim(-14, 76)
ax.set_aspect("equal")
ax.axis("off")

# ---------------- vista de planta ----------------
ax2.set_title("Vista de planta (desde arriba)", fontsize=13, weight="bold", loc="left")
# frente (lado protegido) abajo; atrás arriba
ax2.add_patch(Rectangle((0, -12), 54, 25, fc=WOOD_BASE, ec="#5a3e22", lw=1))
ax2.add_patch(Rectangle((0, 0), 7, T, fc=WOOD_FRAME, ec="#5a3e22", lw=0.8))
ax2.add_patch(Rectangle((47, 0), 7, T, fc=WOOD_FRAME, ec="#5a3e22", lw=0.8))
# puerta cerrada y abierta
ax2.add_patch(Rectangle((dx0, 0), dx1 - dx0, T, fc=WOOD_DOOR, ec="#5a3e22", lw=0.8, zorder=3))
ax2.add_patch(Rectangle((dx0, T), T, 39.5, fc="none", ec="#8a6a45", lw=0.9, ls="--", zorder=3))
ax2.add_patch(Arc((dx0, T), 2 * 39.5, 2 * 39.5, theta1=0, theta2=90, ec="#8a6a45", lw=0.9, ls="--"))
ax2.text(dx0 + 4.5, 36.5, "puerta abierta 90°", fontsize=9, color="#6b4f2f")
ax2.text(27, 25.5, "dejar ~40 cm libres\ndetrás para que abra", fontsize=9.5, color="#6b4f2f",
         ha="center")
# dintel arriba (contorno)
ax2.add_patch(Rectangle((0, -5.2), 54, 7.0, fc="none", ec="#5a3e22", lw=0.8, ls=(0, (2, 2)), zorder=4))
# electroimán y placa
ax2.add_patch(Rectangle((14.5, -3.85), 25, 2.6, fc=METAL, ec="#555", lw=0.6, zorder=4))
ax2.add_patch(Rectangle((17.75, -1.25), 18.5, 1.25, fc=STEEL, ec="#555", lw=0.6, zorder=4))
# sensores
ax2.add_patch(Rectangle((2.5, -1.9), 2.2, 1.9, fc=WHITE, ec="#555", lw=0.6, zorder=5))
for ang in (240, 300):
    ex, ey = 3.6 + 13 * math.cos(math.radians(ang)), -1.9 + 13 * math.sin(math.radians(ang))
    ax2.plot([3.6, ex], [-1.9, ey], color="#2a5fa8", lw=0.9, ls=(0, (3, 2)), zorder=7)
ax2.add_patch(Rectangle((48.0, -1.2), 1.6, 1.2, fc=WHITE, ec="#555", lw=0.6, zorder=5))
ax2.add_patch(Rectangle((44.6, -1.0), 1.4, 1.0, fc=WHITE, ec="#555", lw=0.6, zorder=5))
ax2.add_patch(Rectangle((ax_x, -0.35), 2.0, 0.35, fc=C_ADXL, ec="#333", lw=0.4, zorder=5))
# electrónica
for x0, y0, w, h, c in ((0.6, -10.5, 1.8, 2.0, (0.12, 0.12, 0.12)), (6.5, -10.5, 4.3, 2.1, C_LM),
                        (13, -9.5, 16.5, 5.5, WHITE), (15.5, -8.2, 5.5, 2.8, C_ESP),
                        (31, -9.5, 5, 3.9, C_RELE), (39, -9.5, 6, 5, C_SIRENA)):
    ax2.add_patch(Rectangle((x0, y0), w, h, fc=c, ec="#444", lw=0.5, zorder=5))
# cotas
def cota(a, b, txt, off, vertical=False):
    ax2.add_patch(FancyArrowPatch(a, b, arrowstyle="<->", mutation_scale=9, color="#333", lw=0.8))
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    ax2.text(mx + (off if vertical else 0), my + (0 if vertical else off), txt, fontsize=9.5,
             ha="left" if vertical else "center", va="center", color="#222",
             rotation=0, bbox=dict(fc="white", ec="none", pad=0.5))
cota((0, -15), (54, -15), "54", -0.2)
cota((56.5, -12), (56.5, 13), "25", 1.0, vertical=True)
cota((dx0, 3.6), (dx1, 3.6), "puerta 39,5", 0)
ax2.text(27, -19.5, "FRENTE · lado protegido\n(electroimán, PIR, MC-38 y electrónica)", ha="center",
         va="top", fontsize=10, weight="bold", color="#333")
ax2.text(27, 45.5, "ATRÁS · hacia aquí abre la puerta", ha="center", fontsize=10, weight="bold", color="#333")
ax2.text(-2.5, -17.2, "cono del PIR", fontsize=8.5, color="#2a5fa8", ha="left")
def nombre(x, y, t, c="#222", fs=7.2, **kw):
    ax2.text(x, y, t, fontsize=fs, color=c, ha="center", va="center", zorder=9, **kw)
nombre(18.25, -6.8, "ESP32", "white")
nombre(25.3, -8.6, "protoboard", "#555", fs=6.5)
nombre(33.5, -7.55, "Relé", "white")
nombre(42, -7.0, "Sirena", "white")
nombre(8.65, -7.0, "LM2596")
nombre(1.5, -7.3, "12 V", fs=6.5)
nombre(27, -2.55, "Electroimán (arriba)", fs=7)
nombre(3.6, -3.0, "PIR", fs=6.8)
nombre(10.4, -2.4, "ADXL", "#5a3a8a", fs=6.5)
nombre(50.7, -2.6, "MC-38", fs=6.8)
ax2.text(0, -27.5, "Altura total ≈ 64,6 cm (base 1,8 + lados 61 + dintel 1,8).\n"
         "Escuadras metálicas (4) en las uniones del marco.\n"
         "Los cables van sujetos a la madera con grapas o precintos;\n"
         "el del ADXL335 deja un bucle holgado en las bisagras.",
         fontsize=9.8, va="top", color="#333")
ax2.plot([0, 4], [-39, -39], color="#2b2b2b", lw=1.3)
ax2.text(5, -39, "cable de señal de un sensor", fontsize=9.5, va="center", color="#333")
ax2.plot([0, 4], [-42.5, -42.5], color="#c0392b", lw=1.5)
ax2.text(5, -42.5, "cable de alimentación (12 V / 5 V)", fontsize=9.5, va="center", color="#333")
ax2.set_xlim(-3, 62)
ax2.set_ylim(-45, 48)
ax2.set_aspect("equal")
ax2.axis("off")


# ---------------- plano de cortes ----------------
ax3.set_title("Cortes en una pieza de ~65 × 90 cm (18 mm)", fontsize=13, weight="bold", loc="left")
ax3.add_patch(Rectangle((0, 0), 65, 90, fc="#f3ead9", ec="#8a6a45", lw=1.2, ls="--"))
for x, y, w, h, t, c in ((0.5, 28.5, 39.5, 60, "Puerta\n39,5 × 60", WOOD_DOOR),
                         (40.5, 28.5, 7, 61, "Lado\n7 × 61", WOOD_FRAME),
                         (48, 28.5, 7, 61, "Lado\n7 × 61", WOOD_FRAME),
                         (55.5, 28.5, 7, 54, "Dintel\n7 × 54", WOOD_FRAME),
                         (0.5, 2, 54, 25, "Base\n25 × 54", WOOD_BASE)):
    ax3.add_patch(Rectangle((x, y), w, h, fc=c, ec="#5a3e22", lw=1))
    rot = 90 if w < 10 else 0
    ax3.text(x + w / 2, y + h / 2, t.replace("\n", "  ") if rot else t, rotation=rot,
             ha="center", va="center", fontsize=10 if rot else 12)
ax3.text(0, -5, "Medidas en cm. Pedir los cortes en la maderera.\n"
         "Además: 2 bisagras de 2–3\", tornillos para madera 1½\"\ny 4 escuadras metálicas.",
         fontsize=10.5, va="top", color="#333")
ax3.set_xlim(-1, 66)
ax3.set_ylim(-45, 92)
ax3.set_aspect("equal")
ax3.axis("off")

import sys, pathlib
out = sys.argv[1] if len(sys.argv) > 1 else str(pathlib.Path(__file__).resolve().parents[2] / "04_compras_y_montaje" / "maqueta_puerta_final.png")
fig.savefig(out, facecolor="white")
print(out)
