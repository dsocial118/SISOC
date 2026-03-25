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
    
    const REQUIRED_FIELDS = [
        'apellido',
        'nombre',
        'documento',
        'fecha_nacimiento',
        'sexo',
        'nacionalidad',
        'municipio',
        'localidad',
        'calle',
        'altura',
        'codigo_postal',
        'apellido_responsable',
        'nombre_responsable',
        'documento_responsable',
        'fecha_nacimiento_responsable',
        'sexo_responsable',
        'domicilio_responsable',
        'localidad_responsable'
    ];

    const FIELD_LABELS = {
        apellido: 'apellido',
        nombre: 'nombre',
        documento: 'documento',
        fecha_nacimiento: 'fecha de nacimiento',
        sexo: 'sexo',
        nacionalidad: 'nacionalidad',
        municipio: 'municipio',
        localidad: 'localidad',
        calle: 'calle',
        altura: 'altura',
        codigo_postal: 'codigo postal',
        apellido_responsable: 'apellido del responsable',
        nombre_responsable: 'nombre del responsable',
        documento_responsable: 'documento del responsable',
        fecha_nacimiento_responsable: 'fecha de nacimiento del responsable',
        sexo_responsable: 'sexo del responsable',
        domicilio_responsable: 'domicilio del responsable',
        localidad_responsable: 'localidad del responsable'
    };

    function mostrarErrorValidacion(form, message) {
        if (form.dataset.validationMessage === message) return;
        form.dataset.validationMessage = message;
        showAlert('danger', message);
    }

    function limpiarErrorValidacion(form) {
        delete form.dataset.validationMessage;
    }

    function guardarRegistro(form, registroId) {
        const urlTemplate = document.querySelector('meta[name="actualizar-error-url-template"]')?.content;
        if (!urlTemplate) return;

        const url = urlTemplate.replace('/0/', `/${registroId}/`);
        const formData = new FormData(form);
        const datos = {};
        formData.forEach((value, key) => {
            datos[key] = typeof value === 'string' ? value.trim() : value;
        });

        const faltantes = REQUIRED_FIELDS.filter(field => !String(datos[field] || '').trim());
        if (faltantes.length > 0) {
            const nombres = faltantes.map(field => FIELD_LABELS[field] || field);
            mostrarErrorValidacion(
                form,
                `Faltan campos obligatorios: ${nombres.join(', ')}.`
            );
            return;
        }

        const telefono = String(datos.telefono || '').trim();
        if (telefono && telefono.length < 8) {
            mostrarErrorValidacion(form, 'El telefono debe tener al menos 8 digitos.');
            return;
        }

        const telefonoResponsable = String(datos.telefono_responsable || '').trim();
        if (telefonoResponsable && telefonoResponsable.length < 8) {
            mostrarErrorValidacion(
                form,
                'El telefono del responsable debe tener al menos 8 digitos.'
            );
            return;
        }

        limpiarErrorValidacion(form);
        
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
                limpiarErrorValidacion(form);
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
