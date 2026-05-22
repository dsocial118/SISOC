(function () {
    "use strict";

    function getConfig() {
        return document.getElementById("admisiones-tecnicos-config");
    }

    function getCsrfToken() {
        var config = getConfig();
        if (!config) return "";
        return config.dataset.csrfToken || "";
    }

    function getResyncUrl() {
        var config = getConfig();
        if (!config) return "";
        return config.dataset.urlResyncConvenio || "";
    }

    function mensajeParaAccion(accion) {
        if (accion === "actualizar") {
            return (
                "La información de la Admisión se actualizará desde el Legajo de la " +
                "Organización y se perderá el progreso realizado. " +
                "¿Está seguro de continuar?"
            );
        }
        if (accion === "continuar") {
            return (
                "Continuará gestionando la Admisión con la información ya procesada, " +
                "sin las últimas actualizaciones realizadas al Legajo de la Organización " +
                "correspondiente. ¿Está seguro de continuar?"
            );
        }
        return "";
    }

    function mostrarPasoSeleccion(elementos) {
        elementos.stepSeleccion.classList.remove("d-none");
        elementos.stepConfirmacion.classList.add("d-none");
        elementos.btnAplicar.classList.remove("d-none");
        elementos.btnVolver.classList.add("d-none");
        elementos.btnConfirmar.classList.add("d-none");
        elementos.btnAplicar.disabled = !elementos.select.value;
    }

    function mostrarPasoConfirmacion(elementos, accion) {
        elementos.mensaje.textContent = mensajeParaAccion(accion);
        elementos.stepSeleccion.classList.add("d-none");
        elementos.stepConfirmacion.classList.remove("d-none");
        elementos.btnAplicar.classList.add("d-none");
        elementos.btnVolver.classList.remove("d-none");
        elementos.btnConfirmar.classList.remove("d-none");
        elementos.btnConfirmar.disabled = false;
        elementos.btnConfirmar.dataset.accion = accion;
    }

    function inicializar() {
        var modalEl = document.getElementById("modalResyncConvenio");
        if (!modalEl) {
            return;
        }
        var elementos = {
            modalEl: modalEl,
            stepSeleccion: document.getElementById("modalResyncStepSeleccion"),
            stepConfirmacion: document.getElementById("modalResyncStepConfirmacion"),
            select: document.getElementById("accionResyncConvenio"),
            btnAplicar: document.getElementById("btnAplicarResyncConvenio"),
            btnVolver: document.getElementById("btnVolverResyncConvenio"),
            btnConfirmar: document.getElementById("btnConfirmarResyncConvenio"),
            mensaje: document.getElementById("modalConfirmarResyncConvenioMensaje"),
        };
        var modalInstance = bootstrap.Modal.getOrCreateInstance(modalEl);

        mostrarPasoSeleccion(elementos);

        elementos.select.addEventListener("change", function () {
            elementos.btnAplicar.disabled = !elementos.select.value;
        });

        elementos.btnAplicar.addEventListener("click", function () {
            var accion = elementos.select.value;
            if (!accion) return;
            mostrarPasoConfirmacion(elementos, accion);
        });

        elementos.btnVolver.addEventListener("click", function () {
            mostrarPasoSeleccion(elementos);
        });

        elementos.btnConfirmar.addEventListener("click", function () {
            var accion = elementos.btnConfirmar.dataset.accion;
            if (!accion) return;
            elementos.btnConfirmar.disabled = true;
            var url = getResyncUrl();
            if (!url) {
                alert("No se pudo determinar la URL del endpoint de resincronización.");
                elementos.btnConfirmar.disabled = false;
                return;
            }
            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCsrfToken(),
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Requested-With": "XMLHttpRequest",
                },
                body: new URLSearchParams({ accion: accion }),
            })
                .then(function (response) {
                    return response.json().then(function (data) {
                        return { ok: response.ok, data: data };
                    });
                })
                .then(function (payload) {
                    if (!payload.ok || !payload.data || payload.data.success === false) {
                        var error =
                            (payload.data && payload.data.error) ||
                            "No se pudo aplicar la acción.";
                        alert(error);
                        elementos.btnConfirmar.disabled = false;
                        return;
                    }
                    var redirect =
                        (payload.data && payload.data.redirect) || window.location.href;
                    window.location.href = redirect;
                })
                .catch(function () {
                    alert("Ocurrió un error al aplicar la acción.");
                    elementos.btnConfirmar.disabled = false;
                });
        });

        // Apertura forzada al cargar la pagina: el usuario no puede operar sobre
        // la admision sin elegir explicitamente una de las dos opciones.
        modalInstance.show();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", inicializar);
    } else {
        inicializar();
    }
})();
