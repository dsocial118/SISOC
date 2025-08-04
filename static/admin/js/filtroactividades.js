document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("buscadorActividades");
    const table = document.getElementById("tablaActividades");
    const rows = table.getElementsByTagName("tr");

    input.addEventListener("keyup", function () {
        const filtro = input.value.toLowerCase();

        for (let i = 0; i < rows.length; i++) {
            const texto = rows[i].innerText.toLowerCase();
            rows[i].style.display = texto.includes(filtro) ? "" : "none";
        }
    });
});