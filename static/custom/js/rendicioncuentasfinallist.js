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
});