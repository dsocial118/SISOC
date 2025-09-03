function actualizarEstado(selectElement) {
    const estado = selectElement.value;
    const documentoId = selectElement.dataset.documentoId;
    const admisionId = selectElement.dataset.admisionId;
    const url = selectElement.dataset.url;

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrfToken,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            estado: estado,
            documento_id: documentoId,
            admision_id: admisionId
        })
    })
    .then(response => response.json())
    .then(data => {
        const td = document.getElementById(`estado-${documentoId}`);

        if (!data.success) {
            alert("Error: " + data.error);
            return;
        }

        const nuevoEstado = data.nuevo_estado;
        const grupo = data.grupo_usuario;

        // Mostrar toast de éxito
        const toastEl = document.getElementById("toastEstadoExito");
        const toast = new bootstrap.Toast(toastEl);
        toast.show();

        // Si el estado es Aceptado → solo texto verde
        if (nuevoEstado === "Aceptado") {
            td.innerHTML = `<span class="ps-3 text-success">${nuevoEstado}</span>`;
            return;
        }

        // Si es Pendiente → solo texto plano
        if (nuevoEstado === "Pendiente") {
            td.innerHTML = `<span class="ps-3">${nuevoEstado}</span>`;
            return;
        }

        // Si es "A Validar Abogado"
        if (nuevoEstado === "A Validar Abogado") {
            if (grupo === "Tecnico Comedor") {
                td.innerHTML = `<span class="ps-3">${nuevoEstado}</span>`;
            } else if (grupo === "Abogado Dupla") {
                td.innerHTML = `
                    <select class="form-control"
                            onchange="actualizarEstado(this)"
                            data-admision-id="${admisionId}"
                            data-documento-id="${documentoId}"
                            data-url="${url}">
                        <option selected>Elegir opcion</option>
                        <option value="Aceptado">Aceptado</option>
                        <option value="Rectificar">Rectificar</option>
                    </select>
                `;
            }
            return;
        }

        // En cualquier otro caso: solo Tecnico Comedor ve el select
        if (grupo === "Tecnico Comedor") {
            td.innerHTML = `
                <select class="form-control"
                        onchange="actualizarEstado(this)"
                        data-admision-id="${admisionId}"
                        data-documento-id="${documentoId}"
                        data-url="${url}">
                    <option value="validar" ${nuevoEstado === "validar" ? "selected" : ""}>A Validar</option>
                    <option value="A Validar Abogado" ${nuevoEstado === "A Validar Abogado" ? "selected" : ""}>A Validar Abogado</option>
                    <option value="Rectificar" ${nuevoEstado === "Rectificar" ? "selected" : ""}>Rectificar</option>
                </select>
            `;
        } else {
            td.innerHTML = `<span class="ps-3">${nuevoEstado}</span>`;
        }
    })
    .catch(error => {
        console.error("Error al actualizar estado:", error);
        alert("Ocurrió un error al actualizar el estado.");
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
        if (numeroGDE) {
            displayDiv.innerHTML = `
                <span class="text-success fw-bold">${numeroGDE}</span>
                <i class="bi bi-pencil-square ms-2 text-muted" style="cursor: pointer;" title="Editar número GDE"></i>
            `;
        } else {
            displayDiv.innerHTML = `
                <span class="text-muted">Sin número GDE</span>
                <i class="bi bi-plus-circle ms-2 text-primary" style="cursor: pointer;" title="Agregar número GDE"></i>
            `;
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
