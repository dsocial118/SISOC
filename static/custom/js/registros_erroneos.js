// Manejo de registros erróneos
document.addEventListener('DOMContentLoaded', function() {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

    function obtenerCamposInvalidos(form) {
        return (form.dataset.invalidFields || '')
            .split(',')
            .map(item => item.trim())
            .filter(Boolean);
    }

    function limpiarResaltadoCampos(form) {
        form.querySelectorAll('.field-error-soft').forEach(field => {
            field.classList.remove('field-error-soft');
            field.removeAttribute('aria-invalid');
        });
    }

    function aplicarResaltadoCampos(form, invalidFields = []) {
        limpiarResaltadoCampos(form);
        invalidFields.forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (!field) return;
            field.classList.add('field-error-soft');
            field.setAttribute('aria-invalid', 'true');
        });
    }
    
    // Filtrar y sincronizar localidades/municipios
    document.querySelectorAll('.select-municipio').forEach(selectMunicipio => {
        const registroId = selectMunicipio.dataset.registroId;
        const selectLocalidad = document.querySelector(`.select-localidad[data-registro-id="${registroId}"]`);

        if (!selectLocalidad) return;

        const todasLocalidades = Array.from(selectLocalidad.options)
            .slice(1)
            .map(option => option.cloneNode(true));

        function repoblarLocalidades(municipioId, localidadSeleccionada = '') {
            selectLocalidad.innerHTML = '<option value="">Seleccionar...</option>';

            todasLocalidades.forEach(option => {
                if (!municipioId || option.dataset.municipio === municipioId) {
                    const optionClonada = option.cloneNode(true);
                    if (localidadSeleccionada && optionClonada.value === localidadSeleccionada) {
                        optionClonada.selected = true;
                    }
                    selectLocalidad.appendChild(optionClonada);
                }
            });

            if (
                localidadSeleccionada &&
                !Array.from(selectLocalidad.options).some(option => option.value === localidadSeleccionada)
            ) {
                selectLocalidad.value = '';
            }
        }

        function sincronizarMunicipioDesdeLocalidad() {
            const optionSeleccionada = selectLocalidad.selectedOptions[0];
            const municipioId = optionSeleccionada?.dataset?.municipio || '';

            if (!municipioId) {
                return;
            }

            if (selectMunicipio.value !== municipioId) {
                selectMunicipio.value = municipioId;
            }

            repoblarLocalidades(municipioId, selectLocalidad.value);
        }

        selectMunicipio.addEventListener('change', function() {
            repoblarLocalidades(this.value, selectLocalidad.value);
        });

        selectLocalidad.addEventListener('change', sincronizarMunicipioDesdeLocalidad);

        if (selectLocalidad.value) {
            sincronizarMunicipioDesdeLocalidad();
        } else {
            repoblarLocalidades(selectMunicipio.value, '');
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
        btnConfirmarReprocesar.addEventListener('click', async function() {
            const url = document.querySelector('meta[name="reprocesar-errores-url"]')?.content;
            if (!url) return;

            const modal = bootstrap.Modal.getInstance(modalConfirmar);
            modal.hide();

            const guardadoPrevio = await guardarCambiosPendientesAntesDeReprocesar();
            if (guardadoPrevio.fallidos > 0) {
                showAlert(
                    'warning',
                    `Se guardaron ${guardadoPrevio.exitosos} registros antes de reprocesar y ${guardadoPrevio.fallidos} siguen con errores de validacion.`
                );
            }

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
    const registrosConCambios = new Set();
    document.querySelectorAll('.form-editar-error').forEach(form => {
        const registroId = form.dataset.registroId;
        const inputs = form.querySelectorAll('input, select, textarea');

        aplicarResaltadoCampos(form, obtenerCamposInvalidos(form));

        function programarGuardado() {
            registrosConCambios.add(registroId);
            clearTimeout(saveTimers[registroId]);
            saveTimers[registroId] = setTimeout(() => {
                guardarRegistro(form, registroId);
            }, 500);
        }

        inputs.forEach(input => {
            const limpiarCampo = () => {
                input.classList.remove('field-error-soft');
                input.removeAttribute('aria-invalid');
            };

            input.addEventListener('change', () => {
                limpiarCampo();
                programarGuardado();
            });
            input.addEventListener('input', () => {
                limpiarCampo();
                programarGuardado();
            });
        });
    });
    
    function mostrarErrorValidacion(form, message) {
        if (form.dataset.validationMessage === message) return;
        form.dataset.validationMessage = message;
        showAlert('danger', message);
    }

    function limpiarErrorValidacion(form) {
        delete form.dataset.validationMessage;
    }

    async function guardarCambiosPendientesAntesDeReprocesar() {
        const forms = Array.from(document.querySelectorAll('.form-editar-error'));
        if (forms.length === 0) return { exitosos: 0, fallidos: 0 };

        let exitosos = 0;
        let fallidos = 0;

        for (const form of forms) {
            const registroId = form.dataset.registroId;
            clearTimeout(saveTimers[registroId]);
            const guardadoOk = await guardarRegistro(form, registroId, { mostrarErrores: false });
            if (guardadoOk) {
                exitosos += 1;
            } else {
                fallidos += 1;
            }
        }

        return { exitosos, fallidos };
    }

    function guardarRegistro(form, registroId, options = {}) {
        const { mostrarErrores = true } = options;
        const urlTemplate = document.querySelector('meta[name="actualizar-error-url-template"]')?.content;
        if (!urlTemplate) return Promise.resolve(false);

        const url = urlTemplate.replace('/0/', `/${registroId}/`);
        const formData = new FormData(form);
        const datos = {};
        formData.forEach((value, key) => {
            datos[key] = typeof value === 'string' ? value.trim() : value;
        });

        limpiarErrorValidacion(form);

        return fetch(url, {
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
                form.dataset.invalidFields = '';
                limpiarResaltadoCampos(form);
                registrosConCambios.delete(String(registroId));
                const row = document.querySelector(`.registro-erroneo-row[data-registro-id="${registroId}"]`);
                if (row) {
                    row.style.borderLeft = '4px solid #28a745';
                    setTimeout(() => {
                        row.style.borderLeft = '4px solid #dc3545';
                    }, 1000);
                }
                return true;
            }
            if (data.saved_partial) {
                form.dataset.invalidFields = (data.invalid_fields || []).join(',');
                aplicarResaltadoCampos(form, data.invalid_fields || []);
                registrosConCambios.delete(String(registroId));
                if (mostrarErrores) {
                    mostrarErrorValidacion(
                        form,
                        data.error || 'Se guardaron cambios parciales, pero quedan validaciones pendientes.'
                    );
                }
                return true;
            } else {
                form.dataset.invalidFields = (data.invalid_fields || []).join(',');
                aplicarResaltadoCampos(form, data.invalid_fields || []);
                if (mostrarErrores) {
                    showAlert('danger', 'Error: ' + (data.error || 'Error desconocido'));
                }
                return false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (mostrarErrores) {
                showAlert('danger', 'Error al guardar registro');
            }
            return false;
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


