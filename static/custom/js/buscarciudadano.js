document.addEventListener("DOMContentLoaded", function () {
    const inputDni = document.getElementById("busqueda-dni");
    const botonBuscar = document.getElementById("btn-buscar-dni");
    const buscarUrl = botonBuscar.dataset.url;

    const resultadoDiv = document.getElementById("resultado-busqueda");
    const formularioDiv = document.getElementById("formulario-participante");
    const formulario = formularioDiv ? formularioDiv.closest("form") : null;

    function buscar() {
        const query = inputDni.value;
        if (query.length >= 4) {
            fetch(`${buscarUrl}?query=${encodeURIComponent(query)}`)
                .then((response) => response.json())
                .then((data) => {
                    resultadoDiv.innerHTML = data.html;
                    if (
                        data.html.includes("No se encontraron coincidencias")
                    ) {
                        formularioDiv.style.display = "block";
                    } else {
                        formularioDiv.style.display = "none";
                        if (formulario) {
                            formulario.reset();
                        }
                    }
                });
        } else {
            resultadoDiv.innerHTML = "<p>Ingrese al menos 4 dígitos.</p>";
            formularioDiv.style.display = "none";
            if (formulario) {
                formulario.reset();
            }
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
