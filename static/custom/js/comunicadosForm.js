/**
 * COMUNICADOS FORM - JAVASCRIPT
 * Manejo de archivos adjuntos múltiples
 */

document.addEventListener("DOMContentLoaded", function () {
    // Array para almacenar todos los archivos seleccionados
    let selectedFiles = [];

    const addFilesBtn = document.getElementById("addFilesBtn");
    const archivosInput = document.getElementById("archivosInput");
    const selectedFilesInfo = document.getElementById("selectedFilesInfo");
    const fileCount = document.getElementById("fileCount");
    const filePreviewContainer = document.getElementById("filePreviewContainer");

    if (addFilesBtn && archivosInput) {
        // Event listener para el botón de agregar archivos
        addFilesBtn.addEventListener("click", function () {
            archivosInput.click();
        });

        // Event listener para cuando se seleccionan archivos
        archivosInput.addEventListener("change", function () {
            const files = Array.from(this.files);

            // Concatenar archivos en lugar de reemplazar
            selectedFiles = selectedFiles.concat(files);

            // Actualizar la vista
            updateFileDisplay();
            updateFileInput();
        });

        function updateFileDisplay() {
            // Mostrar contador
            if (selectedFiles.length > 0) {
                selectedFilesInfo?.classList.remove("d-none");
                if (fileCount) fileCount.textContent = selectedFiles.length;
            } else {
                selectedFilesInfo?.classList.add("d-none");
            }

            // Limpiar contenedor de vistas previas
            if (filePreviewContainer) {
                filePreviewContainer.innerHTML = "";

                // Mostrar cada archivo
                selectedFiles.forEach((file, index) => {
                    const previewDiv = document.createElement("div");
                    previewDiv.className = "archivo-preview-item d-flex align-items-center justify-content-between p-2 mb-2 border rounded";
                    previewDiv.setAttribute("data-index", index);

                    // Icono según tipo de archivo
                    let iconClass = "fas fa-file";
                    if (file.type.startsWith("image/")) {
                        iconClass = "fas fa-file-image text-primary";
                    } else if (file.type.includes("pdf")) {
                        iconClass = "fas fa-file-pdf text-danger";
                    } else if (file.type.includes("word") || file.name.endsWith(".doc") || file.name.endsWith(".docx")) {
                        iconClass = "fas fa-file-word text-primary";
                    } else if (file.type.includes("excel") || file.name.endsWith(".xls") || file.name.endsWith(".xlsx")) {
                        iconClass = "fas fa-file-excel text-success";
                    }

                    previewDiv.innerHTML = `
                        <div class="d-flex align-items-center">
                            <i class="${iconClass} me-2"></i>
                            <div>
                                <div class="fw-bold small">${file.name}</div>
                                <div class="text-muted small">${formatFileSize(file.size)}</div>
                            </div>
                        </div>
                        <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeFile(${index})" title="Eliminar">
                            <i class="fas fa-times"></i>
                        </button>
                    `;

                    filePreviewContainer.appendChild(previewDiv);
                });
            }
        }

        function formatFileSize(bytes) {
            if (bytes === 0) return "0 Bytes";
            const k = 1024;
            const sizes = ["Bytes", "KB", "MB", "GB"];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
        }

        function updateFileInput() {
            try {
                const dt = new DataTransfer();
                selectedFiles.forEach((file) => {
                    if (file && file instanceof File) {
                        dt.items.add(file);
                    }
                });
                archivosInput.files = dt.files;
            } catch (error) {
                // Silently fail - some browsers don't support DataTransfer
            }
        }

        // Función global para eliminar archivo
        window.removeFile = function (index) {
            if (index >= 0 && index < selectedFiles.length) {
                selectedFiles.splice(index, 1);
                updateFileDisplay();
                updateFileInput();
            }
        };

        const comunicadoForm = document.querySelector('form[enctype="multipart/form-data"]');
        if (comunicadoForm) {
            comunicadoForm.addEventListener("submit", function (e) {
                if (selectedFiles.length > 0) {
                    e.preventDefault();
                    e.stopPropagation();

                    const formData = new FormData(comunicadoForm);
                    formData.delete("archivos_adjuntos");

                    selectedFiles.forEach((file) => {
                        formData.append("archivos_adjuntos", file);
                    });

                    fetch(comunicadoForm.action || window.location.href, {
                        method: "POST",
                        body: formData,
                        redirect: "follow",
                    })
                        .then((response) => {
                            if (response.redirected) {
                                window.location.href = response.url;
                            } else if (response.ok) {
                                return response.text().then((text) => {
                                    if (text.includes("invalid-feedback") || text.includes("errorlist")) {
                                        document.open();
                                        document.write(text);
                                        document.close();
                                    } else {
                                        window.location.reload();
                                    }
                                });
                            } else {
                                alert("Error al guardar el comunicado");
                            }
                        })
                        .catch(() => {
                            alert("Error al enviar el formulario");
                        });

                    return false;
                }
            }, true);
        }
    }
});
