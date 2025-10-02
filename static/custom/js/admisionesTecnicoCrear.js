document.addEventListener("DOMContentLoaded", function () {
    const modalElement = document.getElementById("seleccionModal");
    const selectTipo = document.getElementById("tipoConvenio");
    const confirmarBtn = document.getElementById("confirmarSeleccion");

    if (!modalElement || !selectTipo || !confirmarBtn) {
        return;
    }

    let bootstrapModal = null;

    if (window.bootstrap && typeof bootstrap.Modal === "function") {
        bootstrapModal = new bootstrap.Modal(modalElement, {
            backdrop: "static",
            keyboard: false,
        });
        bootstrapModal.show();
    } else if (window.jQuery && typeof window.jQuery(modalElement).modal === "function") {
        window.jQuery(modalElement).modal({ backdrop: "static", keyboard: false });
        window.jQuery(modalElement).modal("show");
    }

    selectTipo.addEventListener("change", function () {
        confirmarBtn.disabled = !selectTipo.value;
    });

    confirmarBtn.addEventListener("click", function () {
        if (!selectTipo.value) {
            return;
        }

        if (bootstrapModal) {
            bootstrapModal.hide();
        } else if (window.jQuery && typeof window.jQuery(modalElement).modal === "function") {
            window.jQuery(modalElement).modal("hide");
        }

        if (typeof actualizarTabla === "function") {
            actualizarTabla(selectTipo.value);
        }
    });
});
