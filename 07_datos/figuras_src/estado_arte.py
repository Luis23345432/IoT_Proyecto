"""Figura del estado del arte: qué cubre cada trabajo revisado frente a los
cuatro requisitos del planteamiento del problema."""
import sys
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

trabajos = ["Oduah et al. [2025]", "Al-Khalli et al. [2023]", "Gupta et al. [2021]",
            "Babiuch y Postulka [2020]", "Somwong et al. [2026]", "Rahul et al. [2026]",
            "Netinant et al. [2024]", "Zhang et al. [2025]", "Este trabajo"]
criterios = ["Fusión de\ntecnologías\nde sensado", "Bloqueo\nfísico del\nacceso",
             "Enlace\ninalámbrico\n(MQTT u otro)", "Decisión\nlocal en\nel nodo", "Métricas de\ndesempeño\nreportadas"]
# 2 = cubre, 1 = parcial, 0 = no cubre (según el análisis de la Sección 4)
M = [[1, 1, 0, 2, 1],
     [0, 0, 2, 2, 2],
     [0, 0, 2, 1, 0],
     [0, 0, 2, 0, 0],
     [1, 0, 2, 2, 2],
     [0, 0, 2, 0, 2],
     [0, 0, 2, 1, 2],
     [2, 1, 2, 2, 2],
     [2, 2, 2, 2, 2]]
FILL = {2: "#2a78d6", 1: "#a9c8ee", 0: "#f1f0ed"}
TXT = {2: ("✓", "white"), 1: ("◐", "#0b0b0b"), 0: ("–", "#8a8983")}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
fig, ax = plt.subplots(figsize=(8.2, 5.4), dpi=200)
cw, ch, gap = 1.55, 0.62, 0.06
for i, fila in enumerate(M):
    y = -i * ch
    for j, v in enumerate(fila):
        ax.add_patch(FancyBboxPatch((j * cw + gap, y + gap), cw - 2 * gap, ch - 2 * gap,
                                    boxstyle="round,pad=0,rounding_size=0.06", fc=FILL[v], ec="none"))
        s, c = TXT[v]
        ax.text(j * cw + cw / 2, y + ch / 2, s, ha="center", va="center", color=c, fontsize=13, fontweight="bold")
    ax.text(-0.15, y + ch / 2, trabajos[i], ha="right", va="center",
            fontweight="bold" if i == len(M) - 1 else "normal", color="#0b0b0b")
    cub = sum(fila)
    ax.text(len(criterios) * cw + 0.15, y + ch / 2, f"{cub}/10", ha="left", va="center", color="#52514e", fontsize=9)
# separador antes de "Este trabajo"
ax.plot([-3.4, len(criterios) * cw + 0.8], [-(len(M) - 2) * ch] * 2, color="#52514e", lw=0.8, ls=(0, (3, 3)), clip_on=False)
for j, c in enumerate(criterios):
    ax.text(j * cw + cw / 2, ch + 0.12, c, ha="center", va="bottom", fontsize=8.5, color="#0b0b0b", linespacing=1.15)
ax.text(len(criterios) * cw + 0.15, ch + 0.12, "Puntaje", ha="left", va="bottom", fontsize=9, color="#52514e")
# leyenda
lx, ly = 0.0, -len(M) * ch - 0.25
for k, (v, nombre) in enumerate([(2, "cubre el criterio"), (1, "lo cubre en parte"), (0, "no lo cubre")]):
    x = lx + k * 2.6
    ax.add_patch(FancyBboxPatch((x, ly - 0.2), 0.32, 0.32, boxstyle="round,pad=0,rounding_size=0.05", fc=FILL[v], ec="none"))
    ax.text(x + 0.16, ly - 0.04, TXT[v][0], ha="center", va="center", color=TXT[v][1], fontsize=9, fontweight="bold")
    ax.text(x + 0.42, ly - 0.04, nombre, ha="left", va="center", fontsize=9, color="#52514e")
ax.set_xlim(-3.6, len(criterios) * cw + 0.9)
ax.set_ylim(ly - 0.4, ch + 1.0)
ax.set_aspect("equal"); ax.axis("off")
fig.savefig(sys.argv[1], bbox_inches="tight", facecolor="white")
