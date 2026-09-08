/**
 * MODAL DE ENCUESTA PENDIENTE
 *
 * Se carga globalmente (templates/includes/base.html) y no hace nada si no
 * hay #modal-encuesta-pendiente en la página (el context processor
 * encuestas.context_processors.ronda_pendiente no puso ninguna ronda).
 *
 * Además de mostrar el modal, deshabilita (no solo oculta) los campos de las
 * preguntas condicionales no visibles, para que el POST no los incluya y el
 * backend (encuestas.services._pregunta_es_visible) calcule la misma
 * visibilidad de forma independiente.
 */
(function () {
    "use strict";

    var modalEl = document.getElementById("modal-encuesta-pendiente");
    if (!modalEl) return;

    if (window.bootstrap && window.bootstrap.Modal) {
        window.bootstrap.Modal.getOrCreateInstance(modalEl).show();
    }

    var filas = Array.from(modalEl.querySelectorAll(".pregunta-respuesta"));
    var filasPorOrden = {};
    filas.forEach(function (fila) {
        filasPorOrden[fila.getAttribute("data-orden")] = fila;
    });

    function leerValor(fila) {
        var radioChecked = fila.querySelector('input[type="radio"]:checked');
        if (radioChecked) return radioChecked.value;

        var checkboxes = fila.querySelectorAll('input[type="checkbox"]:checked');
        if (checkboxes.length) {
            return Array.from(checkboxes).map(function (c) { return c.value; });
        }

        var select = fila.querySelector("select");
        if (select) return select.value;

        var input = fila.querySelector("input, textarea");
        return input ? input.value : "";
    }

    function cumpleCondicion(valorActual, operador, valorEsperado) {
        var incluye = Array.isArray(valorActual)
            ? valorActual.indexOf(valorEsperado) !== -1
            : valorActual === valorEsperado;
        return operador === "distinto" ? !incluye : incluye;
    }

    function actualizarVisibilidad() {
        filas.forEach(function (fila) {
            var ordenReferencia = fila.getAttribute("data-condicion-orden");
            if (!ordenReferencia) return;

            var filaReferencia = filasPorOrden[ordenReferencia];
            var visible = filaReferencia
                ? cumpleCondicion(
                    leerValor(filaReferencia),
                    fila.getAttribute("data-condicion-operador"),
                    fila.getAttribute("data-condicion-valor")
                )
                : false;

            fila.classList.toggle("d-none", !visible);
            fila.querySelectorAll("input, select, textarea").forEach(function (campo) {
                campo.disabled = !visible;
            });
        });
    }

    modalEl.addEventListener("change", actualizarVisibilidad);
    modalEl.addEventListener("input", actualizarVisibilidad);
    actualizarVisibilidad();
})();
