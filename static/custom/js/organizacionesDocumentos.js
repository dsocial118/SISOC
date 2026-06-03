let orgRectificarContext = null;
let orgModalRectificarInstance = null;

function getOrganizacionDocsCsrfToken() {
    const config = document.getElementById("organizacion-documentos-config");
    return config && config.dataset ? config.dataset.csrfToken : "";
}

function orgEscapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value || "";
    return div.innerHTML;
}

function orgFormatDateForDisplay(value) {
    if (!value) {
        return "";
    }
    const parts = value.split("-");
    if (parts.length !== 3) {
        return value;
    }
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
}

function orgShowToast(kind, message) {
    const toastId = kind === "error" ? "toastOrganizacionDocsError" : "toastOrganizacionDocsExito";
    const msgId = kind === "error" ? "toastOrganizacionDocsErrorMsg" : "toastOrganizacionDocsExitoMsg";
    const toastEl = document.getElementById(toastId);
    const msgEl = document.getElementById(msgId);
    if (msgEl) {
        msgEl.textContent = message;
    }
    if (toastEl && typeof bootstrap !== "undefined") {
        new bootstrap.Toast(toastEl).show();
        return;
    }
    if (kind === "error") {
        alert(message);
    }
}

function orgBindDynamicHandlers(root) {
    root.querySelectorAll(".org-doc-open-file").forEach(function (button) {
        if (button.dataset.orgBound === "1") {
            return;
        }
        button.dataset.orgBound = "1";
        button.addEventListener("click", function () {
            const input = document.getElementById(button.dataset.fileId);
            if (input) {
                input.click();
            }
        });
    });

    root.querySelectorAll(".org-doc-file").forEach(function (input) {
        if (input.dataset.orgBound === "1") {
            return;
        }
        input.dataset.orgBound = "1";
        input.addEventListener("change", function () {
            orgUploadDocumento(input);
        });
    });

    root.querySelectorAll(".org-doc-state-select").forEach(function (select) {
        if (select.dataset.orgBound === "1") {
            return;
        }
        select.dataset.orgBound = "1";
        select.addEventListener("change", function () {
            orgHandleStateChange(select);
        });
    });

    root.querySelectorAll(".org-doc-history-toggle").forEach(function (button) {
        if (button.dataset.orgBound === "1") {
            return;
        }
        button.dataset.orgBound = "1";
        button.addEventListener("click", function () {
            const historyRow = document.getElementById(button.dataset.historyId);
            if (historyRow) {
                historyRow.classList.toggle("d-none");
            }
        });
    });

    root.querySelectorAll(".org-inline-display").forEach(function (display) {
        if (display.dataset.orgBound === "1") {
            return;
        }
        display.dataset.orgBound = "1";
        display.addEventListener("click", function () {
            orgOpenInlineEditor(display);
        });
    });

    root.querySelectorAll(".org-inline-save").forEach(function (button) {
        if (button.dataset.orgBound === "1") {
            return;
        }
        button.dataset.orgBound = "1";
        button.addEventListener("click", function () {
            const input = button.closest(".org-inline-edit").querySelector(".org-inline-input");
            if (input) {
                orgSaveInlineField(input);
            }
        });
    });

    root.querySelectorAll(".org-inline-cancel").forEach(function (button) {
        if (button.dataset.orgBound === "1") {
            return;
        }
        button.dataset.orgBound = "1";
        button.addEventListener("click", function () {
            const input = button.closest(".org-inline-edit").querySelector(".org-inline-input");
            if (input) {
                orgCloseInlineEditor(input, true);
            }
        });
    });
}

function orgReplaceDocumentRow(rowId, html) {
    if (!rowId || !html) {
        return;
    }
    const row = document.getElementById(`org-doc-row-${rowId}`);
    const historyRow = document.getElementById(`org-doc-row-${rowId}-historial`);
    if (historyRow) {
        historyRow.remove();
    }
    if (!row) {
        return;
    }
    const template = document.createElement("template");
    template.innerHTML = html.trim();
    const fragment = template.content;
    row.replaceWith(fragment);
    orgBindDynamicHandlers(document);
}

function postOrganizacionDocState(url, estado, observaciones) {
    const formData = new FormData();
    formData.append("estado", estado);
    if (observaciones) {
        formData.append("observaciones", observaciones);
    }

    return fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getOrganizacionDocsCsrfToken(),
        },
        body: formData,
    }).then(function (response) {
        return response.json().then(function (data) {
            if (!response.ok || !data.success) {
                throw new Error(data.error || "No se pudo actualizar el estado.");
            }
            return data;
        });
    });
}

function orgSubmitStateChange(select, observaciones) {
    const previousValue = select.dataset.currentValue || "";

    postOrganizacionDocState(select.dataset.url, select.value, observaciones)
        .then(function (data) {
            orgReplaceDocumentRow(data.row_id, data.html);
            orgShowToast("success", "Estado actualizado con éxito.");
        })
        .catch(function (error) {
            orgShowToast("error", error.message);
            select.value = previousValue;
        });
}

function orgHandleStateChange(select) {
    if (!select.value) {
        return;
    }

    const previousValue = select.dataset.currentValue || "";
    const requiresObservacion = select.dataset.requiresObservacion === "1";
    if (select.value === "Rectificar" && requiresObservacion) {
        orgRectificarContext = {
            selectElement: select,
            estado: select.value,
            previousValue: previousValue,
            confirmed: false,
            observaciones: "",
        };

        select.value = previousValue;

        if (orgModalRectificarInstance) {
            orgModalRectificarInstance.show();
        } else {
            const promptValue = window.prompt("Detalle el motivo de la rectificacion:") || "";
            const texto = promptValue.trim();
            if (!texto) {
                orgRectificarContext = null;
                select.value = previousValue;
                return;
            }
            orgRectificarContext = null;
            select.value = "Rectificar";
            orgSubmitStateChange(select, texto);
        }
        return;
    }

    orgSubmitStateChange(select, "");
}

function orgInitRectificarModal() {
    const modalElement = document.getElementById("orgModalObservacionRectificar");
    if (modalElement && typeof bootstrap !== "undefined") {
        orgModalRectificarInstance = new bootstrap.Modal(modalElement);
        modalElement.addEventListener("shown.bs.modal", function () {
            const textarea = document.getElementById("orgObservacionRectificar");
            if (textarea) {
                textarea.focus();
            }
        });
        modalElement.addEventListener("hidden.bs.modal", function () {
            const textarea = document.getElementById("orgObservacionRectificar");
            if (textarea) {
                textarea.value = "";
            }
            const errorLabel = document.getElementById("orgObservacionRectificarError");
            if (errorLabel) {
                errorLabel.textContent = "";
            }
            if (!orgRectificarContext) {
                return;
            }

            const context = orgRectificarContext;
            orgRectificarContext = null;
            const select = context.selectElement;
            if (!select) {
                return;
            }

            if (context.confirmed) {
                select.value = context.estado;
                orgSubmitStateChange(select, context.observaciones);
            } else {
                select.value = context.previousValue || "";
                if (select.dataset) {
                    select.dataset.currentValue = context.previousValue || "";
                }
            }
        });
    }

    const confirmarBtn = document.getElementById("orgBtnConfirmarRectificar");
    if (confirmarBtn) {
        confirmarBtn.addEventListener("click", function () {
            if (!orgRectificarContext) {
                return;
            }
            const textarea = document.getElementById("orgObservacionRectificar");
            const errorLabel = document.getElementById("orgObservacionRectificarError");
            const texto = textarea ? textarea.value.trim() : "";
            if (!texto) {
                if (errorLabel) {
                    errorLabel.textContent = "Debe completar las observaciones.";
                }
                return;
            }
            if (errorLabel) {
                errorLabel.textContent = "";
            }
            orgRectificarContext.observaciones = texto;
            orgRectificarContext.confirmed = true;
            if (orgModalRectificarInstance) {
                orgModalRectificarInstance.hide();
            }
        });
    }
}

function orgOpenInlineEditor(display) {
    const edit = document.getElementById(display.dataset.orgInlineEdit);
    const input = edit ? edit.querySelector(".org-inline-input") : null;
    if (!edit || !input) {
        return;
    }
    input.dataset.originalValue = input.value || "";
    display.classList.add("d-none");
    edit.classList.remove("d-none");
    input.focus();
    if (input.type !== "date") {
        input.select();
    }
}

function orgCloseInlineEditor(input, restoreOriginal) {
    const display = document.getElementById(input.dataset.displayId);
    const edit = document.getElementById(input.dataset.editId);
    if (restoreOriginal) {
        input.value = input.dataset.originalValue || "";
    }
    if (edit) {
        edit.classList.add("d-none");
    }
    if (display) {
        display.classList.remove("d-none");
    }
}

function orgRenderInlineDisplay(input, value) {
    const display = document.getElementById(input.dataset.displayId);
    if (!display) {
        return;
    }

    const emptyText = input.dataset.emptyText || "-";
    const displayValue = input.type === "date" ? orgFormatDateForDisplay(value) : value;
    const hasValue = Boolean(displayValue);
    const iconClass = hasValue ? "bi bi-pencil-square ms-2 text-muted" : "bi bi-plus-circle ms-2 text-primary";
    const iconTitle = hasValue ? "Editar" : "Agregar";

    display.innerHTML = hasValue
        ? `<span class="text-success fw-bold">${orgEscapeHtml(displayValue)}</span><i class="${iconClass}" title="${iconTitle}"></i>`
        : `<span class="text-muted">${orgEscapeHtml(emptyText)}</span><i class="${iconClass}" title="${iconTitle}"></i>`;
}

function orgSaveInlineField(input) {
    const value = (input.value || "").trim();
    const formData = new FormData();
    formData.append(input.dataset.field, value);

    fetch(input.dataset.url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getOrganizacionDocsCsrfToken(),
        },
        body: formData,
    })
        .then(function (response) {
            return response.json().then(function (data) {
                if (!response.ok || !data.success) {
                    throw new Error(data.error || "No se pudo guardar el valor.");
                }
                orgReplaceDocumentRow(data.row_id, data.html);
                orgShowToast(
                    "success",
                    input.dataset.field === "numero_gde"
                        ? "Número GDE actualizado con éxito."
                        : "Vencimiento actualizado con éxito."
                );
            });
        })
        .catch(function (error) {
            orgShowToast("error", error.message);
            input.value = input.dataset.originalValue || "";
        });
}

function orgUploadDocumento(input) {
    if (!input.files.length) {
        return;
    }

    const formData = new FormData();
    const vencimientoInput = document.getElementById(input.dataset.vencimientoId);
    formData.append("archivo", input.files[0]);
    if (vencimientoInput && vencimientoInput.value) {
        formData.append("fecha_vencimiento", vencimientoInput.value);
    }

    const docId = input.id.replace("org-doc-file-", "");
    const progressContainer = document.getElementById(`org-progress-container-${docId}`);
    const progressBar = document.getElementById(`org-progress-bar-${docId}`);
    if (progressContainer && progressBar) {
        progressContainer.style.display = "block";
        progressBar.style.width = "0%";
        progressBar.textContent = "0%";
    }

    const xhr = new XMLHttpRequest();
    xhr.open("POST", input.dataset.uploadUrl, true);
    xhr.setRequestHeader("X-CSRFToken", getOrganizacionDocsCsrfToken());

    xhr.upload.onprogress = function (event) {
        if (event.lengthComputable && progressBar) {
            const percent = Math.round((event.loaded / event.total) * 100);
            progressBar.style.width = `${percent}%`;
            progressBar.textContent = `${percent}%`;
        }
    };

    xhr.onload = function () {
        let data = {};
        try {
            data = JSON.parse(xhr.responseText || "{}");
        } catch (error) {
            data = {};
        }
        if (xhr.status >= 200 && xhr.status < 300 && data.success) {
            orgReplaceDocumentRow(data.row_id, data.html);
            orgShowToast("success", "Documento cargado con éxito.");
            return;
        }
        orgShowToast("error", (data && data.error) || "No se pudo subir el archivo.");
        input.value = "";
        if (progressContainer) {
            progressContainer.style.display = "none";
        }
    };

    xhr.onerror = function () {
        orgShowToast("error", "Error de red al subir el documento.");
        input.value = "";
        if (progressContainer) {
            progressContainer.style.display = "none";
        }
    };

    xhr.send(formData);
}

function orgAppendDocumentoAdicionalRow(html) {
    if (!html) {
        return;
    }
    const tbody = document.querySelector("#documentacion .documentacion-table tbody");
    if (!tbody) {
        return;
    }
    const placeholder = tbody.querySelector("td[colspan]");
    if (placeholder && placeholder.parentElement) {
        placeholder.parentElement.remove();
    }
    const template = document.createElement("template");
    template.innerHTML = html.trim();
    tbody.appendChild(template.content);
    orgBindDynamicHandlers(document);
}

function orgSubmitDocumentoAdicional() {
    const nombreInput = document.getElementById("nuevoDocOrgNombre");
    const archivoInput = document.getElementById("nuevoDocOrgArchivo");
    const vencInput = document.getElementById("nuevoDocOrgVencimiento");
    const btn = document.getElementById("btnAgregarDocOrg");
    if (!nombreInput || !archivoInput || !btn) {
        return;
    }
    const nombre = (nombreInput.value || "").trim();
    if (!nombre) {
        orgShowToast("error", "Debe indicar un nombre para el documento.");
        nombreInput.focus();
        return;
    }
    if (!archivoInput.files.length) {
        return;
    }

    const formData = new FormData();
    formData.append("nombre", nombre);
    formData.append("archivo", archivoInput.files[0]);
    if (vencInput && vencInput.value) {
        formData.append("fecha_vencimiento", vencInput.value);
    }

    const progressContainer = document.getElementById("org-doc-adicional-progress-container");
    const progressBar = document.getElementById("org-doc-adicional-progress-bar");
    if (progressContainer && progressBar) {
        progressContainer.classList.remove("d-none");
        progressBar.style.width = "0%";
        progressBar.textContent = "0%";
    }
    btn.disabled = true;

    const xhr = new XMLHttpRequest();
    xhr.open("POST", btn.dataset.url, true);
    xhr.setRequestHeader("X-CSRFToken", getOrganizacionDocsCsrfToken());

    xhr.upload.onprogress = function (event) {
        if (event.lengthComputable && progressBar) {
            const percent = Math.round((event.loaded / event.total) * 100);
            progressBar.style.width = `${percent}%`;
            progressBar.textContent = `${percent}%`;
        }
    };

    xhr.onload = function () {
        btn.disabled = false;
        if (progressContainer) {
            progressContainer.classList.add("d-none");
        }
        let data = {};
        try {
            data = JSON.parse(xhr.responseText || "{}");
        } catch (error) {
            data = {};
        }
        if (xhr.status >= 200 && xhr.status < 300 && data.success) {
            orgAppendDocumentoAdicionalRow(data.html);
            orgShowToast("success", "Documento adicional agregado con éxito.");
            nombreInput.value = "";
            archivoInput.value = "";
            if (vencInput) {
                vencInput.value = "";
            }
            return;
        }
        orgShowToast("error", (data && data.error) || "No se pudo agregar el documento.");
        archivoInput.value = "";
    };

    xhr.onerror = function () {
        btn.disabled = false;
        if (progressContainer) {
            progressContainer.classList.add("d-none");
        }
        orgShowToast("error", "Error de red al agregar el documento.");
        archivoInput.value = "";
    };

    xhr.send(formData);
}

function orgInitDocumentoAdicional() {
    const btn = document.getElementById("btnAgregarDocOrg");
    const archivoInput = document.getElementById("nuevoDocOrgArchivo");
    const nombreInput = document.getElementById("nuevoDocOrgNombre");
    if (!btn || !archivoInput) {
        return;
    }
    btn.addEventListener("click", function () {
        const nombre = nombreInput ? (nombreInput.value || "").trim() : "";
        if (!nombre) {
            orgShowToast("error", "Debe indicar un nombre para el documento.");
            if (nombreInput) {
                nombreInput.focus();
            }
            return;
        }
        archivoInput.click();
    });
    archivoInput.addEventListener("change", function () {
        if (archivoInput.files.length) {
            orgSubmitDocumentoAdicional();
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {
    orgInitRectificarModal();
    orgInitDocumentoAdicional();
    orgBindDynamicHandlers(document);
});
