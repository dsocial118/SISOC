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
        };

        refs.tipo.addEventListener("change", function () {
            actualizarVisibilidadOpciones(refs);
            refrescarCondicionesValor();
        });
        refs.opciones.addEventListener("input", refrescarCondicionesValor);
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
            refs.opciones.value = (datosIniciales.opciones || []).join("\n");
        }
        actualizarVisibilidadOpciones(refs);

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
                    .filter(Boolean),
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
