// Modelo del tablero: junta todo lo que llega y arma una "foto" del sistema
// que la vista solo tiene que dibujar (así no se pierde nada al recargar).
const UMBRAL_VIB = 40;   // mismo valor que ETA en el firmware
const MAX_EVENTOS = 40;
const MAX_SERIE = 240;   // 60 s a 4 fotos por segundo
const MAX_LAT = 40;      // latencias para la mediana

const ahora = Date.now();
let m = flow.get('modelo') || {};
m = Object.assign({
    sensores: null, ultimo: 0, online: false, modo: null, salida: 0,
    sirena: false, cerradura: false, base: null, vib: 0, vibActiva: false, umbral: UMBRAL_VIB,
    cont: { pir: 0, puerta: 0, vib: 0 }, desde: ahora, eventos: [], serie: [], lats: [], lat: null
}, m);

function evento(tipo, texto) {
    m.eventos.unshift({ t: ahora, tipo, texto });
    m.eventos.splice(MAX_EVENTOS);
}

const NOMBRE = { desarmado: 'desarmado', saliendo: 'armándose', armado: 'armado', sospecha: 'en sospecha', alarma: 'en alarma' };
let cmd = null;

switch (msg.topic) {
case 'iot/seguridad/sensores': {
    const s = msg.payload;
    if (!s || typeof s !== 'object') return null;
    const prev = m.sensores;

    // Vibración: la detecta el nodo a 200 Hz; si no la manda, se estima aquí
    let vib, d;
    if (s.vib !== undefined) {
        vib = !!s.vib;
        d = s.d || 0;
    } else {
        if (!m.base) m.base = { x: s.x, y: s.y, z: s.z };
        d = Math.sqrt((s.x - m.base.x) ** 2 + (s.y - m.base.y) ** 2 + (s.z - m.base.z) ** 2);
        vib = d > UMBRAL_VIB;
        const k = vib ? 0.02 : 0.1;
        for (const e of ['x', 'y', 'z']) m.base[e] += k * (s[e] - m.base[e]);
    }
    if (vib && !m.vibActiva) { m.cont.vib++; evento('vib', 'Golpe o vibración en la puerta'); }
    m.vibActiva = vib;
    m.vib = Math.round(d);

    if (prev) {
        if (s.pir && !prev.pir && !s.pir_calibrando) { m.cont.pir++; evento('pir', 'Movimiento detectado'); }
        if (s.puerta_abierta !== prev.puerta_abierta) {
            if (s.puerta_abierta) { m.cont.puerta++; evento('puerta', 'Puerta abierta'); }
            else evento('puerta-ok', 'Puerta cerrada');
        }
        if (s.estado && s.estado !== prev.estado) {
            if (s.estado === 'alarma') evento('alarma', '¡Alarma! Dos sensores distintos en 10 s');
            else evento('estado', 'Sistema ' + (NOMBRE[s.estado] || s.estado));
        }
        if (s.sirena !== undefined && !!s.sirena !== !!prev.sirena) evento('sirena', s.sirena ? 'Sirena encendida' : 'Sirena apagada');
        if (s.cerradura !== undefined && !!s.cerradura !== !!prev.cerradura) evento('cerradura', s.cerradura ? 'Cerradura bloqueada' : 'Cerradura liberada');
    }

    // Latencia extremo a extremo: hora del nodo (NTP) contra hora de llegada
    if (s.t > 1700000000000) {
        m.lats.push(ahora - s.t);
        m.lats.splice(0, Math.max(0, m.lats.length - MAX_LAT));
        const o = m.lats.slice().sort((a, b) => a - b);
        m.lat = o[Math.floor(o.length / 2)];
    }

    if (!m.online) evento('red', 'Nodo conectado');
    m.online = true;
    m.sensores = s;
    m.ultimo = ahora;
    m.modo = s.estado || m.modo;
    m.salida = s.salida_s || 0;
    m.sirena = !!s.sirena;
    m.cerradura = !!s.cerradura;
    m.serie.push({ t: ahora, d: m.vib });
    m.serie.splice(0, Math.max(0, m.serie.length - MAX_SERIE));
    break;
}
case 'casa/nodo1/evento':
    if (msg.payload && msg.payload.ack) evento('cmd-ok', 'El nodo confirmó: ' + msg.payload.ack);
    else return null;
    break;
case 'tick':
    // Sin lecturas por más de 5 s: el nodo se considera desconectado
    if (m.online && ahora - m.ultimo > 5000) {
        m.online = false;
        evento('red-off', 'Sin datos del nodo');
        break;
    }
    flow.set('modelo', m);
    return null;
case 'ui/cmd':
    cmd = { topic: 'casa/nodo1/cmd', payload: msg.payload };
    evento('cmd', 'Comando enviado: ' + msg.payload);
    break;
case 'ui/reset':
    m.cont = { pir: 0, puerta: 0, vib: 0 };
    m.desde = ahora;
    m.eventos = [];
    m.base = null;
    m.lats = [];
    m.lat = null;
    break;
default:
    return null;
}

flow.set('modelo', m);
const foto = Object.assign({}, m, { ahora });
delete foto.lats;
delete foto.base;
return [{ payload: foto }, cmd];
