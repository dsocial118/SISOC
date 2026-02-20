// Manejo de registros erróneos
document.addEventListener('DOMContentLoaded', function() {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    
    // Filtrar localidades por municipio
    document.querySelectorAll('.select-municipio').forEach(selectMunicipio => {
        const registroId = selectMunicipio.dataset.registroId;
        const selectLocalidad = document.querySelector(`.select-localidad[data-registro-id="${registroId}"]`);
        
        if (!selectLocalidad) return;
        
        const todasLocalidades = Array.from(selectLocalidad.options).slice(1);
        
        selectMunicipio.addEventListener('change', function() {
            const municipioId = this.value;
            selectLocalidad.innerHTML = '<option value="">Seleccionar...</option>';
            
            if (!municipioId) {
                todasLocalidades.forEach(opt => {
                    selectLocalidad.appendChild(opt.cloneNode(true));
                });
            } else {
                todasLocalidades.forEach(opt => {
                    if (opt.dataset.municipio === municipioId) {
                        selectLocalidad.appendChild(opt.cloneNode(true));
                    }
                });
            }
        });
        
        if (selectMunicipio.value) {
            selectMunicipio.dispatchEvent(new Event('change'));
        }
    });
    
    // Reprocesar todos los registros erróneos
    const btnReprocesar = document.getElementById('btn-reprocesar-errores');
    const modalConfirmar = document.getElementById('modalConfirmarReprocesar');
    const btnConfirmarReprocesar = document.getElementById('btn-confirmar-reprocesar');
    
    if (btnReprocesar && modalConfirmar) {
        btnReprocesar.addEventListener('click', function() {
            const modal = new bootstrap.Modal(modalConfirmar);
            modal.show();
        });
    }
    
    if (btnConfirmarReprocesar) {
        btnConfirmarReprocesar.addEventListener('click', function() {
            const url = document.querySelector('meta[name="reprocesar-errores-url"]')?.content;
            if (!url) return;
            
            const modal = bootstrap.Modal.getInstance(modalConfirmar);
            modal.hide();
            
            btnReprocesar.disabled = true;
            btnReprocesar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    let mensaje = `Se crearon ${data.creados} legajos correctamente.`;
                    if (data.errores > 0) {
                        mensaje += ` ${data.errores} registros aún tienen errores.`;
                    }
                    
                    if (data.registros_restantes === 0) {
                        const btnConfirm = document.getElementById('btn-confirm');
                        if (btnConfirm) {
                            btnConfirm.disabled = false;
                            btnConfirm.className = 'btn btn-success';
                            btnConfirm.innerHTML = 'Confirmar Envío';
                            btnConfirm.removeAttribute('title');
                        }
                    }
                    
                    showAlert('success', mensaje);
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showAlert('danger', 'Error: ' + (data.error || 'Error desconocido'));
                    btnReprocesar.disabled = false;
                    btnReprocesar.innerHTML = '<i class="fas fa-sync"></i> Reprocesar Todos';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('danger', 'Error al reprocesar registros');
                btnReprocesar.disabled = false;
                btnReprocesar.innerHTML = '<i class="fas fa-sync"></i> Reprocesar Todos';
            });
        });
    }
    
    // Guardar automáticamente al cambiar campos (con debounce)
    const saveTimers = {};
    document.querySelectorAll('.form-editar-error').forEach(form => {
        const registroId = form.dataset.registroId;
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            input.addEventListener('change', function() {
                clearTimeout(saveTimers[registroId]);
                saveTimers[registroId] = setTimeout(() => {
                    guardarRegistro(form, registroId);
                }, 500);
            });
        });
    });
    
    function guardarRegistro(form, registroId) {
        const urlTemplate = document.querySelector('meta[name="actualizar-error-url-template"]')?.content;
        if (!urlTemplate) return;
        
        const apellido = (form.querySelector('input[name="apellido"]')?.value || '').trim();
        const nombre = (form.querySelector('input[name="nombre"]')?.value || '').trim();
        const documento = (form.querySelector('input[name="documento"]')?.value || '').trim();
        const fecha_nacimiento = (form.querySelector('input[name="fecha_nacimiento"]')?.value || '').trim();
        const sexo = (form.querySelector('select[name="sexo"]')?.value || '').trim();
        const nacionalidad = (form.querySelector('select[name="nacionalidad"]')?.value || '').trim();
        const telefono = (form.querySelector('input[name="telefono"]')?.value || '').trim();
        const email = (form.querySelector('input[name="email"]')?.value || '').trim();
        const calle = (form.querySelector('input[name="calle"]')?.value || '').trim();
        const altura = (form.querySelector('input[name="altura"]')?.value || '').trim();
        const municipio = (form.querySelector('select[name="municipio"]')?.value || '').trim();
        const localidad = (form.querySelector('select[name="localidad"]')?.value || '').trim();
        
        if (!apellido || !nombre || !documento || !fecha_nacimiento || !sexo || !nacionalidad || !telefono || !email || !calle || !altura || !municipio || !localidad) {
            return;
        }
        
        if (telefono.length < 8) {
            return;
        }
        
        const apellido_responsable = (form.querySelector('input[name="apellido_responsable"]')?.value || '').trim();
        const nombre_responsable = (form.querySelector('input[name="nombre_responsable"]')?.value || '').trim();
        const documento_responsable = (form.querySelector('input[name="documento_responsable"]')?.value || '').trim();
        const email_responsable = (form.querySelector('input[name="email_responsable"]')?.value || '').trim();
        const tiene_responsable = apellido_responsable || nombre_responsable || documento_responsable;
        
        if (tiene_responsable && (!apellido_responsable || !nombre_responsable || !documento_responsable || !email_responsable)) {
            return;
        }
        
        const url = urlTemplate.replace('/0/', `/${registroId}/`);
        
        const formData = new FormData(form);
        const datos = {};
        formData.forEach((value, key) => {
            if (value) datos[key] = value;
        });
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datos)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const row = document.querySelector(`.registro-erroneo-row[data-registro-id="${registroId}"]`);
                if (row) {
                    row.style.borderLeft = '4px solid #28a745';
                    setTimeout(() => {
                        row.style.borderLeft = '4px solid #dc3545';
                    }, 1000);
                }
            } else {
                showAlert('danger', 'Error: ' + (data.error || 'Error desconocido'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('danger', 'Error al guardar registro');
        });
    }
    
    // Eliminar registro erróneo
    document.querySelectorAll('.btn-eliminar-error').forEach(btn => {
        btn.addEventListener('click', async function() {
            const registroId = this.dataset.registroId;
            const mensajePreview = await obtenerMensajePreviewEliminar(registroId);
            mostrarModalConfirmacion(mensajePreview, () => {
                eliminarRegistro(registroId);
            });
        });
    });

    async function obtenerMensajePreviewEliminar(registroId) {
        const urlTemplate = document.querySelector('meta[name="eliminar-error-url-template"]')?.content;
        if (!urlTemplate) {
            return '¿Está seguro de realizar la baja lógica de este registro?';
        }
        const url = urlTemplate.replace('/0/', `/${registroId}/`);
        const body = new URLSearchParams();
        body.append('preview', '1');
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: body.toString()
            });
            const data = await response.json();
            if (!response.ok || !data.success || !data.preview) {
                return '¿Está seguro de realizar la baja lógica de este registro?';
            }
            const desglose = (data.preview.desglose_por_modelo || [])
                .map((item) => `- ${item.modelo}: ${item.cantidad}`)
                .join('<br>');
            return `
                Se aplicará una baja lógica en cascada.<br>
                <strong>Total afectados:</strong> ${data.preview.total_afectados}<br>
                ${desglose || '-'}
            `;
        } catch (error) {
            console.error('Error obteniendo preview de eliminación:', error);
            return '¿Está seguro de realizar la baja lógica de este registro?';
        }
    }
    
    function eliminarRegistro(registroId) {
        const urlTemplate = document.querySelector('meta[name="eliminar-error-url-template"]')?.content;
        if (!urlTemplate) return;
        
        const url = urlTemplate.replace('/0/', `/${registroId}/`);
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const row = document.querySelector(`.registro-erroneo-row[data-registro-id="${registroId}"]`);
                if (row) {
                    const nextRow = row.nextElementSibling;
                    row.remove();
                    if (nextRow && nextRow.classList.contains('collapse')) {
                        nextRow.remove();
                    }
                }
                
                const registrosRestantes = document.querySelectorAll('.registro-erroneo-row').length;
                if (registrosRestantes === 0) {
                    const btnConfirm = document.getElementById('btn-confirm');
                    if (btnConfirm) {
                        btnConfirm.disabled = false;
                        btnConfirm.className = 'btn btn-success';
                        btnConfirm.innerHTML = 'Confirmar Envío';
                        btnConfirm.removeAttribute('title');
                    }
                    location.reload();
                } else {
                    const titulos = document.querySelectorAll('h5');
                    const titulo = Array.from(titulos).find(h => h.textContent.includes('Registros con Errores'));
                    if (titulo) {
                        titulo.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Registros con Errores (${registrosRestantes})`;
                    }
                    
                    const btnConfirm = document.getElementById('btn-confirm');
                    if (btnConfirm && btnConfirm.disabled) {
                        btnConfirm.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Confirmar Envío (${registrosRestantes} errores)`;
                    }
                }
            } else {
                showAlert('danger', 'Error: ' + (data.error || 'Error desconocido'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('danger', 'Error al eliminar registro');
        });
    }
    
    function mostrarModalConfirmacion(mensaje, callback) {
        const modalHtml = `
            <div class="modal fade" id="modalConfirmacionCustom" tabindex="-1">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content" style="background-color: #2c3e50; color: #e0e0e0;">
                        <div class="modal-header" style="border-bottom: 1px solid #495057;">
                            <h5 class="modal-title">
                                <i class="fas fa-exclamation-triangle text-warning"></i> Confirmar Acción
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${mensaje}</p>
                        </div>
                        <div class="modal-footer" style="border-top: 1px solid #495057;">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-danger" id="btn-confirmar-accion">Confirmar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const modalExistente = document.getElementById('modalConfirmacionCustom');
        if (modalExistente) modalExistente.remove();
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const modal = new bootstrap.Modal(document.getElementById('modalConfirmacionCustom'));
        modal.show();
        
        document.getElementById('btn-confirmar-accion').addEventListener('click', () => {
            modal.hide();
            callback();
        });
    }
});
