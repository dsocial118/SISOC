document.addEventListener("DOMContentLoaded", function () {
    let selectConvenio = document.getElementById("nuevoTipoConvenio");
    let confirmarBtn = document.getElementById("nuevoConfirmarSeleccion");

    selectConvenio.addEventListener("change", function () {
        confirmarBtn.disabled = !selectConvenio.value;
    });
});

function subirArchivo(admisionId, documentoId) {
    let inputFile = document.getElementById(`file-${documentoId}`);
    let file = inputFile.files[0];

    if (!file) {
        alert("Por favor, selecciona un archivo antes de archivar.");
        return;
    }

    // Crear un nuevo contenedor para la barra de progreso
    let progressContainer = document.getElementById(`progress-container-${documentoId}`);
    let progressBar = document.getElementById(`progress-bar-${documentoId}`);

    // Mostrar la barra de progreso
    progressContainer.style.display = "block";
    progressBar.style.width = "0%";
    progressBar.innerText = "0%";

    let formData = new FormData();
    formData.append("archivo", file);

    let url = `/admision/${admisionId}/documentacion/${documentoId}/subir/`;

    let xhr = new XMLHttpRequest();
    xhr.open("POST", url, true); // ver lo de crftoken aca mas tarde {% csrf_token %}*

    // Enviar la solicitud con el progreso
    xhr.upload.onprogress = function (event) {
        if (event.lengthComputable) {
            let percent = (event.loaded / event.total) * 100;
            progressBar.style.width = percent + "%";
            progressBar.innerText = Math.round(percent) + "%";
        }
    };

    xhr.onload = function () {
        if (xhr.status === 200) {
            let data = JSON.parse(xhr.responseText);
            if (data.success) {
                document.getElementById(`estado-${documentoId}`).innerText = "A Validar";
                inputFile.disabled = true; 
                let button = inputFile.nextElementSibling;
                button.innerText = "Archivado";
                button.disabled = true;

                // Agregar botón de eliminar
                let fila = document.getElementById(`fila-${documentoId}`);
                let eliminarBtn = document.createElement("button");
                eliminarBtn.className = "btn btn-sm btn-danger fw-bold px-3";
                eliminarBtn.innerText = "X";
                eliminarBtn.onclick = function () {
                    confirmarEliminar(admisionId, documentoId);
                };
                fila.querySelector("td:last-child").appendChild(eliminarBtn);

                // Ocultar la barra de progreso una vez completado
                progressContainer.style.display = "none";
            } else {
                alert("Error al subir el archivo: " + data.error);
                // Ocultar la barra de progreso si ocurre un error
                progressContainer.style.display = "none";
            }
        } else {
            alert("Error al subir el archivo");
            // Ocultar la barra de progreso si ocurre un error
            progressContainer.style.display = "none";
        }
    };

    xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN); 
    xhr.send(formData);
}

let admisionIdEliminar;
let documentoIdEliminar;

function confirmarEliminar(admisionId, documentoId) {
    admisionIdEliminar = admisionId;
    documentoIdEliminar = documentoId;
    $("#modalConfirmarEliminar").modal("show");
}

document.getElementById("btnConfirmarEliminar").addEventListener("click", function () {
    eliminarArchivo(admisionIdEliminar, documentoIdEliminar);
});

function eliminarArchivo(admisionId, documentoId) {
    let url = `/admision/${admisionId}/documentacion/${documentoId}/eliminar/`;

    fetch(url, {
        method: "DELETE",
        headers: {
            "X-CSRFToken": CSRF_TOKEN,
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            let fila = document.getElementById(`fila-${documentoId}`);
            fila.innerHTML = `
                <td class="ps-3">${data.nombre}</td>
                <td class="px-3" id="estado-${documentoId}">Pendiente</td>
                <td>
                    <input type="file" id="file-${documentoId}" />
                    <button class="btn btn-primary btn-sm" onclick="subirArchivo(${admisionId}, ${documentoId})">Archivar</button>
                    <!-- Volver a agregar la barra de progreso -->
                    <div class="progress mt-2" style="display:none; height: 3px;"" id="progress-container-${documentoId}">
                        <div class="progress-bar  progress-bar-striped" role="progressbar" id="progress-bar-${documentoId}" style="width: 0%;">0%</div>
                    </div>
                </td>
            `;
            $("#modalConfirmarEliminar").modal("hide");
        } else {
            alert("Error al eliminar el archivo: " + data.error);
        }
    })
    .catch(error => console.error("Error al eliminar:", error));
}