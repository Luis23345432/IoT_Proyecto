<template>
  <div class="sx">
    <header class="sx-top">
      <div>
        <div class="sx-eyebrow">Sistema de seguridad residencial · Nodo 1</div>
        <h1 class="sx-title">Puerta principal</h1>
      </div>
      <div class="sx-chips">
        <span v-if="online && m.lat != null" class="sx-chip" title="Desde que el ESP32 mide hasta que llega aquí"><v-icon size="16">mdi-timer-outline</v-icon>{{ m.lat }} ms</span>
        <span v-if="pirCal" class="sx-chip sx-c-info"><v-icon size="16">mdi-timer-sand</v-icon>PIR calentando</span>
        <span class="sx-chip" :class="online ? 'sx-c-ok' : 'sx-c-off'">
          <span class="sx-dot"></span>{{ online ? 'En línea' : 'Sin conexión' }}<span class="sx-muted">· {{ visto }}</span>
        </span>
      </div>
    </header>

    <section class="sx-hero" :class="'sx-h-' + nivel">
      <div class="sx-hero-icon"><v-icon size="40">{{ heroIcon }}</v-icon></div>
      <div class="sx-hero-text">
        <div class="sx-hero-title">{{ heroTitulo }}</div>
        <div class="sx-hero-sub">{{ heroSub }}</div>
      </div>
      <div class="sx-actions">
        <div class="sx-mode">Modo del sistema: <b>{{ modoTexto }}</b></div>
        <div class="sx-btns">
          <button class="sx-btn sx-b-arm" :disabled="!online || (m.modo && m.modo !== 'desarmado')" @click="cmd('armar')"><v-icon size="18">mdi-shield-lock</v-icon>Armar</button>
          <button class="sx-btn sx-b-dis" :disabled="!online" @click="cmd('desarmar')"><v-icon size="18">mdi-shield-off-outline</v-icon>Desarmar</button>
          <button class="sx-btn sx-b-sil" :disabled="!online || !m.sirena" @click="cmd('silenciar')"><v-icon size="18">mdi-volume-off</v-icon>Silenciar</button>
        </div>
      </div>
    </section>

    <section class="sx-grid">
      <div v-for="c in tarjetas" :key="c.id" class="sx-card sx-sensor" :class="'sx-s-' + c.nivel">
        <div class="sx-card-head">
          <div class="sx-ico"><v-icon size="24">{{ c.icono }}</v-icon></div>
          <div>
            <div class="sx-card-title">{{ c.titulo }}</div>
            <div class="sx-card-sub">{{ c.sensor }}</div>
          </div>
        </div>
        <div class="sx-state"><span class="sx-sdot"></span>{{ c.estado }}</div>
        <div v-if="c.barra !== undefined" class="sx-bar" title="La marca es el umbral">
          <div class="sx-bar-fill" :style="{ width: c.barra + '%' }"></div>
          <div class="sx-bar-mark"></div>
        </div>
        <div class="sx-card-foot">{{ c.pie }}</div>
      </div>
    </section>

    <section class="sx-grid sx-act">
      <div v-for="a in actuadores" :key="a.id" class="sx-card sx-sensor" :class="'sx-s-' + a.nivel">
        <div class="sx-card-head">
          <div class="sx-ico"><v-icon size="24">{{ a.icono }}</v-icon></div>
          <div class="sx-grow">
            <div class="sx-card-title">{{ a.titulo }}</div>
            <div class="sx-card-sub">{{ a.sensor }}</div>
          </div>
          <button class="sx-tgl" :class="{ on: a.on }" :disabled="!online" @click="cmd(a.on ? a.off : a.onCmd)">
            <v-icon size="18">{{ a.on ? a.iconoOff : a.iconoOn }}</v-icon>{{ a.on ? a.txtOff : a.txtOn }}
          </button>
        </div>
        <div class="sx-state"><span class="sx-sdot"></span>{{ a.estado }}</div>
        <div class="sx-card-foot">{{ a.pie }}</div>
      </div>
    </section>

    <section class="sx-grid2">
      <div class="sx-card">
        <div class="sx-card-row">
          <div class="sx-card-title">Acelerómetro · últimos 60 s</div>
          <div class="sx-xyz"><span>X {{ s.x ?? '–' }}</span><span>Y {{ s.y ?? '–' }}</span><span>Z {{ s.z ?? '–' }}</span></div>
        </div>
        <svg class="sx-chart" viewBox="0 0 600 160" preserveAspectRatio="none">
          <line x1="0" :y1="yUmbral" x2="600" :y2="yUmbral" class="sx-thr" />
          <polygon v-if="puntos" :points="area" class="sx-area" />
          <polyline v-if="puntos" :points="puntos" class="sx-line" />
        </svg>
        <div class="sx-legend">
          <span class="sx-lg"><i class="sx-lg-line"></i>Desviación respecto del reposo</span>
          <span class="sx-lg"><i class="sx-lg-thr"></i>Umbral ({{ umbral }})</span>
        </div>
      </div>

      <div class="sx-card">
        <div class="sx-card-row">
          <div class="sx-card-title">Actividad reciente</div>
          <button class="sx-link" @click="reset"><v-icon size="16">mdi-restart</v-icon>Reiniciar</button>
        </div>
        <div v-if="!eventos.length" class="sx-empty">Sin eventos todavía</div>
        <ul class="sx-feed">
          <li v-for="(e, i) in eventos" :key="e.t + '-' + i">
            <span class="sx-fico" :class="'sx-e-' + e.tipo"><v-icon size="16">{{ iconoEvento(e.tipo) }}</v-icon></span>
            <span class="sx-ftext">{{ e.texto }}</span>
            <span class="sx-ftime">{{ hora(e.t) }}</span>
          </li>
        </ul>
        <div class="sx-foot">Contadores desde las {{ hora(m.desde) }}</div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  data() {
    return { now: Date.now(), recibido: Date.now(), timer: null }
  },
  watch: {
    msg() { this.recibido = Date.now() }
  },
  mounted() {
    this.timer = setInterval(() => { this.now = Date.now() }, 1000)
  },
  unmounted() {
    clearInterval(this.timer)
  },
  computed: {
    m() { return (this.msg && this.msg.payload) || {} },
    s() { return this.m.sensores || {} },
    umbral() { return this.m.umbral || 40 },
    // Antigüedad del último dato sin mezclar relojes: lo que ya tenía al salir del servidor
    // más lo que pasó desde que llegó al navegador
    edad() { return this.m.ultimo ? (this.m.ahora - this.m.ultimo) + (this.now - this.recibido) : Infinity },
    online() { return this.edad < 5000 },
    visto() {
      if (!this.m.ultimo) return 'sin datos'
      const d = Math.max(0, Math.round(this.edad / 1000))
      return d <= 1 ? 'ahora' : 'hace ' + this.dur(d)
    },
    pirCal() { return this.online && this.s.pir_calibrando },
    modo() { return this.m.modo || '' },
    activos() {
      const a = []
      if (this.s.pir && !this.s.pir_calibrando) a.push('movimiento en el ambiente')
      if (this.s.puerta_abierta) a.push('puerta abierta')
      if (this.m.vibActiva) a.push('movimiento en la puerta')
      return a
    },
    nivel() {
      if (!this.online) return 'off'
      if (this.modo === 'alarma' || this.m.sirena) return 'alert'
      if (this.modo === 'sospecha' || this.activos.length) return 'warn'
      if (this.modo === 'saliendo') return 'info'
      return 'ok'
    },
    heroIcon() {
      if (this.nivel === 'ok' && this.modo === 'desarmado') return 'mdi-shield-off-outline'
      return { off: 'mdi-lan-disconnect', alert: 'mdi-alarm-light', warn: 'mdi-shield-alert', info: 'mdi-timer-sand', ok: 'mdi-shield-check' }[this.nivel]
    },
    heroTitulo() {
      if (this.nivel === 'off') return 'Sin datos del nodo'
      if (this.nivel === 'alert') return this.modo === 'alarma' ? '¡Alarma!' : 'Sirena encendida'
      if (this.modo === 'sospecha') return 'Sospecha de intrusión'
      if (this.nivel === 'warn') return 'Actividad detectada'
      if (this.modo === 'saliendo') return 'Armando en ' + (this.m.salida || 0) + ' s'
      if (this.modo === 'armado') return 'Armado y vigilando'
      return 'Todo tranquilo'
    },
    heroSub() {
      if (this.nivel === 'off') return 'Revisa que el ESP32 esté encendido y conectado al Wi-Fi.'
      if (this.modo === 'alarma') return 'Dos sensores distintos se activaron en menos de 10 s. Desarma o silencia.'
      if (this.nivel === 'alert') return 'Prueba manual: pitido corto de 0.5 s.'
      if (this.modo === 'sospecha') return 'Un sensor se activó; si otro distinto lo hace en 10 s, suena la alarma.'
      if (this.nivel === 'warn') return 'Ahora: ' + this.activos.join(', ') + '.'
      if (this.modo === 'saliendo') return 'Sal y cierra la puerta antes de que termine la cuenta.'
      if (this.modo === 'armado') return 'Ningún sensor activo. Cualquier evento pasa a sospecha.'
      return 'Sistema desarmado: los sensores se muestran pero no disparan la alarma.'
    },
    modoTexto() {
      const t = { saliendo: 'armándose', sospecha: 'sospecha' }[this.modo] || this.modo || 'sin confirmar'
      return t.charAt(0).toUpperCase() + t.slice(1)
    },
    tarjetas() {
      const s = this.s, c = this.m.cont || { pir: 0, puerta: 0, vib: 0 }, on = this.online
      const plural = (n, a, b) => n + ' ' + (n === 1 ? a : b)
      return [
        {
          id: 'pir', titulo: 'Movimiento', sensor: 'PIR HC-SR501', icono: 'mdi-motion-sensor',
          estado: !on ? 'Sin datos' : s.pir_calibrando ? 'Calentando…' : s.pir ? 'Detectando' : 'Sin movimiento',
          nivel: !on ? 'off' : s.pir_calibrando ? 'info' : s.pir ? 'warn' : 'ok',
          pie: plural(c.pir, 'activación', 'activaciones')
        },
        {
          id: 'puerta', titulo: 'Puerta', sensor: 'Contacto MC-38',
          icono: s.puerta_abierta ? 'mdi-door-open' : 'mdi-door-closed',
          estado: !on ? 'Sin datos' : s.puerta_abierta ? 'Abierta' : 'Cerrada',
          nivel: !on ? 'off' : s.puerta_abierta ? 'alert' : 'ok',
          pie: plural(c.puerta, 'apertura', 'aperturas')
        },
        {
          id: 'vib', titulo: 'Golpes y vibración', sensor: 'Acelerómetro ADXL335', icono: 'mdi-vibrate',
          estado: !on ? 'Sin datos' : this.m.vibActiva ? 'En movimiento' : 'En reposo',
          nivel: !on ? 'off' : this.m.vibActiva ? 'warn' : 'ok',
          barra: Math.min(100, Math.round((this.m.vib || 0) / this.umbral * 50)),
          pie: plural(c.vib, 'evento', 'eventos') + ' · desviación ' + (this.m.vib ?? 0)
        }
      ]
    },
    actuadores() {
      const on = this.online, m = this.m
      return [
        {
          id: 'sirena', titulo: 'Sirena', sensor: 'GP-04 12 V · relé CH2', icono: 'mdi-bullhorn',
          on: !!m.sirena, onCmd: 'sirena_on', off: 'sirena_off',
          txtOn: 'Probar', txtOff: 'Apagar', iconoOn: 'mdi-play', iconoOff: 'mdi-stop',
          estado: !on ? 'Sin datos' : m.sirena ? 'Sonando' : 'Apagada',
          nivel: !on ? 'off' : m.sirena ? 'alert' : 'ok',
          pie: 'La prueba es un pitido de 0.5 s; en alarma suena hasta 60 s.'
        },
        {
          id: 'cerradura', titulo: 'Cerradura', sensor: 'Electroimán 12 V · relé CH1', icono: m.cerradura ? 'mdi-lock' : 'mdi-lock-open-variant',
          on: !!m.cerradura, onCmd: 'cerradura_on', off: 'cerradura_off',
          txtOn: 'Bloquear', txtOff: 'Liberar', iconoOn: 'mdi-lock', iconoOff: 'mdi-lock-open-variant',
          estado: !on ? 'Sin datos' : m.cerradura ? 'Bloqueada' : 'Liberada',
          nivel: !on ? 'off' : m.cerradura ? 'info' : 'ok',
          pie: 'Se bloquea sola ante un golpe con el sistema armado.'
        }
      ]
    },
    eventos() { return this.m.eventos || [] },
    yMax() {
      const v = (this.m.serie || []).map(p => p.d)
      return Math.max(this.umbral * 2, ...v, 1)
    },
    yUmbral() { return 156 - this.umbral / this.yMax * 148 },
    coords() {
      const sr = this.m.serie || [], n = 240
      return sr.map((p, i) => [(n - sr.length + i) / (n - 1) * 600, 156 - p.d / this.yMax * 148])
    },
    puntos() { return this.coords.map(p => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' ') },
    area() {
      const c = this.coords
      if (!c.length) return ''
      return c[0][0].toFixed(1) + ',160 ' + this.puntos + ' ' + c[c.length - 1][0].toFixed(1) + ',160'
    }
  },
  methods: {
    cmd(c) { this.send({ topic: 'ui/cmd', payload: c }) },
    reset() { this.send({ topic: 'ui/reset', payload: true }) },
    hora(t) {
      return t ? new Date(t).toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' }) : '–'
    },
    dur(sec) {
      return sec < 60 ? sec + ' s' : sec < 3600 ? Math.floor(sec / 60) + ' min' : Math.floor(sec / 3600) + ' h'
    },
    iconoEvento(t) {
      return {
        pir: 'mdi-motion-sensor', puerta: 'mdi-door-open', 'puerta-ok': 'mdi-door-closed',
        vib: 'mdi-vibrate', red: 'mdi-wifi', 'red-off': 'mdi-wifi-off',
        cmd: 'mdi-send', 'cmd-ok': 'mdi-check-circle',
        alarma: 'mdi-alarm-light', estado: 'mdi-shield-outline', sirena: 'mdi-bullhorn', cerradura: 'mdi-lock'
      }[t] || 'mdi-circle-small'
    }
  }
}
</script>

<style>
.sx {
  --bg: #0b1220; --card: #111a2c; --card2: #0f1727; --line: #1e2a42;
  --text: #e8eef8; --muted: #8a97b0;
  --ok: #22c55e; --warn: #f59e0b; --alert: #ef4444; --info: #38bdf8; --off: #64748b;
  color: var(--text);
  font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  display: flex; flex-direction: column; gap: 16px;
  max-width: 1200px; margin: 0 auto; width: 100%; min-width: 0; overflow-x: hidden;
}
.sx * { box-sizing: border-box; }
.sx-top { display: flex; justify-content: space-between; align-items: flex-end; gap: 12px; flex-wrap: wrap; }
.sx-eyebrow { color: var(--muted); font-size: 13px; letter-spacing: .02em; }
.sx-title { font-size: 28px; font-weight: 700; margin: 2px 0 0; letter-spacing: -.01em; }
.sx-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.sx-chip { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 999px;
  font-size: 13px; font-weight: 600; background: var(--card); border: 1px solid var(--line); }
.sx-chip .sx-muted { color: var(--muted); font-weight: 500; }
.sx-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
.sx-c-ok { color: var(--ok); } .sx-c-ok .sx-dot { animation: sx-pulse 2s infinite; }
.sx-c-off { color: var(--off); } .sx-c-info { color: var(--info); }

.sx-hero { display: flex; align-items: center; gap: 18px; padding: 20px 22px; border-radius: 18px;
  border: 1px solid var(--line); background: var(--card); flex-wrap: wrap; }
.sx-h-ok { background: linear-gradient(135deg, rgba(34,197,94,.16), rgba(34,197,94,.03)); border-color: rgba(34,197,94,.35); }
.sx-h-warn { background: linear-gradient(135deg, rgba(245,158,11,.20), rgba(245,158,11,.04)); border-color: rgba(245,158,11,.45); }
.sx-h-alert { background: linear-gradient(135deg, rgba(239,68,68,.26), rgba(239,68,68,.05)); border-color: rgba(239,68,68,.6); }
.sx-h-alert .sx-hero-icon { color: var(--alert); background: rgba(239,68,68,.2); animation: sx-glow-r 1s infinite; }
.sx-h-info { background: linear-gradient(135deg, rgba(56,189,248,.16), rgba(56,189,248,.03)); border-color: rgba(56,189,248,.4); }
.sx-h-info .sx-hero-icon { color: var(--info); background: rgba(56,189,248,.15); }
.sx-h-off { background: linear-gradient(135deg, rgba(100,116,139,.18), rgba(100,116,139,.04)); border-color: rgba(100,116,139,.35); }
.sx-hero-icon { width: 68px; height: 68px; border-radius: 18px; display: grid; place-items: center; flex: none; }
.sx-h-ok .sx-hero-icon { color: var(--ok); background: rgba(34,197,94,.15); }
.sx-h-warn .sx-hero-icon { color: var(--warn); background: rgba(245,158,11,.18); animation: sx-glow 1.4s infinite; }
.sx-h-off .sx-hero-icon { color: var(--off); background: rgba(100,116,139,.18); }
.sx-hero-text { flex: 1 1 220px; }
.sx-hero-title { font-size: 24px; font-weight: 700; }
.sx-hero-sub { color: var(--muted); margin-top: 2px; }
.sx-actions { display: flex; flex-direction: column; gap: 8px; align-items: flex-end; }
.sx-mode { font-size: 13px; color: var(--muted); } .sx-mode b { color: var(--text); }
.sx-btns { display: flex; gap: 8px; flex-wrap: wrap; }
.sx-btn { display: inline-flex; align-items: center; gap: 6px; padding: 9px 16px; border-radius: 12px; border: 1px solid transparent;
  font-weight: 600; font-size: 14px; cursor: pointer; color: #fff; transition: transform .1s, filter .2s; }
.sx-btn:hover { filter: brightness(1.12); } .sx-btn:active { transform: scale(.97); }
.sx-b-arm { background: #2563eb; } .sx-b-dis { background: #16a34a; }
.sx-b-sil { background: transparent; border-color: #f87171; color: #fca5a5; }
.sx-btn:disabled, .sx-tgl:disabled { opacity: .4; cursor: not-allowed; filter: none; transform: none; }
.sx-grow { flex: 1; min-width: 0; }
.sx-tgl { display: inline-flex; align-items: center; gap: 4px; padding: 7px 12px; border-radius: 10px; font-weight: 600; font-size: 13px;
  cursor: pointer; background: var(--card2); border: 1px solid var(--line); color: var(--text); flex: none; }
.sx-tgl:hover { border-color: var(--muted); }
.sx-tgl.on { background: var(--alert); border-color: var(--alert); color: #fff; }

.sx-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
.sx-grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
.sx-card { background: var(--card); border: 1px solid var(--line); border-radius: 18px; padding: 18px; min-width: 0; }
.sx-card-head { display: flex; align-items: center; gap: 12px; }
.sx-ico { width: 44px; height: 44px; border-radius: 12px; display: grid; place-items: center; background: var(--card2); }
.sx-card-title { font-weight: 650; font-size: 15px; }
.sx-card-sub { color: var(--muted); font-size: 12.5px; }
.sx-state { display: flex; align-items: center; gap: 8px; font-size: 22px; font-weight: 700; margin: 16px 0 10px; }
.sx-sdot { width: 10px; height: 10px; border-radius: 50%; background: currentColor; flex: none; }
.sx-card-foot { color: var(--muted); font-size: 13px; margin-top: 8px; }
.sx-sensor { border-top-width: 3px; }
.sx-s-ok { border-top-color: var(--ok); } .sx-s-ok .sx-state, .sx-s-ok .sx-ico { color: var(--ok); }
.sx-s-warn { border-top-color: var(--warn); background: linear-gradient(180deg, rgba(245,158,11,.10), var(--card) 60%); }
.sx-s-warn .sx-state, .sx-s-warn .sx-ico { color: var(--warn); } .sx-s-warn .sx-sdot { animation: sx-pulse 1s infinite; }
.sx-s-alert { border-top-color: var(--alert); background: linear-gradient(180deg, rgba(239,68,68,.12), var(--card) 60%); }
.sx-s-alert .sx-state, .sx-s-alert .sx-ico { color: var(--alert); } .sx-s-alert .sx-sdot { animation: sx-pulse 1s infinite; }
.sx-s-info { border-top-color: var(--info); } .sx-s-info .sx-state, .sx-s-info .sx-ico { color: var(--info); }
.sx-s-off { border-top-color: var(--off); } .sx-s-off .sx-state, .sx-s-off .sx-ico { color: var(--off); }
.sx-bar { position: relative; height: 8px; border-radius: 99px; background: var(--card2); overflow: hidden; }
.sx-bar-fill { height: 100%; border-radius: 99px; background: currentColor; transition: width .4s; }
.sx-s-ok .sx-bar, .sx-s-warn .sx-bar { color: inherit; }
.sx-s-ok .sx-bar-fill { background: var(--ok); } .sx-s-warn .sx-bar-fill { background: var(--warn); }
.sx-s-off .sx-bar-fill { background: var(--off); }
.sx-bar-mark { position: absolute; left: 50%; top: 0; bottom: 0; width: 2px; background: var(--muted); }

.sx-card-row { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.sx-xyz { display: flex; gap: 10px; font-size: 12.5px; color: var(--muted); font-variant-numeric: tabular-nums; }
.sx-xyz span { background: var(--card2); padding: 3px 8px; border-radius: 8px; }
.sx-chart { width: 100%; height: 160px; display: block; }
.sx-line { fill: none; stroke: #60a5fa; stroke-width: 2; vector-effect: non-scaling-stroke; }
.sx-area { fill: rgba(96,165,250,.12); stroke: none; }
.sx-thr { stroke: var(--warn); stroke-width: 1.5; stroke-dasharray: 6 5; vector-effect: non-scaling-stroke; }
.sx-legend { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 10px; color: var(--muted); font-size: 12.5px; }
.sx-lg { display: inline-flex; align-items: center; gap: 6px; }
.sx-lg-line { width: 16px; height: 3px; background: #60a5fa; border-radius: 2px; display: inline-block; }
.sx-lg-thr { width: 16px; border-top: 2px dashed var(--warn); display: inline-block; }

.sx-link { display: inline-flex; align-items: center; gap: 4px; background: none; border: 1px solid var(--line); color: var(--muted);
  border-radius: 10px; padding: 5px 10px; font-size: 13px; cursor: pointer; }
.sx-link:hover { color: var(--text); }
.sx-empty { color: var(--muted); font-size: 14px; padding: 24px 0; text-align: center; }
.sx-feed { list-style: none; margin: 0; padding: 0; max-height: 260px; overflow-y: auto; }
.sx-feed li { display: flex; align-items: center; gap: 10px; padding: 8px 2px; border-bottom: 1px solid var(--line); }
.sx-feed li:last-child { border-bottom: none; }
.sx-fico { width: 28px; height: 28px; border-radius: 8px; display: grid; place-items: center; flex: none; background: var(--card2); color: var(--muted); }
.sx-e-pir, .sx-e-vib { color: var(--warn); background: rgba(245,158,11,.14); }
.sx-e-puerta { color: var(--alert); background: rgba(239,68,68,.14); }
.sx-e-puerta-ok, .sx-e-red, .sx-e-cmd-ok { color: var(--ok); background: rgba(34,197,94,.14); }
.sx-e-red-off { color: var(--off); }
.sx-e-alarma, .sx-e-sirena { color: var(--alert); background: rgba(239,68,68,.14); }
.sx-e-estado, .sx-e-cerradura { color: var(--info); background: rgba(56,189,248,.14); }
.sx-e-cmd { color: #60a5fa; background: rgba(96,165,250,.14); }
.sx-ftext { flex: 1; font-size: 14px; }
.sx-ftime { color: var(--muted); font-size: 12.5px; font-variant-numeric: tabular-nums; }
.sx-foot { color: var(--muted); font-size: 12px; margin-top: 10px; }

@keyframes sx-pulse { 0%, 100% { opacity: 1; } 50% { opacity: .35; } }
@keyframes sx-glow-r { 0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,.55); } 50% { box-shadow: 0 0 0 12px rgba(239,68,68,0); } }
@keyframes sx-glow { 0%, 100% { box-shadow: 0 0 0 0 rgba(245,158,11,.45); } 50% { box-shadow: 0 0 0 10px rgba(245,158,11,0); } }
@media (max-width: 600px) {
  .sx-title { font-size: 22px; }
  .sx-hero { padding: 16px; gap: 12px; }
  .sx-hero-icon { width: 52px; height: 52px; border-radius: 14px; }
  .sx-hero-title { font-size: 20px; }
  .sx-actions { align-items: stretch; width: 100%; }
  .sx-btns { width: 100%; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .sx-btn { justify-content: center; padding: 10px 6px; font-size: 13px; min-width: 0; }
  .sx-grid2 { grid-template-columns: minmax(0, 1fr); }
}
</style>
