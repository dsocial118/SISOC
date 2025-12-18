/**
 * COMEDOR FORM - JAVASCRIPT MODERNO
 * Formulario de creación/edición de comedores
 * Funcionalidades: Árbol de estados, Select2, Validación, Progreso
 */

// ============================================
// MANEJO DEL ÁRBOL DE ESTADOS (Estado General > Subestado > Motivo)
// ============================================
document.addEventListener("DOMContentLoaded", function () {
    initializeEstadoTree();
    initializeSelect2Fields();
    initializeCollapsibleSections();
    initializeRealTimeValidation();
    initializeProgressTracking();
    moveTooltipsToLabels();
    initializeSelect2AutoFocus();
});

/**
 * Inicializa el árbol jerárquico de estados
 * Estado General -> Subestado -> Motivo
 */
function initializeEstadoTree() {
    const dataElement = document.getElementById("estado-general-data");
    if (!dataElement) {
        return;
    }

    let estadoTree = {};
    try {
        estadoTree = JSON.parse(dataElement.textContent) || {};
    } catch (error) {
        console.error("No se pudo interpretar los estados del comedor.", error);
        return;
    }

    const estadoSelect = document.getElementById("id_estado_general");
    const subestadoSelect = document.getElementById("id_subestado");
    const motivoSelect = document.getElementById("id_motivo");

    if (!estadoSelect || !subestadoSelect || !motivoSelect) {
        return;
    }

    const subestadoPlaceholder =
        subestadoSelect.dataset.placeholder || "Seleccione un subestado";
    const motivoPlaceholder =
        motivoSelect.dataset.placeholder || "Seleccione un motivo";

    const initialSelections = {
        subestado: subestadoSelect.value,
        motivo: motivoSelect.value,
    };

    function renderOptions(select, options, placeholderText, preservedValue = "") {
        const desiredValue = preservedValue ?? select.value;
        const $select = $(select);

        // IMPORTANTE: Destruir Select2 COMPLETAMENTE antes de manipular el DOM
        if (typeof $.fn.select2 !== 'undefined' && $select.data('select2')) {
            try {
                $select.select2('destroy');
                // Remover cualquier elemento select2 huérfano
                $('.select2-container').has(`[aria-controls="${select.id}"]`).remove();
            } catch (error) {
                console.warn('Error al destruir Select2:', error);
            }
        }

        // Modificar opciones del select nativo
        select.innerHTML = "";

        const emptyOption = document.createElement("option");
        emptyOption.value = "";
        emptyOption.textContent = placeholderText;
        if (!desiredValue) {
            emptyOption.selected = true;
        }
        select.appendChild(emptyOption);

        options.forEach((option) => {
            const opt = document.createElement("option");
            opt.value = option.id;
            opt.textContent = option.label;
            if (desiredValue && String(option.id) === String(desiredValue)) {
                opt.selected = true;
            }
            select.appendChild(opt);
        });

        if (desiredValue) {
            const exists = options.some(
                (option) => String(option.id) === String(desiredValue)
            );
            if (!exists) {
                select.value = "";
            }
        } else {
            select.value = "";
        }

        // Solo inicializar Select2 si hay opciones disponibles
        if (options.length > 0 && typeof initializeSelect2 === 'function') {
            const selectId = select.id;
            // Pequeño delay para asegurar que el DOM esté limpio
            setTimeout(() => {
                initializeSelect2(selectId, {
                    placeholder: placeholderText,
                    allowClear: selectId === 'id_motivo'
                });
            }, 50);
        }
    }

    function getProcesos(actividadId) {
        if (!actividadId) {
            return [];
        }
        const actividad = estadoTree[String(actividadId)];
        return actividad ? actividad.procesos : [];
    }

    function getDetalles(actividadId, procesoId) {
        if (!actividadId || !procesoId) {
            return [];
        }

        const procesos = getProcesos(actividadId);
        const proceso = procesos.find(
            (item) => String(item.id) === String(procesoId)
        );
        const detalles = proceso ? proceso.detalles : [];
        return detalles;
    }

    function setDisabled(select, disabled) {
        select.disabled = disabled;
        const $select = $(select);

        if (disabled) {
            select.setAttribute("disabled", "disabled");
        } else {
            select.removeAttribute("disabled");
        }

        // Actualizar Select2 para reflejar el cambio de estado
        if (typeof $.fn.select2 !== 'undefined' && $select.data('select2')) {
            $select.prop('disabled', disabled);
        }
    }

    function refreshMotivos(preservedMotivo = "") {
        const actividadId = estadoSelect.value;
        const procesoId = subestadoSelect.value;
        const detalles = getDetalles(actividadId, procesoId);

        if (detalles.length === 0) {
            // No hay opciones: limpiar, deshabilitar y NO inicializar Select2
            motivoSelect.innerHTML = '<option value="">---------</option>';
            motivoSelect.value = "";
            setDisabled(motivoSelect, true);
        } else {
            // Hay opciones: renderizar e inicializar Select2
            setDisabled(motivoSelect, false);
            renderOptions(motivoSelect, detalles, motivoPlaceholder, preservedMotivo);
        }
    }

    function refreshSubestados(preservedSubestado = "", preservedMotivo = "") {
        const actividadId = estadoSelect.value;
        const procesos = getProcesos(actividadId);

        if (procesos.length === 0) {
            // No hay opciones: limpiar, deshabilitar y NO inicializar Select2
            subestadoSelect.innerHTML = '<option value="">---------</option>';
            subestadoSelect.value = "";
            setDisabled(subestadoSelect, true);
        } else {
            // Hay opciones: renderizar e inicializar Select2
            setDisabled(subestadoSelect, false);
            renderOptions(subestadoSelect, procesos, subestadoPlaceholder, preservedSubestado);
        }

        refreshMotivos(preservedMotivo);
    }

    // Usar eventos de Select2 en lugar de eventos nativos
    $(estadoSelect).on('select2:select change', function () {
        refreshSubestados("", "");
    });

    $(subestadoSelect).on('select2:select change', function () {
        refreshMotivos("");
    });

    refreshSubestados(initialSelections.subestado || "", initialSelections.motivo || "");
}

// ============================================
// INICIALIZACIÓN DE SELECT2
// ============================================

/**
 * Inicializa todos los campos Select2 del formulario
 * Requiere que initializeSelect2() esté definida en comedorform.js
 */
function initializeSelect2Fields() {
    $(document).ready(function() {
        // Esperar a que el archivo externo esté completamente cargado
        setTimeout(async function () {
            try {
                // Configurar Select2 con AJAX para organizaciones
                $('#id_organizacion').select2({
                    ajax: {
                        url: ajaxLoadOrganizacionesUrl,
                        dataType: 'json',
                        delay: 250,
                        data: function (params) {
                            return {
                                q: params.term,
                                page: params.page || 1
                            };
                        },
                        processResults: function (data, params) {
                            params.page = params.page || 1;
                            return {
                                results: data.results,
                                pagination: {
                                    more: data.pagination.more
                                }
                            };
                        },
                        cache: true
                    },
                    placeholder: "Seleccione una organización",
                    allowClear: true,
                    minimumInputLength: 0,
                    width: '100%'
                });

                // IMPORTANTE: Inicializar Select2 en provincia ANTES del gestor de ubicación
                // para asegurar que las opciones del select estén disponibles
                initializeSelect2('id_provincia', {
                    placeholder: "Seleccione una provincia",
                    allowClear: true
                });

                if (typeof window.initUbicacionSelects === 'function') {
                    await window.initUbicacionSelects({
                        ajaxMunicipiosUrl: ajaxLoadMunicipiosUrl,
                        ajaxLocalidadesUrl: ajaxLoadLocalidadesUrl,
                        selectors: {
                            provincia: "#id_provincia",
                            municipio: "#id_municipio",
                            localidad: "#id_localidad"
                        },
                        ui: {
                            municipio: { loader: "#municipio-loader", wrapper: "#municipio-field", dropdownParent: "#municipio-field" },
                            localidad: { loader: "#localidad-loader", wrapper: "#localidad-field", dropdownParent: "#localidad-field" }
                        },
                        autoPrefetch: true
                    });
                }

                initializeSelect2('id_estado_general', {
                    placeholder: "Seleccione un estado general",
                    allowClear: false
                });

                initializeSelect2('id_subestado', {
                    placeholder: "Seleccione un subestado",
                    allowClear: false
                });

                initializeSelect2('id_motivo', {
                    placeholder: "Seleccione un motivo",
                    allowClear: true
                });

            } catch (error) {
                console.error('ERROR al inicializar Select2:', error);
            }
        }, 500);
    });
}

// ============================================
// SISTEMA DE SECCIONES COLAPSABLES CON ACCESIBILIDAD
// ============================================

/**
 * Alterna el estado de una sección (expandida/colapsada)
 */
function toggleSection(sectionId) {
    const sectionBody = document.getElementById('section-' + sectionId);
    const sectionHeader = document.querySelector(`[data-section="${sectionId}"] .section-header`);

    if (sectionBody) {
        // Bootstrap collapse
        $(sectionBody).collapse('toggle');

        // Toggle clase collapsed en el header
        sectionHeader.classList.toggle('collapsed');
    }
}

/**
 * Inicializa el sistema de secciones colapsables con soporte de accesibilidad
 */
function initializeCollapsibleSections() {
    const sectionHeaders = document.querySelectorAll('.section-header');

    sectionHeaders.forEach(header => {
        // Hacer accesible con teclado
        header.setAttribute('tabindex', '0');
        header.setAttribute('role', 'button');
        header.setAttribute('aria-expanded', 'true');

        // Soporte Enter y Space
        header.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const section = this.closest('.section-card').dataset.section;
                toggleSection(section);
            }
        });

        // Actualizar aria-expanded
        const sectionBody = header.nextElementSibling;
        if (sectionBody) {
            $(sectionBody).on('shown.bs.collapse', function() {
                header.setAttribute('aria-expanded', 'true');
            });
            $(sectionBody).on('hidden.bs.collapse', function() {
                header.setAttribute('aria-expanded', 'false');
            });
        }
    });
}

// ============================================
// VALIDACIÓN EN TIEMPO REAL
// ============================================

/**
 * Inicializa la validación en tiempo real de campos requeridos
 */
function initializeRealTimeValidation() {
    // Seleccionar todos los campos del formulario
    const allFields = document.querySelectorAll('#comedorForm input, #comedorForm select, #comedorForm textarea');

    allFields.forEach(field => {
        // Solo agregar validación si el campo tiene el atributo required del HTML
        if (field.hasAttribute('required')) {
            // Buscar el contenedor MÁS ESPECÍFICO (columna, no el form-group row)
            const wrapper = field.closest('.col-md-2') ||
                           field.closest('.col-md-3') ||
                           field.closest('.col-md-4') ||
                           field.closest('.col-md-6') ||
                           field.closest('.col-12') ||
                           field.closest('.form-group');

            field.addEventListener('blur', function() {
                validateField(this, wrapper);
            });

            field.addEventListener('input', function() {
                if (wrapper && wrapper.classList.contains('field-validated')) {
                    validateField(this, wrapper);
                }
            });
        }
    });

    // Validación especial para Select2 con required
    $('.select2').each(function() {
        const originalSelect = $(this);
        if (originalSelect.prop('required')) {
            originalSelect.on('select2:select select2:unselect', function() {
                // Buscar el contenedor MÁS ESPECÍFICO (columna, no el form-group row)
                const wrapper = $(this).closest('.col-md-2')[0] ||
                               $(this).closest('.col-md-3')[0] ||
                               $(this).closest('.col-md-4')[0] ||
                               $(this).closest('.col-md-6')[0] ||
                               $(this).closest('.col-12')[0] ||
                               $(this).closest('.form-group')[0];
                validateField(this, wrapper);
            });
        }
    });
}

/**
 * Valida un campo individual y actualiza su visualización
 * SOLO APLICA A CAMPOS REQUERIDOS
 */
function validateField(field, wrapper) {
    if (!wrapper) return;

    const value = field.value ? field.value.trim() : '';
    const isRequired = field.hasAttribute('required');

    // Limpiar clases previas
    wrapper.classList.remove('field-validated', 'valid', 'invalid');

    // CRÍTICO: Solo validar y mostrar indicador visual si el campo es requerido
    if (!isRequired) {
        return; // Salir temprano para campos opcionales
    }

    // Aplicar validación solo a campos required
    if (value) {
        wrapper.classList.add('field-validated', 'valid');
    } else {
        wrapper.classList.add('field-validated', 'invalid');
    }
}

// ============================================
// SISTEMA DE PROGRESO
// ============================================

/**
 * Inicializa el seguimiento de progreso del formulario
 */
function initializeProgressTracking() {
    // Actualizar progreso inicial
    updateProgress();

    // Monitorear cambios en formulario
    const form = document.getElementById('comedorForm');
    if (form) {
        form.addEventListener('input', function() {
            updateProgress();
        });
        form.addEventListener('change', function() {
            updateProgress();
        });
    }
}

/**
 * Actualiza el indicador de progreso y los badges de estado
 */
function updateProgress() {
    const sections = {
        basic: checkSectionBasic(),
        estado: checkSectionEstado(),
        ubicacion: checkSectionUbicacion(),
        referente: checkSectionReferente(),
        multimedia: checkSectionMultimedia()
    };

    let completedCount = 0;
    Object.keys(sections).forEach(sectionId => {
        const badge = document.getElementById('status-' + sectionId);
        if (badge) {
            const isComplete = sections[sectionId];
            if (isComplete) {
                completedCount++;
                badge.className = 'status-badge complete';
                badge.innerHTML = '<i class="fas fa-check-circle"></i> Completada';
            } else {
                const hasData = hasSectionData(sectionId);
                if (hasData) {
                    badge.className = 'status-badge incomplete';
                    badge.innerHTML = '<i class="fas fa-exclamation-circle"></i> Incompleta';
                } else {
                    badge.className = 'status-badge empty';
                    badge.innerHTML = '<i class="fas fa-circle"></i> Sin completar';
                }
            }
        }
    });

    // Actualizar barra de progreso
    const progressPercent = (completedCount / 5) * 100;
    const progressBar = document.getElementById('progressBarFill');
    const completedSections = document.getElementById('completedSections');

    if (progressBar) {
        progressBar.style.width = progressPercent + '%';
    }
    if (completedSections) {
        completedSections.textContent = completedCount;
    }
}

/**
 * Verifica si la sección "Información Básica" está completa
 */
function checkSectionBasic() {
    const nombre = document.getElementById('id_nombre');
    const tipocomedor = document.getElementById('id_tipocomedor');
    const organizacion = document.getElementById('id_organizacion');

    return nombre && nombre.value.trim() !== '' &&
           tipocomedor && tipocomedor.value !== '' &&
           organizacion && organizacion.value !== '';
}

/**
 * Verifica si la sección "Estado y Proceso" está completa
 */
function checkSectionEstado() {
    const estadoGeneral = document.getElementById('id_estado_general');
    const subestado = document.getElementById('id_subestado');

    return estadoGeneral && estadoGeneral.value !== '' &&
           subestado && subestado.value !== '';
}

/**
 * Verifica si la sección "Ubicación y Dirección" está completa
 */
function checkSectionUbicacion() {
    const provincia = document.getElementById('id_provincia');
    const municipio = document.getElementById('id_municipio');
    const localidad = document.getElementById('id_localidad');

    return provincia && provincia.value !== '' &&
           municipio && municipio.value !== '' &&
           localidad && localidad.value !== '';
}

/**
 * Verifica si la sección "Datos del Referente" está completa
 */
function checkSectionReferente() {
    const nombre = document.getElementById('id_referente-nombre');
    const apellido = document.getElementById('id_referente-apellido');
    const celular = document.getElementById('id_referente-celular');

    return nombre && nombre.value.trim() !== '' &&
           apellido && apellido.value.trim() !== '' &&
           celular && celular.value.trim() !== '';
}

/**
 * Verifica si la sección "Galería y Multimedia" está completa
 */
function checkSectionMultimedia() {
    // Verificar si hay foto de legajo o imágenes
    const fotoLegajo = document.getElementById('id_foto_legajo');
    const hasExistingPhoto = document.querySelector('.foto-legajo-existente') !== null;
    const hasExistingImages = document.querySelectorAll('.imagen-existente').length > 0;
    const hasNewImages = document.querySelectorAll('.preview-nueva-imagen').length > 0;

    return hasExistingPhoto || (fotoLegajo && fotoLegajo.files.length > 0) ||
           hasExistingImages || hasNewImages;
}

/**
 * Verifica si una sección tiene algún dato ingresado
 */
function hasSectionData(sectionId) {
    const section = document.getElementById('section-' + sectionId);
    if (!section) return false;

    const inputs = section.querySelectorAll('input:not([type="hidden"]), select, textarea');
    for (let input of inputs) {
        if (input.value && input.value.trim() !== '') {
            return true;
        }
    }
    return false;
}

// ============================================
// SKELETON LOADERS PARA AJAX
// ============================================

/**
 * Intercepta la función cargarOpciones para mostrar skeleton loaders
 */
const originalCargarOpciones = window.cargarOpciones;
if (originalCargarOpciones) {
    window.cargarOpciones = async function(url, select) {
        // Mostrar skeleton loader
        if (select === 'municipio') {
            showLoader('municipio');
        } else if (select === 'localidad') {
            showLoader('localidad');
        }

        try {
            await originalCargarOpciones(url, select);
        } finally {
            // Ocultar skeleton loader
            if (select === 'municipio') {
                hideLoader('municipio');
            } else if (select === 'localidad') {
                hideLoader('localidad');
            }
        }
    };
}

/**
 * Muestra el skeleton loader para un campo
 */
function showLoader(fieldName) {
    const loader = document.getElementById(fieldName + '-loader');
    const field = document.getElementById(fieldName + '-field');
    if (loader && field) {
        loader.classList.remove('d-none');
        field.style.opacity = '0.3';
    }
}

/**
 * Oculta el skeleton loader para un campo
 */
function hideLoader(fieldName) {
    const loader = document.getElementById(fieldName + '-loader');
    const field = document.getElementById(fieldName + '-field');
    if (loader && field) {
        loader.classList.add('d-none');
        field.style.opacity = '1';
    }
}

// ============================================
// MOVER TOOLTIPS AL LABEL
// ============================================

/**
 * Mueve los tooltips desde debajo del input hasta junto al label
 */
function moveTooltipsToLabels() {
    // Buscar todos los tooltips en el formulario
    const tooltips = document.querySelectorAll('.field-tooltip');

    tooltips.forEach(tooltip => {
        // Encontrar el contenedor directo (la columna específica donde está el tooltip)
        const directColumn = tooltip.closest('.col-md-2') ||
                            tooltip.closest('.col-md-3') ||
                            tooltip.closest('.col-md-4') ||
                            tooltip.closest('.col-md-6');

        if (directColumn) {
            // Buscar el label SOLO dentro de esa columna específica
            const label = directColumn.querySelector('label');

            if (label) {
                // Remover el tooltip de su posición actual
                tooltip.remove();

                // Insertarlo después del texto del label
                label.appendChild(tooltip);

                // Agregar clase para estilos específicos
                tooltip.classList.add('tooltip-in-label');
            }
        }
    });
}

// ============================================
// AUTO FOCUS EN SELECT2 SEARCH
// ============================================

/**
 * Inicializa el auto-focus en el campo de búsqueda de Select2
 * Cuando se abre un select2, automáticamente enfoca el input de búsqueda
 */
function initializeSelect2AutoFocus() {
    $(document).ready(function() {
        // MÉTODO 1: Listener global para capturar todos los eventos select2:open
        $(document).on('select2:open', function() {
            // Ejecutar el enfoque de manera inmediata y con retry
            focusSelect2SearchField();
        });

        // MÉTODO 2: Observer para detectar nuevos dropdowns de Select2 en el DOM
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    // Si se agrega un dropdown de select2, enfocar su campo de búsqueda
                    if (node.nodeType === 1 && node.classList && node.classList.contains('select2-container--open')) {
                        focusSelect2SearchField();
                    }
                    // También verificar si es el dropdown que se abre
                    if (node.nodeType === 1 && node.classList && node.classList.contains('select2-dropdown')) {
                        focusSelect2SearchField();
                    }
                });
            });
        });

        // Observar cambios en el body
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    });
}

/**
 * Función auxiliar para enfocar el campo de búsqueda de Select2 activo
 */
function focusSelect2SearchField() {
    // Ejecutar inmediatamente
    attemptFocus();

    // Y también con un pequeño delay como backup
    setTimeout(attemptFocus, 10);
    setTimeout(attemptFocus, 50);
}

/**
 * Intenta enfocar el campo de búsqueda visible
 */
function attemptFocus() {
    // Buscar TODOS los campos de búsqueda
    const searchFields = document.querySelectorAll('.select2-search__field');

    // Encontrar el que está visible
    for (let field of searchFields) {
        const isVisible = field.offsetParent !== null &&
                         window.getComputedStyle(field).display !== 'none' &&
                         window.getComputedStyle(field).visibility !== 'hidden';

        if (isVisible) {
            field.focus();
            return; // Salir después de enfocar el primero visible
        }
    }
}

// ============================================
// EXPONER FUNCIONES GLOBALES
// ============================================

// Hacer funciones disponibles globalmente para uso desde HTML
window.toggleSection = toggleSection;
