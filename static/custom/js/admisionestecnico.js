const PERSONALIZED_FLAG = "1";

document.addEventListener("DOMContentLoaded", function () {
    const nombreInput = document.getElementById("nuevoDocumentoNombre");
    const archivoInput = document.getElementById("nuevoDocumentoArchivo");
    const abrirBtn = document.getElementById("btnAbrirFile");
    const progressContainer = document.getElementById("progress-container-nuevo");
    const progressBar = document.getElementById("progress-bar-nuevo");

    if (nombreInput && archivoInput && abrirBtn && window.URL_CREAR_DOCUMENTO_PERSONALIZADO) {
        abrirBtn.addEventListener("click", function () {
            if (!nombreInput.value.trim()) {
                alert("Por favor, escriba un nombre antes de adjuntar un archivo.");
                return;
            }
            archivoInput.click();
        });

        archivoInput.addEventListener("change", function () {
            if (!archivoInput.files.length) return;

            const formData = new FormData();
            formData.append("nombre", nombreInput.value.trim());
            formData.append("archivo", archivoInput.files[0]);

            progressContainer.style.display = "block";
            progressBar.style.width = "0%";
            progressBar.textContent = "0%";

            const xhr = new XMLHttpRequest();
            xhr.open("POST", window.URL_CREAR_DOCUMENTO_PERSONALIZADO, true);
            xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);

            xhr.upload.addEventListener("progress", function (e) {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = percent + "%";
                    progressBar.textContent = percent + "%";
                }
            });

            xhr.onload = function () {
                const hideProgress = () => {
                    progressContainer.style.display = "none";
                };

                let data;

                try {
                    data = JSON.parse(xhr.responseText);
                    console.log("Respuesta servidor:", data);
                } catch (error) {
                    console.error("Respuesta inesperada:", xhr.responseText);
                    alert("Error inesperado en la respuesta del servidor.");
                    hideProgress();
                    return;
                }

                const isSuccessful = xhr.status >= 200 && xhr.status < 300 && data && data.success;

                if (isSuccessful) {
                    const tbody = document.getElementById("tablaDocumentosBody");
                    const placeholderRow = document.getElementById("fila-agregar-documento");

                    if (tbody && placeholderRow && data.html) {
                        placeholderRow.insertAdjacentHTML("beforebegin", data.html);
                    }

                    nombreInput.value = "";
                    archivoInput.value = "";

                    if (progressBar) {
                        progressBar.style.width = "100%";
                        progressBar.textContent = "100%";
                    }

                    hideProgress();
                    return;
                }

                alert((data && data.error) || "No se pudo cargar el documento.");
                hideProgress();
            };

            xhr.onerror = function () {
                alert("Error de red al subir el documento.");
                progressContainer.style.display = "none";
            };

            xhr.send(formData);
        });
    }
});


function subirArchivo(admisionId, documentoId) {
    const inputFile = document.getElementById(`file-${documentoId}`);
    const file = inputFile ? inputFile.files[0] : null;

    if (!file) {
        alert("Por favor, selecciona un archivo antes de adjuntar.");
        return;
    }

    const progressContainer = document.getElementById(`progress-container-${documentoId}`);
    const progressBar = document.getElementById(`progress-bar-${documentoId}`);

    if (progressContainer && progressBar) {
        progressContainer.style.display = "block";
        progressBar.style.width = "0%";
        progressBar.innerText = "0%";
    }

    const formData = new FormData();
    formData.append("archivo", file);

    const url = `/admision/${admisionId}/documentacion/${documentoId}/subir/`;
    const xhr = new XMLHttpRequest();
    xhr.open("POST", url, true);

    xhr.upload.onprogress = function (event) {
        if (event.lengthComputable && progressBar) {
            const percent = (event.loaded / event.total) * 100;
            progressBar.style.width = `${percent}%`;
            progressBar.innerText = `${Math.round(percent)}%`;
        }
    };

    xhr.onload = function () {
        if (xhr.status === 200) {
            const data = JSON.parse(xhr.responseText);
            if (data.success && data.html && data.row_id) {
                const existingRow = document.getElementById(`fila-${data.row_id}`);
                if (existingRow) {
                    existingRow.outerHTML = data.html;
                }
            } else if (!data.success) {
                alert("Error al subir el archivo: " + (data.error || ""));
            }
        } else {
            alert("Error al subir el archivo");
        }

        if (progressContainer) {
            progressContainer.style.display = "none";
        }
    };

    xhr.onerror = function () {
        alert("Error al subir el archivo");
        if (progressContainer) {
            progressContainer.style.display = "none";
        }
    };

    xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
    xhr.send(formData);
}

let admisionIdEliminar;
let documentacionIdEliminar;
let archivoIdEliminar;

function construirUrlEliminar(admisionId, identifier, includePreview = false) {
    let url = `/admision/${admisionId}/documentacion/${identifier}/eliminar/`;
    const params = new URLSearchParams();
    if (archivoIdEliminar !== null) {
        params.append("archivo_id", archivoIdEliminar);
    }
    if (includePreview) {
        params.append("preview", "1");
    }
    if ([...params].length) {
        url += `?${params.toString()}`;
    }
    return url;
}

function renderizarPreview(preview) {
    if (!preview || !Array.isArray(preview.desglose_por_modelo)) {
        return "¿Estás seguro de que deseas dar de baja este archivo?";
    }
    const lineas = preview.desglose_por_modelo
        .map((item) => `- ${item.modelo}: ${item.cantidad}`)
        .join("<br>");
    return `
        <p>Se realizará una baja lógica en cascada.</p>
        <p><strong>Total de registros afectados:</strong> ${preview.total_afectados}</p>
        <p class="mb-0">${lineas || "-"}</p>
    `;
}

function confirmarEliminar(admisionId, documentacionId, archivoId) {
    admisionIdEliminar = admisionId;
    documentacionIdEliminar = documentacionId !== undefined && documentacionId !== null
        ? documentacionId
        : null;
    archivoIdEliminar = archivoId !== undefined && archivoId !== null
        ? archivoId
        : null;
    const identifier = documentacionIdEliminar !== null ? documentacionIdEliminar : archivoIdEliminar;
    const modalBody = document.getElementById("modalConfirmarEliminarBody");
    if (!identifier) {
        if (modalBody) {
            modalBody.textContent = "No se pudo preparar la baja del archivo.";
        }
        $("#modalConfirmarEliminar").modal("show");
        return;
    }

    if (modalBody) {
        modalBody.innerHTML = "Cargando preview de impacto...";
    }

    fetch(construirUrlEliminar(admisionIdEliminar, identifier, true), {
        method: "DELETE",
        headers: { "X-CSRFToken": CSRF_TOKEN }
    })
        .then((response) => response.json())
        .then((data) => {
            if (modalBody) {
                modalBody.innerHTML = data.success
                    ? renderizarPreview(data.preview)
                    : "No se pudo obtener el preview de impacto.";
            }
        })
        .catch(() => {
            if (modalBody) {
                modalBody.textContent = "No se pudo obtener el preview de impacto.";
            }
        })
        .finally(() => {
            $("#modalConfirmarEliminar").modal("show");
        });
}

const botonConfirmarEliminar = document.getElementById("btnConfirmarEliminar");
if (botonConfirmarEliminar) {
    botonConfirmarEliminar.addEventListener("click", function () {
        eliminarArchivo(admisionIdEliminar);
    });
}

function eliminarArchivo(admisionId) {
    const rowId = documentacionIdEliminar !== null
        ? String(documentacionIdEliminar)
        : (archivoIdEliminar !== null ? `custom-${archivoIdEliminar}` : null);
    const fila = rowId ? document.getElementById(`fila-${rowId}`) : null;
    const esPersonalizado = fila && fila.dataset.personalizado === PERSONALIZED_FLAG;

    let identifier = documentacionIdEliminar !== null ? documentacionIdEliminar : archivoIdEliminar;
    if (identifier === null) {
        return;
    }

    const url = construirUrlEliminar(admisionId, identifier, false);

    const removeObservationRows = (...ids) => {
        ids.filter(Boolean).forEach((id) => {
            const obsRow = document.getElementById(`fila-obs-${id}`);
            if (obsRow) {
                obsRow.remove();
            }
        });
    };

    fetch(url, {
        method: "DELETE",
        headers: {
            "X-CSRFToken": CSRF_TOKEN,
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const targetRowId = data.row_id ? String(data.row_id) : rowId;
                const archivoIdTexto = archivoIdEliminar !== null ? String(archivoIdEliminar) : null;
                removeObservationRows(targetRowId, archivoIdTexto);

                if (esPersonalizado) {
                    if (fila) {
                        fila.remove();
                    }
                } else if (fila) {
                    if (data.html && data.row_id) {
                        fila.outerHTML = data.html;
                    } else {
                        fila.remove();
                    }
                }
                $("#modalConfirmarEliminar").modal("hide");
            } else {
                alert("Error al eliminar el archivo: " + (data.error || ""));
            }
        })
        .catch(error => console.error("Error al eliminar:", error));
}
