// Build estático para Vercel: copia la UI y señala el backend de Render.
const fs = require("node:fs");
const path = require("node:path");
const destino = path.join(__dirname, "dist");
const backend = process.env.RENDER_BACKEND_URL;
if (!backend || !/^https:\/\/[^/]+\/?$/.test(backend)) {
  console.error("Configura RENDER_BACKEND_URL con la URL HTTPS del servicio Render.");
  process.exit(1);
}
fs.mkdirSync(destino, {recursive:true});
fs.cpSync(path.join(__dirname,"web"),path.join(destino,"web"),{recursive:true});
fs.cpSync(path.join(__dirname,"assets"),path.join(destino,"assets"),{recursive:true});
fs.copyFileSync(path.join(__dirname,"web","index.html"),path.join(destino,"index.html"));
fs.writeFileSync(path.join(destino,"config.js"),`window.UMA_BACKEND_URL = ${JSON.stringify(backend.replace(/\/$/,""))};\n`);
console.log("Frontend preparado para Render:",backend);
