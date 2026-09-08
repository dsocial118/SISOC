/**
 * EDITOR DINÁMICO DE PREGUNTAS - ENCUESTAS
 *
 * No usa formsets de Django: arma un array de preguntas en el cliente
 * (clonando #pregunta-row-template, mismo patrón que advanced_filters.js) y lo
 * serializa como JSON en el input oculto #preguntas_json justo antes de
 * enviar el formulario. El backend valida y parsea ese JSON en
 * encuestas/validators.py (parse_preguntas_payload).
 */
(function () {
    "use strict";

    var container = document.getElementById("preguntas-container");
    var template = document.getElementById("pregunta-row-template");
    var addBtn = document.getElementById("agregar-pregunta");
    var hiddenInput = document.getElementById("preguntas_json");
    var vacioMsg = document.getElementById("preguntas-vacio-msg");
    var cantidadEl = document.getElementById("preguntas-cantidad");
    var form = document.getElementById("encuesta-form");
    var contextEl = document.querySelector("[data-tipos-con-opciones]");
    var initialDataEl = document.getElementById("preguntas-iniciales");

    if (!container || !template || !addBtn || !hiddenInput || !form) {
        return;
    }

    var tiposConOpciones = (contextEl ? contextEl.getAttribute("data-tipos-con-opciones") : "")
        .split(",")
        .map(function (tipo) { return tipo.trim(); })
        .filter(Boolean);

    // Tipos que pueden ponderar para el puntaje total (ver Pregunta.pondera
    // en encuestas/models.py): Sí/No, opción única/múltiple y escala tienen
    // un conjunto fijo de valores posibles. Texto libre, numérico y fecha no
    // muestran el toggle de puntaje.
    var tiposPonderables = (contextEl ? contextEl.getAttribute("data-tipos-ponderables") : "")
        .split(",")
        .map(function (tipo) { return tipo.trim(); })
        .filter(Boolean);

    // Si/No y las preguntas de opción (única o múltiple) tienen un conjunto
    // fijo y conocido de valores posibles: para esas, "Valor esperado" se
    // arma con un <select> en vez de texto libre, para no depender de que
    // alguien escriba exactamente "si"/"Sí"/"SI" (motivo real de un bug: la
    // condición nunca coincidía porque el value real que viaja en el POST es
    // "si" en minúscula, ver campo_pregunta.html).
    var OPCIONES_SI_NO = [["si", "Sí"], ["no", "No"]];

    function actualizarVacioMsg() {
        var hayFilas = container.children.length > 0;
        if (vacioMsg) vacioMsg.classList.toggle("d-none", hayFilas);
        if (cantidadEl) cantidadEl.textContent = String(container.children.length);
    }

    /** Renumera badges y refresca las opciones de "mostrar si" de cada fila
     * para que cada una solo pueda referenciar preguntas anteriores. */
    function renumerarFilas() {
        var filas = Array.from(container.children);
        filas.forEach(function (fila, indice) {
            var refs = fila._preguntaRefs;
            if (!refs) return;
            refs.numero.textContent = "Pregunta " + (indice + 1);
            refs.quitarBtn.classList.toggle("d-none", false);

            var valorPrevio = refs.condicionRef.value;
            refs.condicionRef.innerHTML = "";
            refs.condicionRef.appendChild(crearOption("", "(siempre visible)"));
            filas.slice(0, indice).forEach(function (filaAnterior) {
                var refsAnterior = filaAnterior._preguntaRefs;
                var texto = refsAnterior.texto.value.trim() || ("Pregunta " + (filas.indexOf(filaAnterior) + 1));
                refsAnterior._orden = filas.indexOf(filaAnterior) + 1;
                refs.condicionRef.appendChild(crearOption(String(refsAnterior._orden), texto));
            });
            refs.condicionRef.value = valorPrevio;
            var condicionDisponible = indice > 0;
            refs.condicionWrap.classList.toggle("d-none", !condicionDisponible);
            if (!condicionDisponible) {
                refs.condicionRef.value = "";
            }
        });
        refrescarCondicionesValor();
    }

    /** Devuelve las opciones [valor, etiqueta] disponibles para la condición
     * según el tipo de la pregunta referenciada, o null si ese tipo no tiene
     * un conjunto fijo (texto/número/fecha siguen siendo texto libre). */
    function opcionesCondicionParaFila(filaReferencia) {
        var refsRef = filaReferencia._preguntaRefs;
        if (refsRef.tipo.value === "si_no") return OPCIONES_SI_NO;
        if (tiposConOpciones.indexOf(refsRef.tipo.value) !== -1) {
            return refsRef.opciones.value
                .split("\n")
                .map(function (linea) { return linea.trim(); })
                .filter(Boolean)
                .map(function (linea) { return [linea, linea]; });
        }
        return null;
    }

    function leerValorCondicionActivo(refs) {
        if (!refs.condicionValorSelect.classList.contains("d-none")) {
            return refs.condicionValorSelect.value;
        }
        return refs.condicionValor.value;
    }

    function escribirValorCondicionActivo(refs, valor) {
        if (!refs.condicionValorSelect.classList.contains("d-none")) {
            refs.condicionValorSelect.value = valor;
        } else {
            refs.condicionValor.value = valor;
        }
    }

    /** Muestra el <select> de valores fijos (y lo repuebla) o el <input> de
     * texto libre, según el tipo de la pregunta que esta fila referencia. */
    function actualizarValorCondicion(refs) {
        var ordenRef = parseInt(refs.condicionRef.value, 10);
        var filaReferencia = ordenRef ? container.children[ordenRef - 1] : null;
        var opciones = filaReferencia ? opcionesCondicionParaFila(filaReferencia) : null;

        if (!opciones) {
            refs.condicionValorSelect.classList.add("d-none");
            refs.condicionValorSelect.innerHTML = "";
            refs.condicionValor.classList.remove("d-none");
            return;
        }

        var valorPrevio = leerValorCondicionActivo(refs);
        refs.condicionValorSelect.innerHTML = "";
        opciones.forEach(function (par) {
            refs.condicionValorSelect.appendChild(crearOption(par[0], par[1]));
        });
        if (opciones.some(function (par) { return par[0] === valorPrevio; })) {
            refs.condicionValorSelect.value = valorPrevio;
        }
        refs.condicionValor.classList.add("d-none");
        refs.condicionValorSelect.classList.remove("d-none");
    }

    function refrescarCondicionesValor() {
        Array.from(container.children).forEach(function (fila) {
            actualizarValorCondicion(fila._preguntaRefs);
        });
    }

    function crearOption(value, label) {
        var option = document.createElement("option");
        option.value = value;
        option.textContent = label;
        return option;
    }

    function actualizarVisibilidadOpciones(refs) {
        var requiereOpciones = tiposConOpciones.indexOf(refs.tipo.value) !== -1;
        refs.opcionesWrap.classList.toggle("d-none", !requiereOpciones);
    }

    /** Renueva las filas de "puntaje por opción" a partir de las líneas
     * actuales del textarea de opciones, conservando el puntaje ya cargado
     * por texto de opción (no por posición: reordenar o agregar una línea
     * en el medio no desarma los puntajes ya cargados de las demás). */
    function actualizarFilasPuntajeOpciones(refs) {
        var textos = refs.opciones.value
            .split("\n")
            .map(function (linea) { return linea.trim(); })
            .filter(Boolean);

        refs.puntajeOpcionesList.innerHTML = "";
        textos.forEach(function (texto) {
            var fila = document.createElement("div");
            fila.className = "puntaje-opcion-row";

            var label = document.createElement("span");
            label.className = "puntaje-opcion-texto";
            label.textContent = texto;
            label.title = texto;

            var input = document.createElement("input");
            input.type = "number";
            input.min = "0";
            input.className = "form-control puntaje-opcion-input";
            input.value = Object.prototype.hasOwnProperty.call(refs._puntajesPorOpcion, texto)
                ? refs._puntajesPorOpcion[texto]
                : 0;
            input.addEventListener("input", function () {
                refs._puntajesPorOpcion[texto] = input.value;
            });

            fila.appendChild(label);
            fila.appendChild(input);
            refs.puntajeOpcionesList.appendChild(fila);
        });
    }

    /** Muestra los campos de puntaje que correspondan según el tipo de
     * pregunta, solo si el switch "¿Pondera?" está activo. */
    function actualizarDetallePondera(refs) {
        var activo = refs.pondera.checked;
        refs.ponderaDetalle.classList.toggle("d-none", !activo);
        refs.puntajeSiNoWrap.classList.add("d-none");
        refs.puntajeOpcionesWrap.classList.add("d-none");
        refs.puntajeEscalaNota.classList.add("d-none");
        if (!activo) return;

        if (refs.tipo.value === "si_no") {
            refs.puntajeSiNoWrap.classList.remove("d-none");
        } else if (tiposConOpciones.indexOf(refs.tipo.value) !== -1) {
            refs.puntajeOpcionesWrap.classList.remove("d-none");
            actualizarFilasPuntajeOpciones(refs);
        } else if (refs.tipo.value === "escala") {
            refs.puntajeEscalaNota.classList.remove("d-none");
        }
    }

    /** Muestra u oculta el switch "¿Pondera?" según si el tipo de pregunta
     * tiene un conjunto fijo de valores posibles. */
    function actualizarVisibilidadPondera(refs) {
        var esPonderable = tiposPonderables.indexOf(refs.tipo.value) !== -1;
        refs.ponderaWrap.classList.toggle("d-none", !esPonderable);
        if (!esPonderable) {
            refs.pondera.checked = false;
        }
        actualizarDetallePondera(refs);
    }

    function crearFila(datosIniciales) {
        var fragmento = template.content.cloneNode(true);
        var fila = fragmento.querySelector(".pregunta-row");

        var refs = {
            numero: fila.querySelector(".pregunta-numero"),
            quitarBtn: fila.querySelector(".btn-quitar-pregunta"),
            texto: fila.querySelector(".pregunta-texto"),
            tipo: fila.querySelector(".pregunta-tipo"),
            obligatoria: fila.querySelector(".pregunta-obligatoria"),
            opcionesWrap: fila.querySelector(".pregunta-opciones-wrap"),
            opciones: fila.querySelector(".pregunta-opciones"),
            condicionWrap: fila.querySelector(".pregunta-condicion-wrap"),
            condicionRef: fila.querySelector(".pregunta-condicion-referencia"),
            condicionOperador: fila.querySelector(".pregunta-condicion-operador"),
            condicionValor: fila.querySelector(".pregunta-condicion-valor"),
            condicionValorSelect: fila.querySelector(".pregunta-condicion-valor-select"),
            ponderaWrap: fila.querySelector(".pregunta-pondera-wrap"),
            pondera: fila.querySelector(".pregunta-pondera"),
            ponderaDetalle: fila.querySelector(".pregunta-puntaje-detalle"),
            puntajeSiNoWrap: fila.querySelector(".pregunta-puntaje-si-no"),
            puntajeSi: fila.querySelector(".pregunta-puntaje-si"),
            puntajeNo: fila.querySelector(".pregunta-puntaje-no"),
            puntajeOpcionesWrap: fila.querySelector(".pregunta-puntaje-opciones-wrap"),
            puntajeOpcionesList: fila.querySelector(".pregunta-puntaje-opciones-list"),
            puntajeEscalaNota: fila.querySelector(".pregunta-puntaje-escala-nota"),
            _puntajesPorOpcion: {},
        };

        refs.tipo.addEventListener("change", function () {
            actualizarVisibilidadOpciones(refs);
            actualizarVisibilidadPondera(refs);
            refrescarCondicionesValor();
        });
        refs.opciones.addEventListener("input", function () {
            actualizarDetallePondera(refs);
            refrescarCondicionesValor();
        });
        refs.pondera.addEventListener("change", function () {
            actualizarDetallePondera(refs);
        });
        refs.condicionRef.addEventListener("change", function () {
            actualizarValorCondicion(refs);
        });
        refs.texto.addEventListener("input", renumerarFilas);
        refs.quitarBtn.addEventListener("click", function () {
            fila.remove();
            actualizarVacioMsg();
            renumerarFilas();
        });

        fila._preguntaRefs = refs;
        container.appendChild(fila);

        if (datosIniciales) {
            refs.texto.value = datosIniciales.texto || "";
            refs.tipo.value = datosIniciales.tipo || refs.tipo.value;
            refs.obligatoria.checked = datosIniciales.obligatoria !== false;
            var opcionesIniciales = (datosIniciales.opciones || []).map(function (opcion) {
                return typeof opcion === "object" ? opcion : { texto: opcion, puntaje: 0 };
            });
            refs.opciones.value = opcionesIniciales
                .map(function (opcion) { return opcion.texto; })
                .join("\n");
            opcionesIniciales.forEach(function (opcion) {
                refs._puntajesPorOpcion[opcion.texto] = opcion.puntaje || 0;
            });
            refs.pondera.checked = Boolean(datosIniciales.pondera);
            refs.puntajeSi.value = datosIniciales.puntaje_si || 0;
            refs.puntajeNo.value = datosIniciales.puntaje_no || 0;
        }
        actualizarVisibilidadOpciones(refs);
        actualizarVisibilidadPondera(refs);

        renumerarFilas();
        actualizarVacioMsg();
        return refs;
    }

    /** Aplica la condición guardada una vez que todas las filas ya existen
     * (necesita que el select de referencia ya tenga las opciones cargadas). */
    function aplicarCondicionesIniciales(datosPorFila) {
        var filas = Array.from(container.children);
        filas.forEach(function (fila, indice) {
            var datos = datosPorFila[indice];
            if (!datos || !datos.condicion) return;
            var refs = fila._preguntaRefs;
            refs.condicionRef.value = String(datos.condicion.orden);
            refs.condicionOperador.value = datos.condicion.operador;
            actualizarValorCondicion(refs);
            escribirValorCondicionActivo(refs, datos.condicion.valor);
        });
    }

    addBtn.addEventListener("click", function () { crearFila(); });

    function serializarPreguntas() {
        var filas = Array.from(container.children);
        return filas.map(function (fila, indice) {
            var refs = fila._preguntaRefs;
            var orden = indice + 1;
            var item = {
                orden: orden,
                texto: refs.texto.value.trim(),
                tipo: refs.tipo.value,
                obligatoria: refs.obligatoria.checked,
                opciones: refs.opciones.value
                    .split("\n")
                    .map(function (linea) { return linea.trim(); })
                    .filter(Boolean)
                    .map(function (texto) {
                        return {
                            texto: texto,
                            puntaje: parseInt(refs._puntajesPorOpcion[texto], 10) || 0,
                        };
                    }),
                pondera: refs.pondera.checked,
                puntaje_si: parseInt(refs.puntajeSi.value, 10) || 0,
                puntaje_no: parseInt(refs.puntajeNo.value, 10) || 0,
                condicion: null,
            };
            if (refs.condicionRef.value) {
                item.condicion = {
                    orden: parseInt(refs.condicionRef.value, 10),
                    operador: refs.condicionOperador.value,
                    valor: leerValorCondicionActivo(refs).trim(),
                };
            }
            return item;
        });
    }

    form.addEventListener("submit", function () {
        hiddenInput.value = JSON.stringify(serializarPreguntas());
    });

    // Hidratación inicial: datos existentes (editar) o el último intento
    // fallido (si el formulario volvió con errores).
    var datosIniciales = [];
    if (initialDataEl) {
        try {
            datosIniciales = JSON.parse(initialDataEl.textContent) || [];
        } catch (e) {
            datosIniciales = [];
        }
    }
    datosIniciales.forEach(function (datos) { crearFila(datos); });
    aplicarCondicionesIniciales(datosIniciales);
    actualizarVacioMsg();
})();
