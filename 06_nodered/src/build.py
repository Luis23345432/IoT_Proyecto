import json, sys, pathlib

here = pathlib.Path(__file__).parent
modelo = (here / "modelo.js").read_text()
vista = (here / "vista.vue").read_text()

T = "tab_nodo1"
flows = [
    {"id": T, "type": "tab", "label": "Nodo 1", "disabled": False,
     "info": "Tablero del sistema de seguridad.\nSensores: iot/seguridad/sensores\nComandos: casa/nodo1/cmd"},
    {"id": "broker1", "type": "mqtt-broker", "name": "HiveMQ público (pruebas)", "broker": "broker.hivemq.com",
     "port": "1883", "clientid": "", "autoConnect": True, "usetls": False, "protocolVersion": "4",
     "keepalive": "60", "cleansession": True, "autoUnsubscribe": True,
     "birthTopic": "", "birthQos": "0", "birthPayload": "", "closeTopic": "", "closeQos": "0", "closePayload": "",
     "willTopic": "", "willQos": "0", "willPayload": ""},
    {"id": "ui_base1", "type": "ui-base", "name": "Seguridad residencial", "path": "/dashboard",
     "includeClientData": True, "acceptsClientConfig": ["ui-notification", "ui-control"],
     "showPathInSidebar": False, "showPageTitle": False, "navigationStyle": "none", "titleBarStyle": "hidden"},
    {"id": "ui_theme1", "type": "ui-theme", "name": "Oscuro",
     "colors": {"surface": "#0b1220", "primary": "#2563eb", "bgPage": "#0b1220",
                "groupBg": "#0b1220", "groupOutline": "#0b1220"},
     "sizes": {"density": "default", "pagePadding": "20px", "groupGap": "0px",
               "groupBorderRadius": "0px", "widgetGap": "0px"}},
    {"id": "ui_page1", "type": "ui-page", "name": "Puerta principal", "ui": "ui_base1", "path": "/nodo1",
     "icon": "shield-home", "layout": "notebook", "theme": "ui_theme1",
     "breakpoints": [{"name": "Default", "px": "0", "cols": "12"}],
     "order": 1, "className": "", "visible": "true", "disabled": "false"},
    {"id": "g_main", "type": "ui-group", "name": "Principal", "page": "ui_page1", "width": "12", "height": "1",
     "order": 1, "showTitle": False, "className": "", "visible": "true", "disabled": "false", "groupType": "default"},

    {"id": "in_sensores", "type": "mqtt in", "z": T, "name": "iot/seguridad/sensores",
     "topic": "iot/seguridad/sensores", "qos": "0", "datatype": "json", "broker": "broker1",
     "nl": False, "rap": True, "rh": 0, "inputs": 0, "x": 160, "y": 80, "wires": [["fn_modelo", "dbg_sensores"]]},
    {"id": "in_estado", "type": "mqtt in", "z": T, "name": "casa/nodo1/estado", "topic": "casa/nodo1/estado",
     "qos": "0", "datatype": "json", "broker": "broker1", "nl": False, "rap": True, "rh": 0, "inputs": 0,
     "x": 150, "y": 140, "wires": [["fn_modelo"]]},
    {"id": "in_evento", "type": "mqtt in", "z": T, "name": "casa/nodo1/evento", "topic": "casa/nodo1/evento",
     "qos": "1", "datatype": "json", "broker": "broker1", "nl": False, "rap": True, "rh": 0, "inputs": 0,
     "x": 150, "y": 200, "wires": [["fn_modelo"]]},
    {"id": "inj_tick", "type": "inject", "z": T, "name": "cada 2 s", "props": [{"p": "topic", "vt": "str"}],
     "repeat": "2", "crontab": "", "once": True, "onceDelay": "1", "topic": "tick",
     "x": 130, "y": 260, "wires": [["fn_modelo"]]},
    {"id": "fn_modelo", "type": "function", "z": T, "name": "modelo del tablero", "func": modelo,
     "outputs": 2, "timeout": 0, "noerr": 0, "initialize": "", "finalize": "", "libs": [],
     "outputLabels": ["foto para la vista", "comando MQTT"],
     "x": 420, "y": 170, "wires": [["ui_vista"], ["out_cmd"]]},
    {"id": "ui_vista", "type": "ui-template", "z": T, "group": "g_main", "page": "", "ui": "",
     "name": "Vista principal", "order": 1, "width": "0", "height": "0", "head": "", "format": vista,
     "storeOutMessages": True, "passthru": False, "resendOnRefresh": True, "templateScope": "local",
     "className": "", "x": 650, "y": 140, "wires": [["fn_modelo"]]},
    {"id": "out_cmd", "type": "mqtt out", "z": T, "name": "casa/nodo1/cmd", "topic": "casa/nodo1/cmd",
     "qos": "1", "retain": "false", "respTopic": "", "contentType": "", "userProps": "", "correl": "",
     "expiry": "", "broker": "broker1", "x": 660, "y": 220, "wires": []},
    {"id": "dbg_sensores", "type": "debug", "z": T, "name": "sensores (apagado)", "active": False,
     "tosidebar": True, "console": False, "tostatus": False, "complete": "payload", "targetType": "msg",
     "statusVal": "", "statusType": "auto", "x": 430, "y": 60, "wires": []},
]
json.dump(flows, open(sys.argv[1], "w"), ensure_ascii=False, indent=4)
print("nodos:", len(flows))
