// Configuración de Node-RED del proyecto.
// Arrancar desde esta carpeta con:  npx node-red -u . -s settings.js
module.exports = {
    uiHost: "127.0.0.1",      // solo accesible desde esta laptop
    uiPort: 1880,
    flowFile: "flows.json",
    flowFilePretty: true,
    credentialSecret: false,
    logging: {
        console: { level: "info", metrics: false, audit: false }
    },
    editorTheme: {
        projects: { enabled: false },
        tours: false
    }
};
