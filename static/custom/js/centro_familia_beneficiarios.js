document.addEventListener("DOMContentLoaded", function() {
    // Inicializar Select2
    $('.select2').select2({
        placeholder: "Seleccione una o más opciones",
        allowClear: true,
        width: '100%'
    });

    // Toggle actividades detalle
    const checkbox = document.getElementById("id_actividades_extracurriculares");
    const detalleContainer = document.getElementById("actividades-detalle-container");

    function toggleDetalle() {
        const detalleInput = document.getElementById("id_actividades_detalle");
        if (checkbox.checked) {
            detalleContainer.style.display = "block";
            if (detalleInput) detalleInput.required = true;
        } else {
            detalleContainer.style.display = "none";
            const checkboxes = detalleContainer.querySelectorAll("input[type=checkbox]");
            checkboxes.forEach(cb => cb.checked = false);
            if (detalleInput) {
                detalleInput.required = false;
                detalleInput.value = '';
            }
        }
    }
    toggleDetalle();
    checkbox.addEventListener("change", toggleDetalle);

    // Toggle nivel educativo
    const estado = document.getElementById("id_estado_academico");
    const nivelContainer = document.getElementById("nivel-educativo-container");
    const nivelSelect = document.getElementById("id_nivel_educativo_actual");

    function toggleNivelEducativo() {
        if (estado.checked) {
            nivelContainer.style.display = "block";
        } else {
            nivelContainer.style.display = "none";
            nivelSelect.selectedIndex = 0;
        }
    }

    toggleNivelEducativo();
    estado.addEventListener("change", toggleNivelEducativo);

    // Envío de formularios
    const submitBtn = document.getElementById("submit-todos-btn");
    const beneficiarioForm = document.getElementById("beneficiario-form");
    const responsableForm = document.getElementById("responsable-form");

    submitBtn.addEventListener("click", function(e) {
        e.preventDefault();
        
        // Validar que ambos formularios estén visibles
        const formContainer = document.getElementById("form-container");
        const responsableContainer = document.getElementById("responsable-form-container");
        
        if (formContainer.style.display === "none" || responsableContainer.style.display === "none") {
            alert("Debe completar la búsqueda de beneficiario y responsable antes de confirmar");
            return;
        }
        
        // Limpiar errores previos
        document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        document.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
        
        let hasErrors = false;
        
        // Validar campos requeridos del beneficiario
        const requiredBeneficiario = ['nombre', 'apellido', 'cuil', 'dni', 'genero', 'fecha_nacimiento', 'domicilio', 'provincia', 'calle', 'maximo_nivel_educativo', 'actividad_preferida'];
        
        requiredBeneficiario.forEach(field => {
            const input = document.getElementById('id_' + field);
            if (input) {
                let isEmpty = false;
                if (input.multiple) {
                    isEmpty = input.selectedOptions.length === 0;
                } else {
                    isEmpty = !input.value || input.value.trim() === '';
                }
                
                if (isEmpty) {
                    input.classList.add('is-invalid');
                    const feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = 'Este campo es requerido';
                    input.parentNode.appendChild(feedback);
                    hasErrors = true;
                }
            }
        });
        
        // Validar campos requeridos del responsable
        const requiredResponsable = ['nombre', 'apellido', 'dni', 'cuil', 'genero', 'fecha_nacimiento', 'vinculo_parental', 'calle', 'provincia'];
        
        requiredResponsable.forEach(field => {
            const input = responsableForm.querySelector('#id_' + field);
            if (input && (!input.value || input.value.trim() === '')) {
                input.classList.add('is-invalid');
                const feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                feedback.textContent = 'Este campo es requerido';
                input.parentNode.appendChild(feedback);
                hasErrors = true;
            }
        });
        
        // Validar actividades_detalle si actividades_extracurriculares está marcado
        const actividadesExtra = document.getElementById('id_actividades_extracurriculares');
        if (actividadesExtra && actividadesExtra.checked) {
            const actividadesDetalle = document.querySelectorAll('input[name="actividades_detalle"]:checked');
            if (actividadesDetalle.length === 0) {
                const container = document.getElementById('actividades-detalle-container');
                container.classList.add('is-invalid');
                const feedback = document.createElement('div');
                feedback.className = 'invalid-feedback d-block';
                feedback.textContent = 'Debe seleccionar al menos una actividad';
                container.appendChild(feedback);
                hasErrors = true;
            }
        }
        
        if (hasErrors) {
            // Scroll al primer campo con error
            const firstError = document.querySelector('.is-invalid');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstError.focus();
            }
            return;
        }
        
        // Crear FormData combinando ambos formularios
        const formData = new FormData();
        
        // Agregar CSRF token una sola vez
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        formData.append('csrfmiddlewaretoken', csrfToken);
        
        // Procesar datos del beneficiario
        const beneficiarioInputs = beneficiarioForm.querySelectorAll('input, select, textarea');
        beneficiarioInputs.forEach(input => {
            if (input.name && input.name !== 'csrfmiddlewaretoken') {
                if (input.type === 'checkbox') {
                    if (input.name === 'actividades_detalle') {
                        // Manejar ManyToMany field
                        if (input.checked) {
                            formData.append('beneficiario_' + input.name, input.value);
                        }
                    } else if (input.name === 'actividad_preferida') {
                        // Manejar MultipleChoiceField
                        if (input.checked) {
                            formData.append('beneficiario_' + input.name, input.value);
                        }
                    } else {
                        formData.append('beneficiario_' + input.name, input.checked);
                    }
                } else if (input.type === 'radio') {
                    if (input.checked) {
                        formData.append('beneficiario_' + input.name, input.value);
                    }
                } else if (input.tagName === 'SELECT' && input.multiple) {
                    // Manejar select múltiple (Select2)
                    const selectedOptions = Array.from(input.selectedOptions);
                    selectedOptions.forEach(option => {
                        formData.append('beneficiario_' + input.name, option.value);
                    });
                } else {
                    // Habilitar campos disabled temporalmente para obtener su valor
                    const wasDisabled = input.disabled;
                    if (wasDisabled) input.disabled = false;
                    
                    if (input.value) {
                        formData.append('beneficiario_' + input.name, input.value);
                    }
                    
                    if (wasDisabled) input.disabled = true;
                }

            }
        });
        
        // Procesar datos del responsable
        const responsableInputs = responsableForm.querySelectorAll('input, select, textarea');
        responsableInputs.forEach(input => {
            if (input.name && input.name !== 'csrfmiddlewaretoken') {
                if (input.type === 'checkbox') {
                    formData.append('responsable_' + input.name, input.checked);
                } else if (input.type === 'radio') {
                    if (input.checked) {
                        formData.append('responsable_' + input.name, input.value);
                    }
                } else {
                    // Habilitar campos disabled temporalmente
                    const wasDisabled = input.disabled;
                    if (wasDisabled) input.disabled = false;
                    
                    if (input.value) {
                        formData.append('responsable_' + input.name, input.value);
                    }
                    
                    if (wasDisabled) input.disabled = true;
                }

            }
        });
        

        
        // Deshabilitar botón y mostrar spinner
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Procesando...';
        
        // Enviar al servidor
        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {

            if (response.ok) {
                return response.json().catch(() => ({ status: 'success' }));
            } else {
                return response.json().then(data => {
                    throw new Error(data.message || 'Error en el servidor');
                });
            }
        })
        .then(data => {

            if (data.status === 'success') {
                // Recargar inmediatamente - el toast aparecerá con el mensaje de Django
                window.location.reload();
            } else {
                alert('Error: ' + (data.message || 'Error al procesar la preinscripción'));

            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al enviar los datos: ' + error.message);
        })
        .finally(() => {
            // Rehabilitar botón
            submitBtn.disabled = false;
            submitBtn.innerHTML = "Confirmar Preinscripción";
        });
    });

    // Búsqueda de CUIL
    const cuilInput = document.getElementById("cuil-input");
    const buscarBtn = document.getElementById("buscar-btn");
    const resultado = document.getElementById("resultado");
    const formContainer = document.getElementById("form-container");
    const beneficiarioFormEl = document.getElementById("beneficiario-form");

    // Máscara de CUIL mientras escribe
    cuilInput.addEventListener("input", function(e) {
        let value = e.target.value.replace(/\D/g, "");

        if (value.length > 2) {
            value = value.slice(0,2) + "-" + value.slice(2);
        }
        if (value.length > 11) {
            value = value.slice(0,11) + "-" + value.slice(11,13);
        }

        e.target.value = value;
    });

    function buscarCuil() {
        let cuil = cuilInput.value.trim();
        if (!cuil) {
            alert("Debe ingresar un CUIL");
            return;
        }

        cuil = cuil.replace(/-/g, "");

        // Cambiar botón a estado de carga
        buscarBtn.disabled = true;
        buscarBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Buscando...';

        fetch(window.buscarCuilUrl + "?cuil=" + encodeURIComponent(cuil))
            .then(response => response.json()) 
            .then(data => {
                hideElement(resultado);

                if (data.status === "exists") {
                    showAlert(resultado, "alert alert-warning text-center", data.message);
                    showElement(formContainer);
                    for (const key in data.data) {
                        const input = document.getElementById("id_" + key);
                        if (input) input.value = data.data[key] || '';
                    }
                } else if (data.status === "not_found") {
                    showAlert(resultado, "alert alert-danger text-center", data.message);
                    hideElement(formContainer);
                } else if (data.status === "possible") {
                    showElement(formContainer);
                    for (const key in data.data) {
                        const input = document.getElementById("id_" + key);
                        if (input) input.value = data.data[key] || '';
                    }
                }
            })
            .catch(err => {
                showAlert(resultado, "alert alert-danger", "Error al buscar CUIL: " + err);
                hideElement(formContainer);
            })
            .finally(() => {
                // Restaurar botón
                buscarBtn.disabled = false;
                buscarBtn.innerHTML = 'Buscar';
            });
    }

    // Botón buscar CUIL
    buscarBtn.addEventListener("click", buscarCuil);

    // Enter en input CUIL
    cuilInput.addEventListener("keypress", function(e) {
        if (e.key === "Enter") {
            e.preventDefault();
            buscarCuil();
        }
    });

    // Búsqueda de responsable
    const buscarRespBtn = document.getElementById("buscar-responsable-btn");
    const dniInput = document.getElementById("dni-input");
    const sexoInputs = document.querySelectorAll("input[name='sexo_resposable']");
    const respFormContainer = document.getElementById("responsable-form-container");
    const resultadoResp = document.getElementById("resultado_responsable");
    const respForm = document.getElementById("responsable-form");

    const sexoMap = { "femenino": "F", "masculino": "M" };

    function clearResponsableForm() {
        const inputs = respForm.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.type === 'checkbox' || input.type === 'radio') {
                input.checked = false;
            } else {
                input.value = '';
            }
        });
        
        // Limpiar selects de ubicación
        const municipioSelect = respForm.querySelector('#id_municipio');
        const localidadSelect = respForm.querySelector('#id_localidad');
        if (municipioSelect) municipioSelect.innerHTML = '<option value="">---------</option>';
        if (localidadSelect) localidadSelect.innerHTML = '<option value="">---------</option>';
    }

    function fillResponsableForm(formData) {
        // Limpiar formulario antes de llenarlo
        clearResponsableForm();
        
        for (const key in formData) {
            const input = respForm.querySelector("#id_" + key);
            if (input) {
                input.value = (input.type === "number" && formData[key] !== null && formData[key] !== "") 
                    ? Number(formData[key]) : formData[key];
            }
        }
        setupLocationSelectsForResponsable();
        
        // Cargar municipios y localidades si hay provincia seleccionada
        if (formData.provincia) {
            loadMunicipiosForResponsable(formData.provincia, formData.municipio, formData.localidad);
        }
    }
    
    function loadMunicipiosForResponsable(provinciaId, municipioId, localidadId) {
        const municipioSelect = respForm.querySelector('#id_municipio');
        const localidadSelect = respForm.querySelector('#id_localidad');
        
        if (provinciaId && municipioSelect) {
            fetch(`/ajax/load-municipios/?provincia_id=${provinciaId}`)
                .then(response => response.json())
                .then(municipios => {
                    populateSelect(municipioSelect, municipios);
                    if (municipioId) {
                        municipioSelect.value = municipioId;
                        loadLocalidadesForResponsable(municipioId, localidadId);
                    }
                })
                .catch(error => console.error('Error cargando municipios:', error));
        }
    }
    
    function loadLocalidadesForResponsable(municipioId, localidadId) {
        const localidadSelect = respForm.querySelector('#id_localidad');
        
        if (municipioId && localidadSelect) {
            fetch(`/ajax/load-localidades/?municipio_id=${municipioId}`)
                .then(response => response.json())
                .then(localidades => {
                    populateSelect(localidadSelect, localidades);
                    if (localidadId) {
                        localidadSelect.value = localidadId;
                    }
                })
                .catch(error => console.error('Error cargando localidades:', error));
        }
    }

    function buscarResponsable() {
        const dni = dniInput.value.trim();
        const sexoSeleccionado = Array.from(sexoInputs).find(r => r.checked)?.value;

        hideElement(resultadoResp);

        if (!dni || !sexoSeleccionado) {
            showAlert(resultadoResp, "alert alert-danger text-center", "Debe ingresar DNI y seleccionar sexo");
            hideElement(respFormContainer);
            return;
        }

        // Cambiar botón a estado de carga
        buscarRespBtn.disabled = true;
        buscarRespBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Buscando...';

        fetch(`${window.buscarResponsableUrl}?dni=${encodeURIComponent(dni)}&sexo=${encodeURIComponent(sexoMap[sexoSeleccionado])}`)
            .then(res => res.json())
            .then(data => {
                const alertContainer = document.getElementById('responsable-alert-container');
                
                if (data.status === "exists") {
                    if (alertContainer) {
                        alertContainer.innerHTML = `
                            <div class="alert alert-warning alert-dismissible fade show mt-3 mb-3 text-center" role="alert">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                <strong>Responsable encontrado:</strong> ${data.message}
                                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                            </div>`;
                    }
                    showElement(respFormContainer);
                    fillResponsableForm(data.data);
                } else if (data.status === "possible") {
                    if (alertContainer) {
                        alertContainer.innerHTML = '';
                    }
                    showElement(respFormContainer);
                    fillResponsableForm(data.data);
                } else {
                    if (alertContainer) {
                        alertContainer.innerHTML = '';
                    }
                    showAlert(resultadoResp, "alert alert-danger text-center", data.message || "No se encontró el Responsable");
                    hideElement(respFormContainer);
                }
            })
            .catch(err => {
                showAlert(resultadoResp, "alert alert-danger text-center", "Error al consultar Responsable: " + err);
                hideElement(respFormContainer);
            })
            .finally(() => {
                // Restaurar botón
                buscarRespBtn.disabled = false;
                buscarRespBtn.innerHTML = 'Buscar';
            });
    }

    buscarRespBtn.addEventListener("click", buscarResponsable);

    // Enter en input DNI
    dniInput.addEventListener("keypress", function(e) {
        if (e.key === "Enter") {
            e.preventDefault();
            buscarResponsable();
        }
    });
    
    // Funciones auxiliares
    function hideElement(element) {
        if (element) {
            element.style.display = "none";
            // Solo limpiar contenido si no es un contenedor de formulario
            if (element.id !== "form-container" && element.id !== "responsable-form-container") {
                element.className = "";
                element.innerText = "";
            }
        }
    }

    function showElement(element) {
        element.style.display = "block";
    }

    function showAlert(element, className, message) {
        element.style.display = "block";
        element.className = className;
        element.innerText = message;
    }

    function populateSelect(select, items, valueKey = 'id', textKey = 'nombre') {
        select.innerHTML = '<option value="">---------</option>';
        items.forEach(item => {
            const option = document.createElement('option');
            option.value = item[valueKey];
            option.textContent = item[textKey];
            select.appendChild(option);
        });
    }

    function setupLocationSelects(prefix, containerPrefix = '') {
        const provinciaSelect = document.querySelector(`${containerPrefix}#id_${prefix}provincia`);
        const municipioSelect = document.querySelector(`${containerPrefix}#id_${prefix}municipio`);
        const localidadSelect = document.querySelector(`${containerPrefix}#id_${prefix}localidad`);
        
        if (!provinciaSelect || !municipioSelect || !localidadSelect) return;
        
        provinciaSelect.addEventListener('change', function() {
            const provinciaId = this.value;
            localidadSelect.innerHTML = '<option value="">---------</option>';
            
            if (provinciaId) {
                fetch(`/ajax/load-municipios/?provincia_id=${provinciaId}`)
                    .then(response => response.json())
                    .then(municipios => populateSelect(municipioSelect, municipios))
                    .catch(error => console.error('Error cargando municipios:', error));
            } else {
                municipioSelect.innerHTML = '<option value="">---------</option>';
            }
        });
        
        municipioSelect.addEventListener('change', function() {
            const municipioId = this.value;
            
            if (municipioId) {
                fetch(`/ajax/load-localidades/?municipio_id=${municipioId}`)
                    .then(response => response.json())
                    .then(localidades => populateSelect(localidadSelect, localidades))
                    .catch(error => console.error('Error cargando localidades:', error));
            } else {
                localidadSelect.innerHTML = '<option value="">---------</option>';
            }
        });
    }
    
    function setupLocationSelectsForResponsable() {
        setupLocationSelects('', '#responsable-form ');
    }
    
    // Configurar selects para beneficiario
    setupLocationSelects('');
    
    // Limpiar errores cuando el usuario empiece a escribir/seleccionar
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('is-invalid')) {
            e.target.classList.remove('is-invalid');
            const feedback = e.target.parentNode.querySelector('.invalid-feedback');
            if (feedback) feedback.remove();
        }
    });
    
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('is-invalid')) {
            e.target.classList.remove('is-invalid');
            const feedback = e.target.parentNode.querySelector('.invalid-feedback');
            if (feedback) feedback.remove();
        }
    });
});