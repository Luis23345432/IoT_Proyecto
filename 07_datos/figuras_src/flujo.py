"""Genera el diagrama de flujo del firmware (draw.io) a partir de nodo_seguridad.ino."""
import sys
from xml.sax.saxutils import escape
cells, n = [], [0]
def nid():
    n[0] += 1; return f"n{n[0]}"
EST = {
 "term": "rounded=1;arcSize=50;whiteSpace=wrap;html=1;fillColor=#E6E6E6;strokeColor=#333333;fontSize=11;fontStyle=1;",
 "proc": "rounded=0;whiteSpace=wrap;html=1;fillColor=#D6E6F2;strokeColor=#333333;fontSize=11;",
 "io":   "shape=parallelogram;perimeter=parallelogramPerimeter;fixedSize=1;size=12;whiteSpace=wrap;html=1;fillColor=#E1F5DC;strokeColor=#333333;fontSize=11;",
 "dec":  "rhombus;whiteSpace=wrap;html=1;fillColor=#FFF2CC;strokeColor=#333333;fontSize=10.5;",
 "sub":  "shape=process;whiteSpace=wrap;html=1;fillColor=#F8D7E3;strokeColor=#333333;fontSize=11;size=0.08;",
 "act":  "rounded=0;whiteSpace=wrap;html=1;fillColor=#F8D0D0;strokeColor=#333333;fontSize=11;",
 "grp":  "rounded=0;whiteSpace=wrap;html=1;dashed=1;dashPattern=4 4;fillColor=none;strokeColor=#999999;fontColor=#555555;fontStyle=1;fontSize=12;align=left;verticalAlign=top;spacingLeft=8;spacingTop=4;",
}
def box(tipo, txt, x, y, w, h):
    i = nid()
    cells.append(f'<mxCell id="{i}" value="{escape(txt, {chr(34): "&quot;"})}" style="{EST[tipo]}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    return i
def edge(a, b, label="", sx=None, sy=None, tx=None, ty=None, pts=()):
    i = nid(); st = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;strokeColor=#333333;fontSize=10;labelBackgroundColor=#FFFFFF;"
    if sx is not None: st += f"exitX={sx};exitY={sy};exitDx=0;exitDy=0;"
    if tx is not None: st += f"entryX={tx};entryY={ty};entryDx=0;entryDy=0;"
    p = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in pts)
    g = f'<mxGeometry relative="1" as="geometry">' + (f'<Array as="points">{p}</Array>' if p else '') + '</mxGeometry>'
    cells.append(f'<mxCell id="{i}" value="{escape(label)}" style="{st}" edge="1" parent="1" source="{a}" target="{b}">{g}</mxCell>')

# ---------------- columna principal ----------------
X, W = 60, 280; cx = X + W / 2
box("grp", "a) Programa principal", 20, 10, 610, 1190)
ini = box("term", "Inicio", cx - 60, 45, 120, 36)
s1 = box("proc", "Relés en reposo antes de configurar las salidas<br>(sin pulsos al arrancar)", X, 100, W, 46)
s2 = box("proc", "Entradas: PIR (GPIO27), MC-38 (GPIO26, pull-up)<br>ADC 12 bits, 11 dB en GPIO34/35/32", X, 162, W, 46)
s3 = box("io", "Wi-Fi + hora NTP + MQTT<br>(LWT retenido en casa/nodo1/lwt)", X, 224, W, 46)
lp = box("proc", "<b>loop()</b>", cx - 60, 290, 120, 32)
c1 = box("proc", "Mantener conexión: reintenta Wi-Fi cada 10 s<br>y MQTT cada 5 s, sin detener el sensado", X, 340, W, 46)
c2 = box("io", "Atender comandos de casa/nodo1/cmd<br>(armar, desarmar, silenciar, relés)", X, 402, W, 46)
d1 = box("dec", "¿Flanco de subida<br>del PIR y fuera de<br>los 60 s de calentamiento?", X + 25, 470, W - 50, 86)
e1 = box("sub", "eventoSensor(P)", 400, 493, 160, 40)
d2 = box("dec", "¿Contacto cambió<br>y se mantuvo 30 ms?", X + 25, 590, W - 50, 76)
e2 = box("sub", "eventoSensor(R)", 400, 608, 160, 40)
d3 = box("dec", "¿Pasaron 5 ms<br>(200 Hz)?", X + 45, 700, W - 90, 66)
a1 = box("proc", "Leer X, Y, Z → filtro EMA (α = 0,25)<br>d = ‖ f − b ‖ respecto del reposo b", X, 786, W, 46)
d4 = box("dec", "¿d &gt; η = 40 durante<br>N<sub>v</sub> = 3 muestras?", X + 25, 852, W - 50, 76)
e3 = box("sub", "eventoSensor(V)", 400, 870, 160, 40)
a2 = box("proc", "Actualizar estado: saliendo → armado (30 s);<br>sospecha → armado si vence W;<br>corte de sirena a los 60 s", X, 962, W, 58)
d5 = box("dec", "¿Hubo cambio o<br>pasaron 250 ms?", X + 45, 1040, W - 90, 66)
a3 = box("io", "Publicar foto JSON en<br>iot/seguridad/sensores", X, 1126, W, 46)

for a, b in [(ini, s1), (s1, s2), (s2, s3), (s3, lp), (lp, c1), (c1, c2), (c2, d1)]:
    edge(a, b)
edge(d1, e1, "sí", 1, 0.5, 0, 0.5)
edge(d1, d2, "no", 0.5, 1, 0.5, 0)
edge(e1, d2, "", 0.5, 1, 0.5, 0, pts=[(480, 574), (cx, 574)])
edge(d2, e2, "sí", 1, 0.5, 0, 0.5)
edge(d2, d3, "no", 0.5, 1, 0.5, 0)
edge(e2, d3, "", 0.5, 1, 0.5, 0, pts=[(480, 684), (cx, 684)])
edge(d3, a1, "sí", 0.5, 1, 0.5, 0)
edge(d3, a2, "no", 0, 0.5, 0, 0.5, pts=[(40, 733), (40, 991)])
edge(a1, d4)
edge(d4, e3, "sí", 1, 0.5, 0, 0.5)
edge(d4, a2, "no", 0.5, 1, 0.5, 0)
edge(e3, a2, "", 0.5, 1, 0.5, 0, pts=[(480, 946), (cx, 946)])
edge(a2, d5)
edge(d5, a3, "sí", 0.5, 1, 0.5, 0)
edge(d5, lp, "no", 1, 0.5, 1, 0.5, pts=[(600, 1073), (600, 306)])
edge(a3, lp, "", 1, 0.5, 1, 0.5, pts=[(600, 1149), (600, 306)])

# ---------------- subrutina eventoSensor ----------------
X2, W2 = 700, 300; c2x = X2 + W2 / 2
box("grp", "b) eventoSensor(c), c ∈ {P, R, V}", 660, 10, 400, 720)
i2 = box("term", "Evento del canal c", c2x - 80, 45, 160, 36)
b1 = box("io", "Publicar evento en casa/nodo1/evento<br>(canal, detalle, estado, hora NTP)", X2, 100, W2, 46)
q1 = box("dec", "¿Estado armado<br>o sospecha?", X2 + 50, 166, W2 - 100, 70)
f1 = box("term", "Fin", 975, 185, 60, 32)
b2 = box("proc", "Registrar t<sub>c</sub> (hora del último evento del canal)", X2, 256, W2 - 0, 40)
q2 = box("dec", "¿Estado armado?", X2 + 50, 316, W2 - 100, 60)
b3 = box("act", "Estado ← sospecha<br>si c = V: bloquear cerradura (preventivo)", X2, 396, W2, 46)
q3 = box("dec", "¿≥ 2 canales distintos<br>con evento en<br>W = 10 s?", X2 + 40, 462, W2 - 80, 86)
b4 = box("act", "<b>Estado ← alarma</b><br>sirena y cerradura activas", X2, 568, W2, 46)
f2 = box("term", "Fin", c2x - 35, 640, 70, 32)
edge(i2, b1); edge(b1, q1)
edge(q1, b2, "sí", 0.5, 1, 0.5, 0)
edge(q1, f1, "no", 1, 0.5, 0, 0.5)
edge(b2, q2)
edge(q2, b3, "sí", 0.5, 1, 0.5, 0)
edge(q2, q3, "no", 0, 0.5, 0, 0.5, pts=[(680, 346), (680, 505)])
edge(b3, q3)
edge(q3, b4, "sí", 0.5, 1, 0.5, 0)
edge(q3, f2, "no", 1, 0.5, 1, 0.5, pts=[(1030, 505), (1030, 656)])
edge(b4, f2)

# leyenda de estados
box("proc", "<div style='text-align:left'><b>Estados:</b> desarmado → (armar) → saliendo → (30 s) → armado → sospecha → alarma.<br>"
    "<b>desarmar</b> apaga todo y vuelve a desarmado desde cualquier estado; <b>silenciar</b> apaga la sirena.</div>",
    660, 760, 400, 70)
xml = ('<mxfile host="drawio"><diagram id="flujo" name="Diagrama de flujo"><mxGraphModel dx="1200" dy="900" grid="0" '
       'gridSize="10" guides="1" page="0" math="0" shadow="0" background="#FFFFFF"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
       + "".join(cells) + '</root></mxGraphModel></diagram></mxfile>')
open(sys.argv[1], "w").write(xml)
