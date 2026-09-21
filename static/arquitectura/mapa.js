/* Mapa de arquitectura de SISOC — script generado, no editar la copia de static/.
   Fuente: scripts/arquitectura/plantilla/mapa.js

   Espera un contenedor con id="mapa". El grafo llega por window.__GRAFO_SISOC__
   (documento autocontenido) o por fetch de la URL en data-grafo (vista Django). */

(() => {
  "use strict";

  const raiz = document.getElementById("mapa");
  if (!raiz) return;

  const CAPAS = {
    api: { etiqueta: "Contrato público", hue: "var(--api)", punteado: false },
    internal: { etiqueta: "Import de internals", hue: "var(--deuda)", punteado: false },
    movil: { etiqueta: "Plano móvil", hue: "var(--movil)", punteado: false },
    s2s: { etiqueta: "Server-to-server", hue: "var(--s2s)", punteado: false },
    externo: { etiqueta: "Salidas", hue: "var(--neutro)", punteado: true }
  };

  const PLANOS_API = { token: "token DRF", api_key: "API key", sesion: "sesión" };

  const ARMAZON = `
    <header class="barra">
      <div class="marca">
        <h1>Arquitectura de SISOC</h1>
        <button class="ayuda-btn" id="mp-ayuda" type="button" aria-expanded="false" aria-controls="mp-ficha" title="Detalles de esta generación">?</button>
      </div>
      <label class="buscador">
        <span class="lupa" aria-hidden="true">/</span>
        <input id="mp-busqueda" type="search" placeholder="Buscar módulo o pantalla" autocomplete="off" aria-label="Buscar módulo o pantalla">
      </label>
      <div class="capas" id="mp-capas" role="group" aria-label="Capas de relación"></div>
      <div class="ficha" id="mp-ficha" hidden></div>
    </header>

    <div class="cuerpo">
      <main class="lienzo" id="mp-lienzo">
       <div class="lienzo-contenido" id="mp-contenido">
        <svg class="cables" id="mp-cables" aria-hidden="true"></svg>
        <section class="marco">
          <header>
            <h2>SISOC · monolito Django</h2>
            <p id="mp-marco-sub"></p>
          </header>
          <div class="zonas" id="mp-zonas"></div>
        </section>
        <div class="rails">
          <section class="rail">
            <header><h2>PWA · plano móvil</h2><p>Repos privados, auth por token.</p></header>
            <div class="rejilla" id="mp-pwas"></div>
            <p class="nota" id="mp-pwa-nota"></p>
          </section>
          <section class="rail">
            <header><h2>Sistemas externos</h2><p>Entradas por API key y salidas.</p></header>
            <div class="rejilla" id="mp-externos"></div>
          </section>
          <section class="rail">
            <header><h2>Ejecución diferida</h2><p>Un rol por contenedor.</p></header>
            <ul class="async" id="mp-async"></ul>
            <p class="nota">El resto de la asincronía son hilos dentro del proceso web.</p>
          </section>
        </div>
       </div>
      </main>

      <aside class="panel">
        <nav class="pestanias" role="tablist">
          <button class="pestania" id="mp-tab-detalle" type="button" role="tab" aria-selected="true" aria-controls="mp-hoja-detalle">Detalle</button>
          <span class="anuncio" id="mp-anuncio" role="status" aria-live="polite"></span>
          <button class="pestania" id="mp-tab-menu" type="button" role="tab" aria-selected="false" aria-controls="mp-hoja-menu">Menú del usuario</button>
        </nav>
        <div class="hoja" id="mp-hoja-detalle" role="tabpanel" aria-labelledby="mp-tab-detalle" tabindex="0"></div>
        <div class="hoja" id="mp-hoja-menu" role="tabpanel" aria-labelledby="mp-tab-menu" tabindex="0" hidden></div>
      </aside>
    </div>`;

  const $ = id => document.getElementById(id);
  const el = (tag, cls, texto) => {
    const nodo = document.createElement(tag);
    if (cls) nodo.className = cls;
    if (texto != null) nodo.textContent = texto;
    return nodo;
  };
  const miles = n => (n ?? 0).toLocaleString("es-AR");

  function sinDatos(motivo) {
    raiz.classList.add("mapa-app");
    const caja = el("div", "vacio");
    caja.append(el("h2", null, "El mapa todavía no fue generado"));
    const p = el("p");
    p.append(document.createTextNode("Falta el grafo de arquitectura. Se genera con "));
    p.append(el("code", null, "python manage.py generar_mapa_arquitectura"));
    p.append(document.createTextNode(", que corre en cada arranque del contenedor."));
    caja.append(p);
    if (motivo) caja.append(el("p", "pista", motivo));
    raiz.replaceChildren(caja);
  }

  /* ------------------------------------------------------------------ */

  function arrancar(G) {
    raiz.classList.add("mapa-app");
    raiz.innerHTML = ARMAZON;

    const modulos = new Map(G.modulos.map(m => [m.id, m]));
    const activas = new Set(["api", "movil", "s2s", "externo"]);
    let seleccion = null;
    let resaltado = null;
    let cache = null;
    const ocultos = new Set();

    /* ---------- aristas ---------- */

    const aristas = [];

    for (const a of G.aristas) {
      aristas.push({ desde: "mod:" + a.src, hasta: "mod:" + a.dst, capa: a.kind, n: a.n, ejemplos: a.ejemplos || [] });
    }

    for (const p of G.pwas) {
      for (const c of p.consume) {
        aristas.push({
          desde: "pwa:" + p.id,
          hasta: "mod:" + c.modulo,
          capa: "movil",
          n: 1,
          ejemplos: [c.evidencia],
          certeza: c.certeza,
          punteado: c.certeza === "inferido"
        });
      }
    }

    for (const x of G.externos) {
      const capa = x.plano === "api_key" ? "s2s" : "externo";
      const entrante = x.direccion === "entrada" || x.direccion === "bidireccional";
      for (const m of x.modulos) {
        aristas.push({
          desde: entrante ? "ext:" + x.id : "mod:" + m,
          hasta: entrante ? "mod:" + m : "ext:" + x.id,
          capa,
          n: 1,
          ejemplos: [x.evidencia],
          doble: x.direccion === "bidireccional",
          punteado: x.direccion === "manual" || capa === "externo"
        });
      }
    }

    const porNodo = new Map();
    for (const a of aristas) {
      for (const punta of [a.desde, a.hasta]) {
        if (!porNodo.has(punta)) porNodo.set(punta, []);
        porNodo.get(punta).push(a);
      }
    }

    if (raiz.dataset.volver) {
      const volver = document.createElement("a");
      volver.className = "volver";
      volver.href = raiz.dataset.volver;
      volver.textContent = "← Novedades";
      raiz.querySelector(".barra").append(volver);
    }

    const t = G.totales;
    $("mp-marco-sub").textContent = `${t.apps} apps · ${miles(t.lineas)} líneas · una base MySQL`;

    /* ---------- ficha del (?) ---------- */

    const ficha = $("mp-ficha");
    ficha.append(el("h2", null, "Esta generación"));
    const dl = el("dl");
    const filas = [
      ["generado", (G.generado || "").slice(0, 16).replace("T", " ")],
      ["commit", G.commit || "—"],
      ["rama", G.rama || "—"],
      ["apps", miles(t.apps)],
      ["líneas de Python", miles(t.lineas)],
      ["dependencias", `${t.aristas} (${t.aristas_api} por fachada, ${t.aristas_internals} por internals)`],
      ["entradas de menú", miles(t.items_menu)]
    ];
    for (const [k, v] of filas) dl.append(el("dt", null, k), el("dd", null, v));
    ficha.append(dl);
    ficha.append(el("h2", null, "De dónde sale"));
    const origen = el("p");
    origen.append(document.createTextNode("Se extrae del repositorio en cada arranque: apps instaladas, rutas montadas, autenticación de cada API, imports reales entre apps y el árbol del menú lateral con sus permisos. Líneas y dependencias excluyen migraciones, tests y templates."));
    ficha.append(origen);
    const aviso = el("p");
    aviso.append(document.createTextNode("Las flechas son imports directos. El acoplamiento por signals y registries no aparece como flecha."));
    ficha.append(aviso);

    const btnAyuda = $("mp-ayuda");
    const alternarFicha = abrir => {
      ficha.hidden = !abrir;
      btnAyuda.setAttribute("aria-expanded", String(abrir));
    };
    btnAyuda.addEventListener("click", () => alternarFicha(ficha.hidden));
    document.addEventListener("click", ev => {
      if (!ficha.hidden && !ficha.contains(ev.target) && ev.target !== btnAyuda) alternarFicha(false);
    });

    /* ---------- capas ---------- */

    const cuentas = {};
    for (const a of aristas) cuentas[a.capa] = (cuentas[a.capa] || 0) + 1;

    for (const [id, def] of Object.entries(CAPAS)) {
      const boton = el("button", "capa");
      boton.type = "button";
      boton.style.setProperty("--hue", def.hue);
      if (def.punteado) boton.dataset.punteado = "1";
      boton.setAttribute("aria-pressed", String(activas.has(id)));
      boton.title = {
        api: "Un dominio consume otro por su fachada pública <app>/api.py",
        internal: "Un dominio importa models, services o views de otro. Es la deuda que corta el ratchet de .importlinter",
        movil: "Las PWA entran por APIs con token DRF",
        s2s: "Sistemas externos entran por APIs con API key",
        externo: "Servicios que SISOC consume hacia afuera"
      }[id];
      boton.append(el("span", "trazo"), el("span", "etq", def.etiqueta), el("span", "cuenta", String(cuentas[id] || 0)));
      boton.addEventListener("click", () => {
        activas.has(id) ? activas.delete(id) : activas.add(id);
        boton.setAttribute("aria-pressed", String(activas.has(id)));
        dibujar();
        if (seleccion) panel();
      });
      $("mp-capas").append(boton);
    }

    /* ---------- nodos ---------- */

    function insignia(texto, hue, titulo) {
      const s = el("span", "insignia", texto);
      s.style.setProperty("--hue", hue);
      if (titulo) s.title = titulo;
      return s;
    }

    function cablear(boton, id) {
      boton.dataset.nodo = id;
      boton.type = "button";
      boton.setAttribute("aria-pressed", "false");
      boton.addEventListener("click", () => seleccionar(seleccion === id ? null : id));
      boton.addEventListener("pointerenter", () => resaltar(id));
      boton.addEventListener("pointerleave", () => resaltar(null));
      boton.addEventListener("focus", () => resaltar(id));
      boton.addEventListener("blur", () => resaltar(null));
      return boton;
    }

    const maxLineas = Math.max(...G.modulos.map(m => m.lineas), 1);

    for (const zona of G.zonas) {
      const apps = G.modulos.filter(m => m.zona === zona.id);
      if (!apps.length) continue;

      const fila = el("div", "zona");
      const info = el("div");
      info.append(el("p", "zona-nombre", zona.nombre), el("p", "zona-detalle", zona.detalle));
      const rejilla = el("div", "rejilla");

      for (const m of apps.slice().sort((a, b) => b.lineas - a.lineas)) {
        const b = cablear(el("button", "nodo"), "mod:" + m.id);
        b.append(el("span", "titulo", m.nombre), el("span", "paquete", m.id));
        const ins = el("span", "insignias");
        if (m.tiene_fachada) ins.append(insignia("api", "var(--api)", "Expone fachada pública en " + m.id + "/api.py"));
        if (m.planos_api.includes("token")) ins.append(insignia("token", "var(--movil)", "API con token DRF (plano móvil)"));
        if (m.planos_api.includes("api_key")) ins.append(insignia("key", "var(--s2s)", "API con API key (server-to-server)"));
        if (m.menu.length) ins.append(insignia("menú " + m.menu.length, "var(--neutro)", m.menu.length + " entradas en el menú lateral"));
        if (!m.instalada) ins.append(insignia("no instalada", "var(--alerta)", "Paquete del runtime fuera de INSTALLED_APPS"));
        if (ins.childElementCount) b.append(ins);
        const barra = el("span", "barrita");
        const relleno = el("span");
        relleno.style.width = Math.max(2, Math.round((m.lineas / maxLineas) * 100)) + "%";
        barra.title = miles(m.lineas) + " líneas";
        barra.append(relleno);
        b.append(barra);
        rejilla.append(b);
      }

      fila.append(info, rejilla);
      $("mp-zonas").append(fila);
    }

    const nombrePwa = p => p.repository.split("/").pop().replace(/-/g, " ");

    for (const p of G.pwas) {
      const b = cablear(el("button", "nodo"), "pwa:" + p.id);
      b.append(el("span", "titulo", nombrePwa(p)), el("span", "paquete", p.canonical_path));
      const ins = el("span", "insignias");
      ins.append(insignia(p.enabled ? "activa" : "apagada", p.enabled ? "var(--movil)" : "var(--alerta)"));
      if (!p.consume.length) ins.append(insignia("sin contrato", "var(--alerta)", "Ningún namespace de API declarado para esta PWA"));
      b.append(ins);
      $("mp-pwas").append(b);
    }

    const sinContrato = G.pwas.filter(p => !p.consume.length);
    $("mp-pwa-nota").textContent = sinContrato.length
      ? `Sin contrato declarado: ${sinContrato.map(p => p.id).join(", ")}.`
      : "Las tres tienen su consumo de API declarado.";

    for (const x of G.externos) {
      const b = cablear(el("button", "nodo"), "ext:" + x.id);
      b.append(el("span", "titulo", x.nombre));
      const ins = el("span", "insignias");
      const hue = x.plano === "api_key" ? "var(--s2s)" : "var(--neutro)";
      ins.append(insignia(x.direccion, hue));
      b.append(ins);
      $("mp-externos").append(b);
    }

    for (const rol of G.asincronia.roles_contenedor) $("mp-async").append(el("li", null, rol));
    for (const s of G.asincronia.servicios_celery) $("mp-async").append(el("li", "celery", s));

    /* ---------- cables ---------- */

    const svg = $("mp-cables");
    const NS = "http://www.w3.org/2000/svg";

    function defs() {
      const d = document.createElementNS(NS, "defs");
      for (const [id, def] of Object.entries(CAPAS)) {
        const marker = document.createElementNS(NS, "marker");
        marker.setAttribute("id", "mp-punta-" + id);
        marker.setAttribute("viewBox", "0 0 8 8");
        marker.setAttribute("refX", "7");
        marker.setAttribute("refY", "4");
        marker.setAttribute("markerWidth", "5.5");
        marker.setAttribute("markerHeight", "5.5");
        marker.setAttribute("orient", "auto-start-reverse");
        const poly = document.createElementNS(NS, "polygon");
        poly.setAttribute("points", "0,1 8,4 0,7");
        poly.setAttribute("fill", def.hue);
        marker.append(poly);
        d.append(marker);
      }
      return d;
    }

    function medir() {
      const contenido = $("mp-contenido");
      const marco = contenido.getBoundingClientRect();
      const cajas = new Map();
      for (const nodo of contenido.querySelectorAll("[data-nodo]")) {
        const r = nodo.getBoundingClientRect();
        cajas.set(nodo.dataset.nodo, {
          x: r.left - marco.left,
          y: r.top - marco.top,
          w: r.width,
          h: r.height
        });
      }
      cache = { ancho: marco.width, alto: marco.height, cajas };
      return cache;
    }

    function remedir() {
      cache = null;
      dibujar();
    }

    function borde(caja, hacia) {
      const cx = caja.x + caja.w / 2;
      const cy = caja.y + caja.h / 2;
      const dx = hacia.x - cx;
      const dy = hacia.y - cy;
      if (!dx && !dy) return { x: cx, y: cy };
      const k = Math.min(
        dx ? (caja.w / 2 + 3) / Math.abs(dx) : Infinity,
        dy ? (caja.h / 2 + 3) / Math.abs(dy) : Infinity,
        1
      );
      return { x: cx + dx * k, y: cy + dy * k };
    }

    // Opacidad por capa: cada una llega al 3:1 que pide un grafico informativo.
    const OPACIDAD = { api: 0.75, internal: 0.7, movil: 0.75, s2s: 0.75, externo: 0.85 };
    let cables = [];

    function aplicarOpacidad() {
      const foco = resaltado || seleccion;
      for (const { path, arista } of cables) {
        const filtrado = ocultos.has(arista.desde) || ocultos.has(arista.hasta);
        const tocado = !foco || arista.desde === foco || arista.hasta === foco;
        path.setAttribute(
          "opacity",
          filtrado ? "0.05" : tocado ? String(OPACIDAD[arista.capa]) : "0.06"
        );
      }
    }

    function dibujar() {
      const { ancho, alto, cajas } = cache || medir();
      svg.setAttribute("viewBox", `0 0 ${ancho} ${alto}`);
      const piezas = [defs()];
      cables = [];

      for (const a of aristas) {
        if (!activas.has(a.capa) || !cajas.has(a.desde) || !cajas.has(a.hasta)) continue;
        const A = cajas.get(a.desde);
        const B = cajas.get(a.hasta);
        const p1 = borde(A, { x: B.x + B.w / 2, y: B.y + B.h / 2 });
        const p2 = borde(B, { x: A.x + A.w / 2, y: A.y + A.h / 2 });

        const dx = p2.x - p1.x;
        const dy = p2.y - p1.y;
        const dist = Math.hypot(dx, dy) || 1;
        const curva = Math.min(40, dist * 0.17);
        const cx = (p1.x + p2.x) / 2 - (dy / dist) * curva;
        const cy = (p1.y + p2.y) / 2 + (dx / dist) * curva;

        const path = document.createElementNS(NS, "path");
        path.setAttribute("d", `M ${p1.x.toFixed(1)} ${p1.y.toFixed(1)} Q ${cx.toFixed(1)} ${cy.toFixed(1)} ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`);
        path.setAttribute("fill", "none");
        path.setAttribute("stroke", CAPAS[a.capa].hue);
        path.setAttribute("stroke-width", a.capa === "internal" ? "1" : "1.3");
        path.setAttribute("stroke-linecap", "round");
        if (a.punteado || CAPAS[a.capa].punteado) path.setAttribute("stroke-dasharray", "4 3");
        path.setAttribute("marker-end", `url(#mp-punta-${a.capa})`);
        if (a.doble) path.setAttribute("marker-start", `url(#mp-punta-${a.capa})`);

        piezas.push(path);
        cables.push({ path, arista: a });
      }

      svg.replaceChildren(...piezas);
      aplicarOpacidad();
    }

    /* ---------- foco ---------- */

    function vecinos(nodo) {
      const set = new Set();
      for (const a of porNodo.get(nodo) || []) {
        if (!activas.has(a.capa)) continue;
        set.add(a.desde === nodo ? a.hasta : a.desde);
      }
      return set;
    }

    function pintarFoco() {
      const foco = resaltado || seleccion;
      const lienzo = $("mp-lienzo");
      lienzo.classList.toggle("enfocado", Boolean(foco));
      const cerca = foco ? vecinos(foco) : new Set();
      for (const nodo of lienzo.querySelectorAll("[data-nodo]")) {
        nodo.classList.toggle("foco", nodo.dataset.nodo === foco);
        nodo.classList.toggle("vecino", cerca.has(nodo.dataset.nodo));
        nodo.setAttribute("aria-pressed", String(nodo.dataset.nodo === seleccion));
      }
    }

    function resaltar(nodo) {
      resaltado = nodo;
      pintarFoco();
      aplicarOpacidad();
    }

    function seleccionar(nodo) {
      seleccion = nodo;
      pintarFoco();
      aplicarOpacidad();
      panel();
      if (nodo) {
        verPestania("detalle");
        $("mp-anuncio").textContent = nombreDe(nodo) + ": detalle actualizado.";
      }
    }

    /* ---------- panel ---------- */

    const hojaDetalle = $("mp-hoja-detalle");

    function nombreDe(id) {
      const [tipo, clave] = id.split(":");
      if (tipo === "mod") return modulos.get(clave)?.nombre || clave;
      if (tipo === "pwa") {
        const p = G.pwas.find(x => x.id === clave);
        return p ? nombrePwa(p) : clave;
      }
      return G.externos.find(x => x.id === clave)?.nombre || clave;
    }

    function bloque(titulo, contenido) {
      const b = el("section", "bloque");
      b.append(el("h4", null, titulo));
      b.append(contenido);
      return b;
    }

    function relacion(a, propio) {
      const otro = a.desde === propio ? a.hasta : a.desde;
      const caja = el("div", "rel");
      const linea = el("div", "rel-linea");
      const pip = el("span", "pip");
      pip.style.setProperty("--hue", CAPAS[a.capa].hue);
      linea.append(pip);
      const boton = el("button", null, (a.desde === propio ? "→ " : "← ") + nombreDe(otro));
      boton.type = "button";
      boton.addEventListener("click", () => seleccionar(otro));
      linea.append(boton);
      if (a.n > 1) linea.append(el("span", "n", a.n + " imports"));
      if (a.certeza === "inferido") linea.append(el("span", "n", "inferido"));
      caja.append(linea);

      // Visible, no en un title: un tooltip nativo no existe en tactil ni con teclado.
      if (a.ejemplos.length) {
        caja.append(el("p", "meta", a.ejemplos[0]));
        if (a.ejemplos.length > 1) {
          caja.append(el("p", "meta", `y ${a.ejemplos.length - 1} más`));
        }
      }
      return caja;
    }

    function panelInicial() {
      hojaDetalle.replaceChildren();
      hojaDetalle.append(el("h3", null, "Cómo leer el mapa"));
      hojaDetalle.append(el("p", "sub", "Pasá el cursor por un módulo para ver sus vínculos. Clic para fijarlo."));

      const caja = el("div");
      const puntos = [
        ["var(--api)", `<strong>${t.aristas_api} dependencias por fachada</strong> contra <strong>${t.aristas_internals} por imports de internals</strong>. Las fronteras están declaradas en <code>.importlinter</code>, pero la mayor parte del acoplamiento sigue siendo directo: ese es el baseline que el ratchet va cortando.`],
        ["var(--movil)", "El <strong>plano móvil</strong> (token DRF) y el <strong>server-to-server</strong> (API key) son dos superficies distintas y entran por módulos distintos."],
        ["var(--deuda)", "Prendé <em>Import de internals</em> arriba para ver el acoplamiento real. Está apagado por defecto porque tapa todo lo demás."]
      ];
      for (const [hue, html] of puntos) {
        const p = el("p", "hallazgo");
        p.style.setProperty("--hue", hue);
        p.innerHTML = html;
        caja.append(p);
      }
      hojaDetalle.append(bloque("Lo primero que se ve", caja));

      const contratos = el("ul", "lista");
      for (const c of G.contratos) {
        const li = el("li");
        li.append(el("span", null, c.nombre));
        li.append(el("span", "meta", c.excepciones.length ? c.excepciones.length + " excepción(es) en baseline" : "sin excepciones"));
        contratos.append(li);
      }
      hojaDetalle.append(bloque(`Contratos de arquitectura (${G.contratos.length})`, contratos));
    }

    function panel() {
      if (!seleccion) return panelInicial();
      hojaDetalle.replaceChildren();
      const [tipo, clave] = seleccion.split(":");

      if (tipo === "mod") {
        const m = modulos.get(clave);
        hojaDetalle.append(el("h3", null, m.nombre));
        hojaDetalle.append(el("p", "sub", m.id + "/"));

        const datos = el("dl", "datos");
        const filas2 = [
          ["líneas", miles(m.lineas) + ` en ${m.archivos} archivos`],
          ["zona", G.zonas.find(z => z.id === m.zona)?.nombre || m.zona],
          ["rutas web", m.rutas_web.join(" ") || "—"],
          ["rutas API", m.rutas_api.join(" ") || "—"],
          ["auth API", m.planos_api.map(x => PLANOS_API[x] || x).join(", ") || "—"],
          ["fachada", m.tiene_fachada ? m.id + "/api.py" : "no expone"]
        ];
        for (const [k, v] of filas2) datos.append(el("dt", null, k), el("dd", null, v));
        hojaDetalle.append(bloque("Ficha", datos));

        if (m.menu.length) {
          const lista = el("ul", "lista");
          for (const item of m.menu) {
            const li = el("li");
            li.append(el("span", null, item.label));
            li.append(el("span", "camino", [item.grupo, ...item.ruta].filter(Boolean).join(" / ")));
            if (item.permisos.length) li.append(el("span", "meta", item.permisos.join(" · ")));
            lista.append(li);
          }
          hojaDetalle.append(bloque(`Menú del usuario (${m.menu.length})`, lista));
        } else {
          hojaDetalle.append(bloque("Menú del usuario", el("p", "pista", "No tiene entrada propia: se llega desde otra pantalla o por API.")));
        }
      }

      if (tipo === "pwa") {
        const x = G.pwas.find(p => p.id === clave);
        hojaDetalle.append(el("h3", null, nombrePwa(x)));
        hojaDetalle.append(el("p", "sub", x.repository));
        const datos = el("dl", "datos");
        const filas2 = [
          ["ruta canónica", x.canonical_path],
          ["ruta previa", x.legacy_path || "—"],
          ["proyecto", x.project + " : " + x.port],
          ["checkout", x.checkout],
          ["habilitada", x.enabled ? "sí" : "no"]
        ];
        for (const [k, v] of filas2) datos.append(el("dt", null, k), el("dd", null, v));
        hojaDetalle.append(bloque("Despliegue", datos));

        if (x.consume.length) {
          const lista = el("ul", "lista");
          for (const c of x.consume) {
            const li = el("li");
            li.append(el("span", null, nombreDe("mod:" + c.modulo) + (c.certeza === "inferido" ? " (inferido)" : "")));
            li.append(el("span", "meta", c.evidencia));
            lista.append(li);
          }
          hojaDetalle.append(bloque("Qué consume de SISOC", lista));
        } else {
          hojaDetalle.append(bloque("Qué consume de SISOC", el("p", "pista", "Ningún namespace de API declarado para esta PWA en este repositorio.")));
        }
      }

      if (tipo === "ext") {
        const x = G.externos.find(e => e.id === clave);
        hojaDetalle.append(el("h3", null, x.nombre));
        hojaDetalle.append(el("p", "sub", x.direccion + (x.plano === "api_key" ? " · API key" : "")));
        hojaDetalle.append(bloque("Rol", el("p", "pista", x.rol)));
        hojaDetalle.append(bloque("Evidencia", el("p", "pista", x.evidencia)));
      }

      const mias = (porNodo.get(seleccion) || []).filter(a => activas.has(a.capa));
      const salen = mias.filter(a => a.desde === seleccion).sort((a, b) => b.n - a.n);
      const entran = mias.filter(a => a.hasta === seleccion).sort((a, b) => b.n - a.n);

      if (salen.length) {
        const caja = el("div");
        for (const a of salen) caja.append(relacion(a, seleccion));
        hojaDetalle.append(bloque(`Depende de (${salen.length})`, caja));
      }
      if (entran.length) {
        const caja = el("div");
        for (const a of entran) caja.append(relacion(a, seleccion));
        hojaDetalle.append(bloque(`Lo usan (${entran.length})`, caja));
      }
      if (!mias.length) {
        hojaDetalle.append(bloque("Vínculos", el("p", "pista", "Sin vínculos en las capas activas. Probá prendiendo Import de internals.")));
      }
    }

    /* ---------- pestaña de menú ---------- */

    const hojaMenu = $("mp-hoja-menu");

    for (const grupo of G.menu) {
      const caja = el("div", "grupo");
      const h = el("h4");
      h.append(el("span", null, grupo.label || "(sin nombre)"));
      h.append(el("span", "cant", grupo.items.length ? String(grupo.items.length) : "dinámico"));
      caja.append(h);

      if (!grupo.items.length) {
        caja.append(el("p", "pista", "Tableros armados por permiso al renderizar; no hay rutas fijas en el template."));
      } else {
        const lista = el("ul");
        let ramaActual = "";
        for (const item of grupo.items) {
          const rama = item.ruta.join(" / ");
          if (rama && rama !== ramaActual) {
            lista.append(el("li", "rama", rama));
            ramaActual = rama;
          }
          const li = el("li");
          li.dataset.nivel = String(item.nivel);
          const b = el("button");
          b.type = "button";
          b.append(el("span", "etq", item.label));
          b.append(el("span", "destino", item.app || "?"));
          b.title = item.permisos.length ? "Permisos del gate: " + item.permisos.join(", ") : "Sin permiso explícito en el template";
          if (item.app) {
            b.addEventListener("click", () => {
              seleccionar("mod:" + item.app);
              $("mp-lienzo").querySelector('[data-nodo="mod:' + item.app + '"]')?.scrollIntoView({ block: "nearest", behavior: "smooth" });
            });
            b.addEventListener("pointerenter", () => resaltar("mod:" + item.app));
            b.addEventListener("pointerleave", () => resaltar(null));
          }
          li.append(b);
          lista.append(li);
        }
        caja.append(lista);
      }
      hojaMenu.append(caja);
    }

    function verPestania(cual) {
      const esDetalle = cual === "detalle";
      $("mp-tab-detalle").tabIndex = esDetalle ? 0 : -1;
      $("mp-tab-menu").tabIndex = esDetalle ? -1 : 0;
      $("mp-tab-detalle").setAttribute("aria-selected", String(esDetalle));
      $("mp-tab-menu").setAttribute("aria-selected", String(!esDetalle));
      hojaDetalle.hidden = !esDetalle;
      hojaMenu.hidden = esDetalle;
    }

    $("mp-tab-detalle").addEventListener("click", () => verPestania("detalle"));
    $("mp-tab-menu").addEventListener("click", () => verPestania("menu"));

    raiz.querySelector(".pestanias").addEventListener("keydown", ev => {
      if (ev.key !== "ArrowLeft" && ev.key !== "ArrowRight") return;
      ev.preventDefault();
      const otra = ev.target.id === "mp-tab-detalle" ? "menu" : "detalle";
      verPestania(otra);
      $("mp-tab-" + otra).focus();
    });

    /* ---------- búsqueda ---------- */

    $("mp-busqueda").addEventListener("input", ev => {
      const consulta = ev.target.value.trim().toLowerCase();
      const lienzo = $("mp-lienzo");
      lienzo.classList.toggle("filtrando", Boolean(consulta));
      ocultos.clear();
      let visibles = 0;

      for (const nodo of lienzo.querySelectorAll("[data-nodo]")) {
        const [tipo, clave] = nodo.dataset.nodo.split(":");
        let heno = nodo.textContent.toLowerCase() + " " + clave.toLowerCase();
        if (tipo === "mod") heno += " " + (modulos.get(clave)?.menu || []).map(i => i.label).join(" ").toLowerCase();
        const fuera = Boolean(consulta) && !heno.includes(consulta);
        nodo.classList.toggle("oculto", fuera);
        if (fuera) ocultos.add(nodo.dataset.nodo);
        else visibles += 1;
      }

      aplicarOpacidad();
      $("mp-anuncio").textContent = consulta ? `${visibles} coincidencias.` : "";
    });

    document.addEventListener("keydown", ev => {
      if (ev.key === "Escape") {
        if (!ficha.hidden) {
          alternarFicha(false);
          btnAyuda.focus();
        } else if (seleccion) {
          seleccionar(null);
        }
      }
      if (ev.key === "/" && document.activeElement !== $("mp-busqueda")) {
        ev.preventDefault();
        $("mp-busqueda").focus();
      }
    });

    /* ---------- arranque ---------- */

    panelInicial();
    dibujar();

    new ResizeObserver(remedir).observe($("mp-contenido"));
    window.addEventListener("resize", remedir);
    if (document.fonts?.ready) document.fonts.ready.then(remedir);
  }

  /* ------------------------------------------------------------------ */

  if (window.__GRAFO_SISOC__) {
    arrancar(window.__GRAFO_SISOC__);
  } else if (raiz.dataset.grafo) {
    raiz.classList.add("mapa-app");
    const espera = el("div", "vacio");
    espera.append(el("p", null, "Cargando el mapa de arquitectura…"));
    raiz.replaceChildren(espera);

    fetch(raiz.dataset.grafo, { credentials: "same-origin" })
      .then(r => (r.ok ? r.json() : Promise.reject(new Error("HTTP " + r.status))))
      .then(arrancar)
      .catch(err => sinDatos("No se pudo leer el grafo: " + err.message));
  } else {
    sinDatos();
  }
})();
