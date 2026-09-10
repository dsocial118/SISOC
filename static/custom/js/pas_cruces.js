(function (window, document) {
    document.addEventListener("DOMContentLoaded", function () {
        const form = document.getElementById("pas-renaper-update-form");
        if (!form) {
            return;
        }
        form.addEventListener("submit", function (event) {
            const confirmado = window.confirm(
                "Se solicitará el control mensual RENAPER. Si ya existe, se conservará esa corrida. ¿Desea continuar?"
            );
            if (!confirmado) {
                event.preventDefault();
            }
        });
    });
})(window, document);
