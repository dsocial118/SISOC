document.addEventListener("DOMContentLoaded", function () {
    const inputDni = document.getElementById("busqueda-dni");
    const botonBuscar = document.getElementById("btn-buscar-dni");

    const resultadoDiv = document.getElementById("resultado-busqueda");

    function buscar() {
        const query = inputDni.value;
        if (query.length >= 4) {
            fetch(`/centros/buscar-ciudadano/?query=${query}`)
                .then((response) => response.json())
                .then((data) => {
                    resultadoDiv.innerHTML = data.html;
                });
        } else {
            resultadoDiv.innerHTML = "<p>Ingrese al menos 4 dígitos.</p>";
        }
    }

    // Buscar al presionar el botón
    botonBuscar.addEventListener("click", buscar);

    // Buscar automáticamente al tipear
    inputDni.addEventListener("input", function () {
        if (inputDni.value.length >= 4) {
            buscar();
        }
    });
});
