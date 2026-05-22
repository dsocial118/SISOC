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

    function inicializar() {
        var selectAccion = document.getElementById("accionResyncConvenio");
        var btnAplicar = document.getElementById("btnAplicarResyncConvenio");
        var modalEl = document.getElementById("modalConfirmarResyncConvenio");
        var mensajeEl = document.getElementById("modalConfirmarResyncConvenioMensaje");
        var btnConfirmar = document.getElementById("btnConfirmarResyncConvenio");
        if (!selectAccion || !btnAplicar || !modalEl || !mensajeEl || !btnConfirmar) {
            return;
        }
        var modalInstance = bootstrap.Modal.getOrCreateInstance(modalEl);

        selectAccion.addEventListener("change", function () {
            btnAplicar.disabled = !selectAccion.value;
        });

        btnAplicar.addEventListener("click", function () {
            var accion = selectAccion.value;
            if (!accion) return;
            mensajeEl.textContent = mensajeParaAccion(accion);
            btnConfirmar.dataset.accion = accion;
            modalInstance.show();
        });

        btnConfirmar.addEventListener("click", function () {
            var accion = btnConfirmar.dataset.accion;
            if (!accion) return;
            btnConfirmar.disabled = true;
            var url = getResyncUrl();
            if (!url) {
                alert("No se pudo determinar la URL del endpoint de resincronización.");
                btnConfirmar.disabled = false;
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
                        btnConfirmar.disabled = false;
                        return;
                    }
                    modalInstance.hide();
                    var redirect =
                        (payload.data && payload.data.redirect) || window.location.href;
                    window.location.href = redirect;
                })
                .catch(function () {
                    alert("Ocurrió un error al aplicar la acción.");
                    btnConfirmar.disabled = false;
                });
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", inicializar);
    } else {
        inicializar();
    }
})();
