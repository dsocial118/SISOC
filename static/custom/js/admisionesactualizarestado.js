let rectificarContext = null;
let modalRectificarInstance = null;

function escapeHtml(value) {
    if (value === null || value === undefined) {
        return '';
    }
    const div = document.createElement('div');
    div.textContent = value;
    return div.innerHTML;
}

function renderObservationInline(td, observacion, estado) {
    const existing = td.querySelector('.observacion-inline');
    if (existing) {
        existing.remove();
    }

    if (!td || (estado || '').toLowerCase() !== 'rectificar') {
        return;
    }

    const texto = (observacion || '').trim();
    if (!texto) {
        return;
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'observacion-inline mt-2 small text-danger fw-semibold';
    const contenido = escapeHtml(texto).replace(/\r?\n/g, '<br>');
    wrapper.innerHTML = `<i class="bi bi-arrow-return-right me-1"></i>Observaciones: <span class="text-dark">${contenido}</span>`;
    td.appendChild(wrapper);
}

function badgeClassForState(estado) {
    switch ((estado || '').toLowerCase()) {
        case 'rectificar':
            return 'badge bg-danger';
        case 'aceptado':
            return 'badge bg-success';
        case 'pendiente':
            return 'badge bg-secondary';
        case 'a validar':
            return 'badge bg-warning text-dark';
        case 'a validar abogado':
            return 'badge bg-primary';
        case 'Documento adjunto':
            return 'badge bg-secondary';
        default:
            return 'badge bg-secondary';
    }
}

function displayState(td, estado, observaciones) {
    td.innerHTML = '';
    const span = document.createElement('span');
    span.className = badgeClassForState(estado);
    span.textContent = estado;
    td.appendChild(span);

    if ((estado || '').toLowerCase() === 'rectificar' && observaciones) {
        renderObservationInline(td, observaciones, estado);
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const modalElement = document.getElementById("modalObservacionRectificar");
    if (modalElement) {
        modalRectificarInstance = new bootstrap.Modal(modalElement);
        modalElement.addEventListener("hidden.bs.modal", function () {
            const textarea = document.getElementById("observacionRectificar");
            if (textarea) {
                textarea.value = "";
            }
            const errorLabel = document.getElementById("observacionRectificarError");
            if (errorLabel) {
                errorLabel.textContent = "";
            }
            if (rectificarContext) {
                if (rectificarContext.confirmed) {
                    const context = rectificarContext;
                    rectificarContext = null;
                    if (context.selectElement) {
                        context.selectElement.value = context.estado;
                    }
                    actualizarEstado(context.selectElement, context.observacion);
                } else {
                    const select = rectificarContext.selectElement;
                    const previousValue = rectificarContext.previousValue || "";
                    if (select) {
                        select.value = previousValue;
                        if (select.dataset) {
                            select.dataset.currentValue = previousValue;
                        }
                    }
                    rectificarContext = null;
                }
            }
        });
    }

    const confirmarBtn = document.getElementById("btnConfirmarRectificar");
    if (confirmarBtn) {
        confirmarBtn.addEventListener("click", function () {
            if (!rectificarContext) {
                return;
            }
            const textarea = document.getElementById("observacionRectificar");
            const errorLabel = document.getElementById("observacionRectificarError");
            const texto = textarea ? textarea.value.trim() : "";
            if (!texto) {
                if (errorLabel) {
                    errorLabel.textContent = "Debe completar las observaciones.";
                } else {
                    alert("Debe completar las observaciones.");
                }
                return;
            }
            if (errorLabel) {
                errorLabel.textContent = "";
            }
            rectificarContext.observacion = texto;
            rectificarContext.confirmed = true;
            if (modalRectificarInstance) {
                modalRectificarInstance.hide();
            } else {
                const context = rectificarContext;
                rectificarContext = null;
                if (context.selectElement) {
                    context.selectElement.value = context.estado;
                }
                actualizarEstado(context.selectElement, texto);
            }
        });
    }
});

function actualizarEstado(selectElement, observacionForzada = null) {
    if (!selectElement) {
        return;
    }

    const estado = selectElement.value;
    const documentoId = selectElement.dataset.documentoId;
    const admisionId = selectElement.dataset.admisionId;
    const url = selectElement.dataset.url;
    const requiresObservacion = selectElement.dataset.requiresObservacion === "1";
    const previousValue = selectElement.dataset.currentValue || selectElement.value || "";

    if (!estado || !documentoId || !admisionId || !url) {
        return;
    }

    if (!observacionForzada && estado === "Rectificar" && requiresObservacion) {
        rectificarContext = {
            selectElement: selectElement,
            estado: estado,
            documentoId: documentoId,
            admisionId: admisionId,
            url: url,
            previousValue: previousValue,
            confirmed: false,
            observacion: null,
        };

        selectElement.value = previousValue;
        if (selectElement.dataset) {
            selectElement.dataset.currentValue = previousValue;
        }

        if (modalRectificarInstance) {
            modalRectificarInstance.show();
        } else {
            const promptValue = prompt("Detalle el motivo de la rectificacion:");
            const texto = promptValue ? promptValue.trim() : "";
            if (!texto) {
                rectificarContext = null;
                return;
            }
            rectificarContext = null;
            selectElement.value = estado;
            actualizarEstado(selectElement, texto);
        }
        return;
    }

    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfInput) {
        alert("No se encontro el token CSRF.");
        return;
    }

    const observacion = observacionForzada ? observacionForzada.trim() : null;

    const params = new URLSearchParams({
        estado: estado,
        documento_id: documentoId,
        admision_id: admisionId,
    });
    if (observacion) {
        params.append("observacion", observacion);
    }

    fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrfInput.value,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: params,
    })
        .then((response) => response.json())
        .then((data) => {
            const td = document.getElementById(`estado-${documentoId}`);

            if (!data.success) {
                alert("Error: " + (data.error || "No se pudo actualizar el estado."));
                selectElement.value = previousValue || "";
                if (selectElement.dataset) {
                    selectElement.dataset.currentValue = previousValue || "";
                }
                return;
            }

            const nuevoEstado = data.nuevo_estado;
            const grupo = data.grupo_usuario;

            if (selectElement.dataset) {
                selectElement.dataset.currentValue = nuevoEstado;
            }

            const toastEl = document.getElementById("toastEstadoExito");
            if (toastEl) {
                new bootstrap.Toast(toastEl).show();
            }

            if (!td) {
                return;
            }

            const obsRowId = `fila-obs-${documentoId}`;
            let obsRow = document.getElementById(obsRowId);
            const mainRow = document.getElementById(`fila-${documentoId}`);
            if (!obsRow && mainRow) {
                obsRow = document.createElement('tr');
                obsRow.id = obsRowId;
                obsRow.className = 'observacion-row d-none';
                const cell = document.createElement('td');
                cell.colSpan = 4;
                cell.className = 'bg-warning-subtle small ps-4';
                obsRow.appendChild(cell);
                mainRow.insertAdjacentElement('afterend', obsRow);
            }
            if (obsRow) {
                const cell = obsRow.querySelector('td');
                const debeMostrar = (nuevoEstado || '').toLowerCase() === 'rectificar' && (data.observaciones || '').trim() !== '';
                if (debeMostrar) {
                    obsRow.classList.remove('d-none');
                    if (cell) {
                        const contenido = escapeHtml(data.observaciones || '').replace(/\r?\n/g, '<br>');
                        cell.innerHTML = '<strong>Observaciones:</strong> ' + contenido;
                    }
                } else {
                    obsRow.classList.add('d-none');
                    if (cell) {
                        cell.innerHTML = '';
                    }
                }
            }

            if (nuevoEstado === "Aceptado") {
                displayState(td, nuevoEstado, data.observaciones);
                return;
            }

            if (nuevoEstado === "Pendiente") {
                displayState(td, nuevoEstado, data.observaciones);
                return;
            }

            if (nuevoEstado === "A Validar Abogado") {
                td.innerHTML = '';
                if (grupo === "Tecnico Comedor") {
                    const span = document.createElement('span');
                    span.className = 'badge bg-primary';
                    span.textContent = nuevoEstado;
                    td.appendChild(span);
                } else if (grupo === "Abogado Dupla") {
                    const select = document.createElement('select');
                    select.className = 'form-control form-control-sm mb-2';
                    select.addEventListener('change', function () { actualizarEstado(this); });
                    select.setAttribute('data-admision-id', admisionId);
                    select.setAttribute('data-documento-id', documentoId);
                    select.setAttribute('data-url', url);
                    select.setAttribute('data-requires-observacion', '1');
                    select.dataset.currentValue = 'A Validar Abogado';

                    const optionActual = document.createElement('option');
                    optionActual.value = 'A Validar Abogado';
                    optionActual.textContent = 'A Validar Abogado';
                    optionActual.selected = true;
                    select.appendChild(optionActual);

                    const optionAceptado = document.createElement('option');
                    optionAceptado.value = 'Aceptado';
                    optionAceptado.textContent = 'Aceptado';
                    select.appendChild(optionAceptado);

                    const optionRectificar = document.createElement('option');
                    optionRectificar.value = 'Rectificar';
                    optionRectificar.textContent = 'Rectificar';
                    select.appendChild(optionRectificar);

                    td.appendChild(select);
                renderObservationInline(td, data.observaciones, nuevoEstado);
                renderObservationInline(td, data.observaciones, nuevoEstado);
                }
                return;
            }

            if (grupo === "Tecnico Comedor") {
                td.innerHTML = '';
                const select = document.createElement('select');
                const baseClass = 'form-control form-control-sm mb-2';
                select.className = (nuevoEstado || '').toLowerCase() === 'rectificar'
                    ? baseClass + ' border border-danger border-2'
                    : baseClass;
                select.addEventListener('change', function () { actualizarEstado(this); });
                select.setAttribute('data-admision-id', admisionId);
                select.setAttribute('data-documento-id', documentoId);
                select.setAttribute('data-url', url);
                select.setAttribute('data-requires-observacion', '0');
                select.dataset.currentValue = nuevoEstado;

                const estadosTecnico = [
                    { value: 'Documento adjunto', label: 'Documento adjunto' },
                    { value: 'A Validar Abogado', label: 'A Validar Abogado' },
                ];
                const nuevoEstadoLower = (nuevoEstado || '').toLowerCase();
                estadosTecnico.forEach(function (item) {
                    const option = document.createElement('option');
                    option.value = item.value;
                    option.textContent = item.label;
                    option.selected = item.value.toLowerCase() === nuevoEstadoLower;
                    select.appendChild(option);
                });

                td.appendChild(select);
                return;
            }

            if ((nuevoEstado || '').toLowerCase() === 'rectificar') {
                displayState(td, nuevoEstado, data.observaciones);
                return;
            }

            td.innerHTML = '';
            const span = document.createElement('span');
            span.className = badgeClassForState(nuevoEstado);
            span.textContent = nuevoEstado;
            td.appendChild(span);
        })
        .catch((error) => {
            console.error('Error al actualizar estado:', error);
            alert('Ocurrio un error al actualizar el estado.');
            selectElement.value = previousValue || "";
            if (selectElement.dataset) {
                selectElement.dataset.currentValue = previousValue || "";
            }
        });
}



// Función para activar el modo edición
function activarEdicionGDE(documentoId) {
    const displayDiv = document.getElementById(`gde-display-${documentoId}`);
    const editDiv = document.getElementById(`gde-edit-${documentoId}`);
    const input = document.getElementById(`gde-input-${documentoId}`);
    
    if (displayDiv && editDiv && input) {
        displayDiv.classList.add('d-none');
        editDiv.classList.remove('d-none');
        input.focus();
    }
}

// Función para cancelar edición y volver a modo vista
function cancelarEdicionGDE(documentoId) {
    const displayDiv = document.getElementById(`gde-display-${documentoId}`);
    const editDiv = document.getElementById(`gde-edit-${documentoId}`);
    const input = document.getElementById(`gde-input-${documentoId}`);
    
    if (displayDiv && editDiv && input) {
        // Restaurar valor original desde el atributo data o desde la vista
        const valorOriginal = displayDiv.querySelector('span').textContent;
        if (valorOriginal !== 'Sin número GDE') {
            input.value = valorOriginal;
        } else {
            input.value = '';
        }
        
        editDiv.classList.add('d-none');
        displayDiv.classList.remove('d-none');
    }
}

// Función para guardar el número GDE
function guardarNumeroGDE(documentoId) {
    const input = document.getElementById(`gde-input-${documentoId}`);
    const numeroGDE = input ? input.value.trim() : '';
    
    actualizarNumeroGDE(documentoId, numeroGDE);
}

// Función principal de actualización (modificada)
function actualizarNumeroGDE(documentoId, numeroGDE) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch(window.URL_ACTUALIZAR_NUMERO_GDE, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrfToken,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            documento_id: documentoId,
            numero_gde: numeroGDE
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            alert("Error: " + data.error);
            // Restaurar valor anterior si hubo error
            const input = document.getElementById(`gde-input-${documentoId}`);
            if (input) {
                input.value = data.valor_anterior || '';
            }
            return;
        }

        // Mostrar toast de éxito
        const toastEl = document.getElementById("toastGDEExito");
        if (toastEl) {
            const toast = new bootstrap.Toast(toastEl);
            toast.show();
        }

        // Actualizar la vista con el nuevo valor
        actualizarVistaGDE(documentoId, data.numero_gde);
        
        // Volver a modo vista
        volverAModoVista(documentoId);
    })
    .catch(error => {
        console.error("Error al actualizar número GDE:", error);
        alert("Ocurrió un error al actualizar el número GDE.");
    });
}

// Función para actualizar la vista después de guardar
function actualizarVistaGDE(documentoId, numeroGDE) {
    const displayDiv = document.getElementById(`gde-display-${documentoId}`);
    const input = document.getElementById(`gde-input-${documentoId}`);
    
    if (displayDiv && input) {
        // Actualizar el input con el valor confirmado
        input.value = numeroGDE || '';
        
        // Actualizar el contenido de la vista
        displayDiv.innerHTML = '';
        if (numeroGDE) {
            const span = document.createElement('span');
            span.className = 'text-success fw-bold';
            span.textContent = numeroGDE;
            displayDiv.appendChild(span);
            
            const icon = document.createElement('i');
            icon.className = 'bi bi-pencil-square ms-2 text-muted';
            icon.style.cursor = 'pointer';
            icon.title = 'Editar número GDE';
            displayDiv.appendChild(icon);
        } else {
            const span = document.createElement('span');
            span.className = 'text-muted';
            span.textContent = 'Sin número GDE';
            displayDiv.appendChild(span);
            
            const icon = document.createElement('i');
            icon.className = 'bi bi-plus-circle ms-2 text-primary';
            icon.style.cursor = 'pointer';
            icon.title = 'Agregar número GDE';
            displayDiv.appendChild(icon);
        }
    }
}

// Función para volver a modo vista
function volverAModoVista(documentoId) {
    const displayDiv = document.getElementById(`gde-display-${documentoId}`);
    const editDiv = document.getElementById(`gde-edit-${documentoId}`);
    
    if (displayDiv && editDiv) {
        editDiv.classList.add('d-none');
        displayDiv.classList.remove('d-none');
    }
}

// Función legacy mantenida para compatibilidad
function actualizarNumeroGDELegacy(documentoId, numeroGDE) {
    actualizarNumeroGDE(documentoId, numeroGDE);
}

function activarEdicionConvenioNumero() {
    const displayDiv = document.getElementById("convenio-numero-display");
    const editDiv = document.getElementById("convenio-numero-edit");
    const input = document.getElementById("convenio-numero-input");

    if (displayDiv && editDiv && input) {
        displayDiv.classList.add("d-none");
        editDiv.classList.remove("d-none");
        input.focus();
        input.select();
    }
}

function cancelarEdicionConvenioNumero() {
    const displayDiv = document.getElementById("convenio-numero-display");
    const editDiv = document.getElementById("convenio-numero-edit");
    const input = document.getElementById("convenio-numero-input");

    if (displayDiv && editDiv && input) {
        const valorActual = displayDiv.querySelector("span")?.textContent || "";
        input.value = valorActual === "Sin numero de convenio" ? "" : valorActual;
        editDiv.classList.add("d-none");
        displayDiv.classList.remove("d-none");
    }
}

function guardarConvenioNumero() {
    const input = document.getElementById("convenio-numero-input");
    const numero = input ? input.value.trim() : "";
    actualizarConvenioNumero(numero);
}

function actualizarConvenioNumero(numero) {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfInput) {
        alert("No se encontro el token CSRF.");
        return;
    }

    if (!window.URL_ACTUALIZAR_CONVENIO_NUMERO || !window.ADMISION_ID) {
        alert("No se pudo actualizar el numero de convenio.");
        return;
    }

    fetch(window.URL_ACTUALIZAR_CONVENIO_NUMERO, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrfInput.value,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            admision_id: window.ADMISION_ID,
            convenio_numero: numero,
        }),
    })
        .then((response) => response.json())
        .then((data) => {
            if (!data.success) {
                const toastEl = document.getElementById("toastConvenioNumeroError");
                const msgEl = document.getElementById("toastConvenioNumeroErrorMsg");
                if (msgEl) {
                    msgEl.textContent = data.error || "No se pudo actualizar el numero de convenio.";
                }
                if (toastEl) {
                    new bootstrap.Toast(toastEl).show();
                } else {
                    alert("Error: " + (data.error || "No se pudo actualizar el numero de convenio."));
                }
                return;
            }
            const toastEl = document.getElementById("toastConvenioNumeroExito");
            if (toastEl) {
                new bootstrap.Toast(toastEl).show();
            }
            actualizarVistaConvenioNumero(data.convenio_numero);
            volverAModoVistaConvenioNumero();
        })
        .catch((error) => {
            console.error("Error al actualizar numero de convenio:", error);
            const toastEl = document.getElementById("toastConvenioNumeroError");
            const msgEl = document.getElementById("toastConvenioNumeroErrorMsg");
            if (msgEl) {
                msgEl.textContent = "Ocurrio un error al actualizar el numero de convenio.";
            }
            if (toastEl) {
                new bootstrap.Toast(toastEl).show();
            } else {
                alert("Ocurrio un error al actualizar el numero de convenio.");
            }
        });
}

function actualizarVistaConvenioNumero(numero) {
    const displayDiv = document.getElementById("convenio-numero-display");
    const input = document.getElementById("convenio-numero-input");

    if (input) {
        input.value = numero === null || numero === undefined ? "" : numero;
    }

    if (!displayDiv) {
        return;
    }

    const hasValue = numero !== null && numero !== undefined && numero !== "";
    displayDiv.innerHTML = "";
    if (hasValue) {
        const span = document.createElement("span");
        span.className = "text-success fw-bold";
        span.textContent = String(numero);
        displayDiv.appendChild(span);

        const icon = document.createElement("i");
        icon.className = "bi bi-pencil-square ms-2 text-muted";
        icon.style.cursor = "pointer";
        icon.title = "Editar numero de convenio";
        displayDiv.appendChild(icon);
    } else {
        const span = document.createElement("span");
        span.className = "text-muted";
        span.textContent = "Sin numero de convenio";
        displayDiv.appendChild(span);

        const icon = document.createElement("i");
        icon.className = "bi bi-plus-circle ms-2 text-primary";
        icon.style.cursor = "pointer";
        icon.title = "Agregar numero de convenio";
        displayDiv.appendChild(icon);
    }
}

function volverAModoVistaConvenioNumero() {
    const displayDiv = document.getElementById("convenio-numero-display");
    const editDiv = document.getElementById("convenio-numero-edit");

    if (displayDiv && editDiv) {
        editDiv.classList.add("d-none");
        displayDiv.classList.remove("d-none");
    }
}

window.activarEdicionConvenioNumero = activarEdicionConvenioNumero;
window.cancelarEdicionConvenioNumero = cancelarEdicionConvenioNumero;
window.guardarConvenioNumero = guardarConvenioNumero;

