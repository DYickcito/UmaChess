// La carpeta frontend/ no contiene Python: Vercel la construye como sitio estático.
const fs = require("node:fs");
const path = require("node:path");
const backend = process.env.RENDER_BACKEND_URL;
if (!backend || !/^https:\/\/[^/]+\/?$/.test(backend)) {
  console.error("Configura RENDER_BACKEND_URL con la URL HTTPS de Render.");
  process.exit(1);
}
const dist = path.join(__dirname, "dist");
fs.mkdirSync(dist, {recursive:true});
fs.cpSync(path.join(__dirname,"web"),path.join(dist,"web"),{recursive:true});
fs.cpSync(path.join(__dirname,"assets"),path.join(dist,"assets"),{recursive:true});
fs.copyFileSync(path.join(__dirname,"index.html"),path.join(dist,"index.html"));
fs.writeFileSync(path.join(dist,"config.js"),`window.UMA_BACKEND_URL = ${JSON.stringify(backend.replace(/\/$/,""))};\n`);
console.log("Frontend estático preparado para:", backend);
