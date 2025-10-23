// Manejo de registros erróneos
document.addEventListener('DOMContentLoaded', function() {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    
    // Filtrar localidades por municipio
    document.querySelectorAll('.select-municipio').forEach(selectMunicipio => {
        const registroId = selectMunicipio.dataset.registroId;
        const selectLocalidad = document.querySelector(`.select-localidad[data-registro-id="${registroId}"]`);
        
        if (!selectLocalidad) return;
        
        // Guardar todas las opciones de localidad
        const todasLocalidades = Array.from(selectLocalidad.options).slice(1); // Excluir "Seleccionar..."
        
        // Filtrar al cambiar municipio
        selectMunicipio.addEventListener('change', function() {
            const municipioId = this.value;
            
            // Limpiar select de localidad
            selectLocalidad.innerHTML = '<option value="">Seleccionar...</option>';
            
            if (!municipioId) {
                // Si no hay municipio, mostrar todas
                todasLocalidades.forEach(opt => {
                    selectLocalidad.appendChild(opt.cloneNode(true));
                });
            } else {
                // Filtrar por municipio
                todasLocalidades.forEach(opt => {
                    if (opt.dataset.municipio === municipioId) {
                        selectLocalidad.appendChild(opt.cloneNode(true));
                    }
                });
            }
        });
        
        // Filtrar inicialmente si hay municipio seleccionado
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
                    
                    // Actualizar el botón de confirmar envío si no quedan errores
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
    
    // Guardar automáticamente al cambiar campos
    document.querySelectorAll('.form-editar-error').forEach(form => {
        const registroId = form.dataset.registroId;
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            input.addEventListener('change', function() {
                guardarRegistro(form, registroId);
            });
        });
    });
    
    function guardarRegistro(form, registroId) {
        const urlTemplate = document.querySelector('meta[name="actualizar-error-url-template"]')?.content;
        if (!urlTemplate) return;
        
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
                // Mostrar indicador visual de guardado
                const row = document.querySelector(`.registro-erroneo-row[data-registro-id="${registroId}"]`);
                if (row) {
                    row.style.borderLeft = '4px solid #28a745';
                    setTimeout(() => {
                        row.style.borderLeft = '4px solid #dc3545';
                    }, 1000);
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
    
    // Función auxiliar para actualizar el estado del botón de confirmar envío
    function actualizarBotonConfirmarEnvio() {
        const registrosRestantes = document.querySelectorAll('.registro-erroneo-row').length;
        const btnConfirm = document.getElementById('btn-confirm');
        
        if (btnConfirm) {
            if (registrosRestantes === 0) {
                btnConfirm.disabled = false;
                btnConfirm.className = 'btn btn-success';
                btnConfirm.innerHTML = 'Confirmar Envío';
                btnConfirm.removeAttribute('title');
            } else {
                btnConfirm.disabled = true;
                btnConfirm.className = 'btn btn-secondary';
                btnConfirm.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Confirmar Envío (${registrosRestantes} errores)`;
                btnConfirm.setAttribute('title', 'No se puede enviar mientras haya registros con errores');
            }
        }
    }
    
    // Eliminar registro erróneo
    document.querySelectorAll('.btn-eliminar-error').forEach(btn => {
        btn.addEventListener('click', function() {
            mostrarModalConfirmacion('¿Está seguro de eliminar este registro?', () => {
                eliminarRegistro(this.dataset.registroId);
            });
        });
    });
    
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
                    const titulo = document.querySelector('h5:contains("Registros con Errores")');
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