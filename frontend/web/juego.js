"use strict";
const $ = (id) => document.getElementById(id);
const nombres = {p:"special_week",r:"silent_suzuka",n:"tokai_teio",b:"haru_urara",q:"oguri_cap",k:"agnes_tachyon"};
const etiquetas = {q:"Dama",r:"Torre",b:"Alfil",n:"Caballo"};
const codigo = new URLSearchParams(location.search).get("sala");
const backend = (window.UMA_BACKEND_URL || location.origin).replace(/\/$/, "");
let lado = "espectador", estado = null, socket = null, seleccion = null, opcionesPromo = null;
const nombrePieza = (pieza) => nombres[pieza.toLowerCase()];
const colorPieza = (pieza) => pieza === pieza.toUpperCase() ? "blanca" : "negra";
const imagenPieza = (pieza) => `/assets/piezas/${nombrePieza(pieza)}_${colorPieza(pieza)}.png`;
const aviso = (texto) => { $("mensaje").textContent = texto; };
const enviar = (tipo, extra={}) => {
  if(socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({tipo,...extra}));
  else aviso("Sin conexión. Espera a la reconexión.");
};

function piezasDeFen(fen) {
  const piezas = {};
  fen.split(" ")[0].split("/").forEach((fila, y) => {
    let x=0;
    for (const c of fila) {
      if (/\d/.test(c)) x+=Number(c);
      else piezas["abcdefgh"[x++]+(8-y)] = c;
    }
  });
  return piezas;
}

function dibujar() {
  if(!estado) return;
  const piezas = piezasDeFen(estado.fen), destino = $("tablero");
  destino.replaceChildren();
  const blancasAbajo = lado !== "negras";
  const archivos = blancasAbajo ? "abcdefgh" : "hgfedcba";
  const rangos = blancasAbajo ? "87654321" : "12345678";
  for(let y=0;y<8;y++) for(let x=0;x<8;x++) {
    const casilla=archivos[x]+rangos[y], pieza=piezas[casilla];
    const boton=document.createElement("button");
    boton.type="button";
    boton.className=`casilla ${(x+y)%2 ? "oscura" : "clara"}`;
    boton.setAttribute("aria-label", `${casilla}${pieza ? ": "+nombrePieza(pieza)+" "+colorPieza(pieza) : ""}`);
    if(estado.ultima && [estado.ultima.slice(0,2),estado.ultima.slice(2,4)].includes(casilla)) boton.classList.add("ultima");
    if(seleccion===casilla) boton.classList.add("seleccionada");
    if(seleccion && estado.legales.some(m=>m.slice(0,2)===seleccion && m.slice(2,4)===casilla)) boton.classList.add("posible");
    if(pieza){const img=document.createElement("img");img.src=imagenPieza(pieza);img.alt="";boton.append(img);}
    boton.addEventListener("click",()=>pulsar(casilla,piezas));
    destino.append(boton);
  }
  $("lado").textContent=`Juegas con: ${lado}`;
  $("estado").textContent=estado.fin ? `Resultado: ${estado.fin.resultado} (${estado.fin.motivo})` :
    `Turno: ${estado.turno}${estado.jaque ? " · ¡Jaque!" : ""}`;
  $("jugadores").textContent=`Blancas: ${estado.conectados.blancas ? "conectadas" : "desconectadas"} · Negras: ${estado.conectados.negras ? "conectadas" : "desconectadas"}`;
  const historial=$("historial");
  historial.replaceChildren();
  for(let i=0;i<estado.historial.length;i+=2){
    const linea=document.createElement("div");
    linea.textContent=`${i/2+1}. ${estado.historial[i]}   ${estado.historial[i+1] || ""}`;
    historial.append(linea);
  }
  historial.scrollTop=historial.scrollHeight;
  const jugando=lado!=="espectador" && !estado.fin;
  $("rendirse").disabled=!jugando;
  $("tablas").disabled=!jugando;
  $("revancha").classList.toggle("oculto",!estado.fin || lado==="espectador");
  $("revancha").disabled=estado.revancha.includes(lado);
  $("revancha").textContent=estado.revancha.includes(lado) ? "Esperando rival…" : "Pedir revancha";
}

function pulsar(casilla,piezas) {
  if(!estado || estado.fin || lado!==estado.turno || opcionesPromo) return;
  const pieza=piezas[casilla];
  if(pieza && colorPieza(pieza) === (lado==="blancas" ? "blanca" : "negra")) {
    seleccion=casilla===seleccion ? null : casilla;dibujar();return;
  }
  if(!seleccion) return;
  const candidatas=estado.legales.filter(m=>m.slice(0,2)===seleccion && m.slice(2,4)===casilla);
  if(candidatas.length===1){enviar("mover",{uci:candidatas[0]});seleccion=null;dibujar();}
  else if(candidatas.length>1) mostrarCoronacion(candidatas);
  else aviso("Movimiento ilegal. Elige una casilla marcada.");
}

function mostrarCoronacion(jugadas) {
  opcionesPromo=jugadas;
  const contenedor=$("opciones");contenedor.replaceChildren();
  for(const tipo of ["q","r","b","n"]){
    const boton=document.createElement("button"), img=document.createElement("img");
    img.src=`/assets/piezas/${nombres[tipo]}_${lado==="blancas" ? "blanca" : "negra"}.png`;
    img.alt="";boton.append(img,document.createTextNode(etiquetas[tipo]));
    boton.addEventListener("click",()=>{enviar("mover",{uci:jugadas.find(m=>m.endsWith(tipo))});cerrarModal();seleccion=null;dibujar();});
    contenedor.append(boton);
  }
  $("modal").classList.remove("oculto");
}
function cerrarModal(){opcionesPromo=null;$("modal").classList.add("oculto");}

function conectar() {
  const clave=sessionStorage.getItem("uma-"+codigo) || "";
  const destino=new URL(backend);
  const protocolo=destino.protocol==="https:" ? "wss:" : "ws:";
  socket=new WebSocket(`${protocolo}//${destino.host}/ws/${codigo}?clave=${encodeURIComponent(clave)}`);
  socket.onopen=()=>aviso("Conectado. ¡Buena partida!");
  socket.onmessage=(evento)=>{
    const datos=JSON.parse(evento.data);
    if(datos.tipo==="bienvenida"){
      lado=datos.lado;
      if(datos.clave) sessionStorage.setItem("uma-"+codigo,datos.clave);
    }else if(datos.tipo==="estado"){
      estado=datos;seleccion=null;cerrarModal();dibujar();
    }else if(datos.tipo==="error") aviso(datos.mensaje);
  };
  socket.onclose=()=>{aviso("Conexión perdida. Intentando reconectar…");setTimeout(conectar,2500);};
  socket.onerror=()=>aviso("Error de conexión.");
}

$("crear").addEventListener("click",async()=>{
  $("crear").disabled=true;
  try{
    const respuesta=await fetch(`${backend}/api/salas`,{method:"POST"});
    if(!respuesta.ok) throw Error("No se pudo crear la sala.");
    const sala=await respuesta.json();
    sessionStorage.setItem("uma-"+sala.sala,sala.clave);
    location.href=`/?sala=${sala.sala}`;
  }catch(error){$("inicio-error").textContent=error.message;$("crear").disabled=false;}
});
$("copiar").addEventListener("click",async()=>{
  try{await navigator.clipboard.writeText($("enlace").value);aviso("Enlace copiado.");}
  catch{ $("enlace").select();aviso("Copia el enlace seleccionado."); }
});
$("cancelar").addEventListener("click",cerrarModal);
$("rendirse").addEventListener("click",()=>{if(confirm("¿Seguro que deseas rendirte?")) enviar("rendirse");});
$("tablas").addEventListener("click",()=>enviar("tablas"));
$("revancha").addEventListener("click",()=>enviar("revancha"));
if(codigo && /^[0-9a-f]{8}$/.test(codigo)){
  $("inicio").classList.add("oculto");$("partida").classList.remove("oculto");
  $("sala-titulo").textContent=`Sala ${codigo}`;
  $("enlace").value=`${location.origin}/?sala=${codigo}`;
  conectar();
}
