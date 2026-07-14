(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        var programaSelect = document.getElementById("id_programa");
        var categoriaSelect = document.getElementById("id_categoria");

        if (!programaSelect || !categoriaSelect) {
            return;
        }

        // El filtrado quita opciones del DOM, así que hay que conservar la lista
        // completa para poder restaurarlas al cambiar de programa.
        var todasLasOpciones = Array.prototype.slice.call(categoriaSelect.options);

        function sincronizarCategorias() {
            var programaId = programaSelect.value;
            var seleccionActual = categoriaSelect.value;
            var seleccionSigueValida = false;

            categoriaSelect.innerHTML = "";

            todasLasOpciones.forEach(function (opcion) {
                var programaDeLaOpcion = opcion.getAttribute("data-programa");

                // La opción vacía ("Sin categoría") no tiene programa: siempre disponible.
                if (!programaDeLaOpcion) {
                    categoriaSelect.appendChild(opcion);
                    return;
                }

                if (programaId && programaDeLaOpcion === programaId) {
                    categoriaSelect.appendChild(opcion);
                    if (opcion.value === seleccionActual) {
                        seleccionSigueValida = true;
                    }
                }
            });

            categoriaSelect.value = seleccionSigueValida ? seleccionActual : "";
        }

        programaSelect.addEventListener("change", sincronizarCategorias);
        sincronizarCategorias();
    });
})();
