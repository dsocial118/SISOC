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
                    alert(mensaje);
                    location.reload();
                } else {
                    alert('Error: ' + (data.error || 'Error desconocido'));
                    btnReprocesar.disabled = false;
                    btnReprocesar.innerHTML = '<i class="fas fa-sync"></i> Reprocesar Todos';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al reprocesar registros');
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
    
    // Eliminar registro erróneo
    document.querySelectorAll('.btn-eliminar-error').forEach(btn => {
        btn.addEventListener('click', function() {
            if (!confirm('¿Está seguro de eliminar este registro?')) {
                return;
            }
            
            const registroId = this.dataset.registroId;
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
                    // Eliminar la fila de la tabla
                    const row = document.querySelector(`.registro-erroneo-row[data-registro-id="${registroId}"]`);
                    if (row) {
                        const nextRow = row.nextElementSibling;
                        row.remove();
                        if (nextRow && nextRow.classList.contains('collapse')) {
                            nextRow.remove();
                        }
                    }
                    
                    // Si no quedan más registros, recargar la página
                    if (document.querySelectorAll('.registro-erroneo-row').length === 0) {
                        location.reload();
                    }
                } else {
                    alert('Error: ' + (data.error || 'Error desconocido'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al eliminar registro');
            });
        });
    });
});
