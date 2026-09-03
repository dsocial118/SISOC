// Gestión de comentarios técnicos en legajos

function escapeHtml(value = "") {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

document.addEventListener('DOMContentLoaded', function() {
    // Cargar comentarios al abrir detalle del legajo
    document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const target = this.getAttribute('data-bs-target');
            const match = target.match(/detalle-(\d+)-/);
            if (match) {
                const legajoId = match[1];
                cargarComentarios(legajoId);
            }
        });
    });

    // Enviar nuevo comentario
    document.addEventListener('submit', function(e) {
        if (e.target.id === 'form-agregar-comentario') {
            e.preventDefault();
            enviarComentario(e.target);
        }
    });

    inicializarFormularioTecnico();
});

/* ===== Formulario estructurado de comentario técnico ===== */

// El campo Observaciones sólo aparece cuando la respuesta es "Sí", y el cuadro
// de redacción libre sólo cuando la observación elegida es "Otros".
function inicializarFormularioTecnico() {
    const selTipo = document.getElementById('comentario-tipo-documento');
    const selTiene = document.getElementById('comentario-tiene-observaciones');
    const selObs = document.getElementById('comentario-observacion');
    if (!selTipo || !selTiene || !selObs) return;

    selTipo.addEventListener('change', () => {
        poblarObservaciones(selTipo.value);
        actualizarVisibilidadTecnico();
    });
    selTiene.addEventListener('change', actualizarVisibilidadTecnico);
    selObs.addEventListener('change', actualizarVisibilidadTecnico);
}

function observacionesDe(tipo) {
    const catalogo = window.CATALOGO_COMENTARIOS_TECNICOS || {};
    return catalogo[tipo] || [];
}

function poblarObservaciones(tipo) {
    const selObs = document.getElementById('comentario-observacion');
    if (!selObs) return;

    selObs.innerHTML = '<option value="">Seleccioná una observación…</option>';
    observacionesDe(tipo).forEach(obs => {
        const option = document.createElement('option');
        option.value = obs.codigo;
        option.textContent = obs.texto;
        if (obs.libre) option.dataset.libre = '1';
        selObs.appendChild(option);
    });
}

function actualizarVisibilidadTecnico() {
    const selTiene = document.getElementById('comentario-tiene-observaciones');
    const selObs = document.getElementById('comentario-observacion');
    const wrapObs = document.getElementById('comentario-observacion-wrapper');
    const wrapLibre = document.getElementById('comentario-libre-wrapper');
    if (!selTiene || !selObs || !wrapObs || !wrapLibre) return;

    const tieneObservaciones = selTiene.value === 'si';
    wrapObs.classList.toggle('d-none', !tieneObservaciones);
    selObs.required = tieneObservaciones;
    if (!tieneObservaciones) selObs.value = '';

    const opcion = selObs.selectedOptions[0];
    const esLibre = tieneObservaciones && opcion?.dataset.libre === '1';
    const textarea = document.getElementById('comentario-observacion-libre');
    wrapLibre.classList.toggle('d-none', !esLibre);
    if (textarea) {
        textarea.required = esLibre;
        if (!esLibre) textarea.value = '';
    }
}

function resetFormularioTecnico(form) {
    form.reset();
    poblarObservaciones('');
    actualizarVisibilidadTecnico();
}

function cargarComentarios(legajoId) {
    const expedienteId = document.querySelector('meta[name="expediente-id"]')?.content;
    if (!expedienteId) return;

    const url = `/celiaquia/expedientes/${expedienteId}/legajos/${legajoId}/comentarios/`;
    const container = document.getElementById(`comentarios-list-${legajoId}`);

    if (!container || container.dataset.loaded === 'true') return;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                mostrarComentarios(legajoId, data.comentarios);
                container.dataset.loaded = 'true';
            }
        })
        .catch(error => console.error('Error cargando comentarios:', error));
}

// Encabezado de un comentario técnico: tipo de documento y si tiene
// observaciones. Para los comentarios libres previos no aplica.
function encabezadoTecnico(comentario) {
    if (!comentario.es_comentario_tecnico) return '';

    const tipo = escapeHtml(comentario.tipo_documento_display || '');
    const badgeTipo = `<span class="badge bg-info text-dark">${tipo}</span>`;
    const badgeObs = comentario.tiene_observaciones
        ? '<span class="badge bg-warning text-dark">Con observaciones</span>'
        : '<span class="badge bg-secondary">Sin observaciones</span>';
    return ` ${badgeTipo} ${badgeObs}`;
}

function mostrarComentarios(legajoId, comentarios) {
    const container = document.getElementById(`comentarios-list-${legajoId}`);
    if (!container) return;

    if (comentarios.length === 0) {
        container.innerHTML = '<p class="text-muted small">Sin comentarios técnicos</p>';
        return;
    }

    container.innerHTML = comentarios.map(c => {
        const usuario = escapeHtml(c.usuario || "");
        const fecha = escapeHtml(c.fecha || "");
        const texto = escapeHtml(c.texto || "");
        const archivoUrl = c.archivo_url ? escapeHtml(encodeURI(c.archivo_url)) : "";
        let bgColor = c.es_provincia ? 'rgba(13, 110, 253, .1)' : 'rgba(25, 135, 84, .1)';
        let borderColor = c.es_provincia ? 'rgba(13, 110, 253, .3)' : 'rgba(25, 135, 84, .3)';
        const badge = c.es_provincia ? '<span class="badge bg-primary">Provincia</span>' : '<span class="badge bg-success">Técnico</span>';
        // Comentario interno (solo Nación lo recibe del backend): se resalta.
        let internoBadge = '';
        if (c.es_interno) {
            bgColor = 'rgba(33, 37, 41, .08)';
            borderColor = 'rgba(33, 37, 41, .35)';
            internoBadge = ' <span class="badge bg-dark"><i class="fas fa-lock"></i> Interno</span>';
        } else if (c.publicado_en) {
            internoBadge = ` <span class="badge bg-light text-dark" title="Publicado a la provincia el ${escapeHtml(c.publicado_en)}"><i class="fas fa-share"></i> Publicado</span>`;
        }

        // En un comentario técnico sin observaciones el cuerpo repetiría lo
        // que ya dice el badge, así que se omite.
        const sinObservaciones = c.es_comentario_tecnico && c.tiene_observaciones === false;

        return `
        <div class="comentario-item mb-2 p-2 rounded" style="background:${bgColor}; border:1px solid ${borderColor}">
            <div class="d-flex justify-content-between align-items-start mb-1">
                <small class="text-muted"><i class="fas fa-user"></i> ${usuario} ${badge}${internoBadge}${encabezadoTecnico(c)}</small>
                <small class="text-muted">${fecha}</small>
            </div>
            ${sinObservaciones ? '' : `<p class="mb-1 small">${texto}</p>`}
            ${c.tiene_archivo ? `<a href="${archivoUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-outline-secondary"><i class="fas fa-paperclip"></i> Ver archivo</a>` : ''}
        </div>
    `;
    }).join('');
}

function enviarComentario(form) {
    const formData = new FormData(form);
    const legajoId = form.dataset.legajoId;
    const expedienteId = document.querySelector('meta[name="expediente-id"]')?.content;

    const url = `/celiaquia/expedientes/${expedienteId}/legajos/${legajoId}/comentarios/crear/`;
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // El formulario vuelve a estar disponible para otro comentario.
            resetFormularioTecnico(form);
            // Cerrar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalAgregarComentario'));
            if (modal) modal.hide();
            // Recargar comentarios
            const container = document.getElementById(`comentarios-list-${legajoId}`);
            if (container) {
                container.dataset.loaded = 'false';
                cargarComentarios(legajoId);
            }
            // Mostrar mensaje
            mostrarAlerta('success', data.message);
        } else {
            mostrarAlerta('danger', data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarAlerta('danger', 'Error al agregar comentario');
    });
}

function mostrarAlerta(tipo, mensaje) {
    const alertContainer = document.getElementById('expediente-alerts');
    if (!alertContainer) return;

    const alert = document.createElement('div');
    alert.className = `alert alert-${tipo} alert-dismissible fade show`;
    alert.innerHTML = `
        ${escapeHtml(mensaje)}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertContainer.appendChild(alert);

    setTimeout(() => alert.remove(), 5000);
}

// Preparar modal al abrirlo
document.addEventListener('show.bs.modal', function(e) {
    if (e.target.id === 'modalAgregarComentario') {
        const button = e.relatedTarget;
        const legajoId = button.getAttribute('data-legajo-id');
        const form = document.getElementById('form-agregar-comentario');
        if (form) {
            form.dataset.legajoId = legajoId;
            resetFormularioTecnico(form);
        }
    }
});
