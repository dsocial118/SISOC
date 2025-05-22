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
