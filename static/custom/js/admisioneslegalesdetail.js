
// --- Modal Documento Expediente ---
document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("modalDocumentoExpediente");
    if (modal) {
        modal.addEventListener("show.bs.modal", function (event) {
            const button = event.relatedTarget;
            const tipo = button.getAttribute("data-bs-tipo");
            const label = button.getAttribute("data-bs-label");

            const tipoInput = modal.querySelector("#tipo_id");
            if (tipoInput) tipoInput.value = tipo;

            const modalTitle = modal.querySelector("#modalDocumentoExpedienteLabel");
            if (modalTitle) modalTitle.textContent = tipo;

            const modalLabel = modal.querySelector("#valueLabel");
            if (modalLabel) modalLabel.textContent = label;
        });
    }

    // --- Intervención Jurídicos ---
    const selectIntervencion = document.getElementById("id_intervencion_juridicos");
    const motivoField = document.getElementById("motivoRechazoField");
    const dictamenField = document.getElementById("motivoDictamenField");
    const motivoSelect = document.getElementById("id_rechazo_juridicos_motivo");
    const dictamenInput = document.getElementById("id_dictamen_motivo");

    function toggleMotivos() {
        if (selectIntervencion && selectIntervencion.value === "rechazado") {
            if (motivoField) motivoField.style.display = "block";
            if (motivoSelect) motivoSelect.required = true;

            if (motivoSelect && motivoSelect.value === "dictamen") {
                if (dictamenField) dictamenField.style.display = "block";
                if (dictamenInput) dictamenInput.required = true;
            } else {
                if (dictamenField) dictamenField.style.display = "none";
                if (dictamenInput) {
                    dictamenInput.required = false;
                    dictamenInput.value = "";
                }
            }
        } else {
            if (motivoField) motivoField.style.display = "none";
            if (dictamenField) dictamenField.style.display = "none";

            if (motivoSelect) {
                motivoSelect.required = false;
                motivoSelect.value = "";
            }
            if (dictamenInput) {
                dictamenInput.required = false;
                dictamenInput.value = "";
            }
        }
    }

    if (selectIntervencion) {
        selectIntervencion.addEventListener("change", toggleMotivos);
    }
    if (motivoSelect) {
        motivoSelect.addEventListener("change", toggleMotivos);
    }

    toggleMotivos();
});
