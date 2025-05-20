document.addEventListener("DOMContentLoaded", function () {
    var modal = document.getElementById("modalSubsanar");
    var form = document.getElementById("formSubsanar");

    modal.addEventListener("show.bs.modal", function (event) {
        var button = event.relatedTarget;
        var documentoId = button.getAttribute("data-documento-id");
        var actionUrl = SUBSANAR_URL.replace("0", documentoId);

        form.action = actionUrl;
        form.querySelector("textarea[name='observacion']").value = "";
    });

    const toggleBtn = document.getElementById("toggle-validados");
    let ocultos = false;

    toggleBtn.addEventListener("click", function () {
        const rows = document.querySelectorAll(
            ".estado-validado, .estado-subsanar"
        );

        rows.forEach(row => {
            row.style.display = ocultos ? "table-row" : "none";
        });

        ocultos = !ocultos;
        toggleBtn.textContent = ocultos
            ? "Mostrar analizados"
            : "Ocultar analizados";
    });
});