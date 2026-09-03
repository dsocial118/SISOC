(function (window, document) {
    document.addEventListener("DOMContentLoaded", function () {
        const form = document.getElementById("pas-renaper-update-form");
        if (!form) {
            return;
        }
        form.addEventListener("submit", function (event) {
            const confirmado = window.confirm(
                "Se volverá a consultar RENAPER para todo el padrón PAS. ¿Desea continuar?"
            );
            if (!confirmado) {
                event.preventDefault();
            }
        });
    });
})(window, document);
