/**
 * DISPOSITIVO FORM - JAVASCRIPT MODERNO
 * Funcionalidades: Secciones colapsables, Progreso, Validación
 */

document.addEventListener("DOMContentLoaded", function () {
    initializeCollapsibleSections();
    initializeRealTimeValidation();
    initializeProgressTracking();
    moveTooltipsToLabels();
    initializeMunicipioAjax();
    initializeConditionalFields();
    initializeDocumentSlots();
    initializeAddDocButton();
    initializeNumericInputs();
});

const NUMERIC_ONLY_INPUT_IDS = [
    "id_telefono_prefijo",
    "id_telefono_numero",
];

function initializeNumericInputs() {
    NUMERIC_ONLY_INPUT_IDS.forEach((id) => {
        const input = document.getElementById(id);
        if (!input) return;
        input.addEventListener("input", () => {
            const stripped = input.value.replace(/\D/g, "");
            if (stripped !== input.value) {
                input.value = stripped;
            }
        });
    });
}

// ============================================
// SECCIONES COLAPSABLES
// ============================================

function toggleSection(sectionId) {
    const sectionBody = document.getElementById("section-" + sectionId);
    const sectionHeader = document.querySelector(
        `[data-section="${sectionId}"] .section-header`
    );
    if (sectionBody) {
        $(sectionBody).collapse("toggle");
        sectionHeader.classList.toggle("collapsed");
    }
}

function initializeCollapsibleSections() {
    const sectionHeaders = document.querySelectorAll(".section-header");

    sectionHeaders.forEach((header) => {
        header.setAttribute("tabindex", "0");
        header.setAttribute("role", "button");
        header.setAttribute("aria-expanded", "true");

        header.addEventListener("click", function () {
            const section = this.closest(".section-card").dataset.section;
            toggleSection(section);
        });

        header.addEventListener("keydown", function (e) {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                const section = this.closest(".section-card").dataset.section;
                toggleSection(section);
            }
        });

        const sectionBody = header.nextElementSibling;
        if (sectionBody) {
            $(sectionBody).on("shown.bs.collapse", function () {
                header.setAttribute("aria-expanded", "true");
            });
            $(sectionBody).on("hidden.bs.collapse", function () {
                header.setAttribute("aria-expanded", "false");
            });
        }
    });
}

// ============================================
// VALIDACIÓN EN TIEMPO REAL
// ============================================

function getFieldValidationWrapper(field) {
    return (
        field.closest(".col-md-2") ||
        field.closest(".col-md-3") ||
        field.closest(".col-md-4") ||
        field.closest(".col-md-6") ||
        field.closest(".col-md-8") ||
        field.closest(".col-md-12") ||
        field.closest(".col-12") ||
        field.closest(".form-group")
    );
}

function initializeRealTimeValidation() {
    const allFields = document.querySelectorAll(
        "#dispositivoForm input, #dispositivoForm select, #dispositivoForm textarea"
    );

    allFields.forEach((field) => {
        if (field.hasAttribute("required")) {
            const wrapper = getFieldValidationWrapper(field);
            const revalidate = function () {
                validateField(field, wrapper);
            };

            if (field.tagName === "SELECT") {
                field.addEventListener("change", revalidate);
                return;
            }
            if (field.type === "checkbox") {
                field.addEventListener("change", revalidate);
                return;
            }

            field.addEventListener("blur", revalidate);
            field.addEventListener("input", function () {
                if (wrapper && wrapper.classList.contains("field-validated")) {
                    validateField(this, wrapper);
                }
            });
        }
    });
}

function validateField(field, wrapper) {
    if (!wrapper || !field.hasAttribute("required")) return;

    wrapper.classList.remove("field-validated", "valid", "invalid");

    if (field.disabled) return;

    const value = field.value ? field.value.trim() : "";
    if (value) {
        wrapper.classList.add("field-validated", "valid");
    } else {
        wrapper.classList.add("field-validated", "invalid");
    }
}

// ============================================
// SISTEMA DE PROGRESO
// ============================================

function initializeProgressTracking() {
    updateProgress();

    const form = document.getElementById("dispositivoForm");
    if (form) {
        form.addEventListener("input", updateProgress);
        form.addEventListener("change", updateProgress);
    }
}

function updateProgress() {
    const sections = {
        identificacion: checkSectionIdentificacion(),
        caracteristicas: checkSectionCaracteristicas(),
        poblacion: checkSectionPoblacion(),
        ingreso: checkSectionIngreso(),
        servicios: checkSectionServicios(),
        registro: checkSectionRegistro(),
        infraestructura: checkSectionInfraestructura(),
        articulaciones: checkSectionArticulaciones(),
        final: checkSectionFinal(),
    };

    const total = Object.keys(sections).length;
    let completedCount = 0;

    Object.keys(sections).forEach((sectionId) => {
        const badge = document.getElementById("status-" + sectionId);
        if (!badge) return;

        const isComplete = sections[sectionId];
        if (isComplete) {
            completedCount++;
            badge.className = "status-badge complete";
            badge.innerHTML = '<i class="fas fa-check-circle"></i> Completada';
        } else {
            const hasData = hasSectionData(sectionId);
            if (hasData) {
                badge.className = "status-badge incomplete";
                badge.innerHTML =
                    '<i class="fas fa-exclamation-circle"></i> Incompleta';
            } else {
                badge.className = "status-badge empty";
                badge.innerHTML =
                    '<i class="fas fa-circle"></i> Sin completar';
            }
        }
    });

    const progressPercent = (completedCount / total) * 100;
    const progressBar = document.getElementById("progressBarFill");
    const completedSections = document.getElementById("completedSections");

    if (progressBar) progressBar.style.width = progressPercent + "%";
    if (completedSections) completedSections.textContent = completedCount;
}

function checkedCount(name) {
    return document.querySelectorAll(`[name="${name}"]:checked`).length;
}

function fieldHasValue(id) {
    const el = document.getElementById(id);
    return el && el.value && el.value.trim() !== "";
}

function checkSectionIdentificacion() {
    return (
        fieldHasValue("id_nombre_institucion") &&
        fieldHasValue("id_tipo_gestion") &&
        fieldHasValue("id_provincia")
    );
}

function checkSectionCaracteristicas() {
    return fieldHasValue("id_tipo_dispositivo") && fieldHasValue("id_modalidad_funcionamiento");
}

function checkSectionPoblacion() {
    return checkedCount("poblacion_destinataria") > 0 && checkedCount("franja_etaria_destinataria") > 0;
}

function checkSectionIngreso() {
    return checkedCount("modalidad_ingreso") > 0;
}

function checkSectionServicios() {
    return checkedCount("servicios_brindados") > 0;
}

function checkSectionRegistro() {
    return fieldHasValue("id_registra_informacion_personas");
}

function checkSectionInfraestructura() {
    return checkedCount("infraestructura_disponible") > 0;
}

function checkSectionArticulaciones() {
    return checkedCount("articulaciones_institucionales") > 0;
}

function checkSectionFinal() {
    return fieldHasValue("id_observaciones_adicionales");
}

function hasSectionData(sectionId) {
    const section = document.getElementById("section-" + sectionId);
    if (!section) return false;

    const checkboxes = section.querySelectorAll("input[type='checkbox']");
    for (let cb of checkboxes) {
        if (cb.checked) return true;
    }

    const inputs = section.querySelectorAll(
        "input:not([type='hidden']):not([type='checkbox']), select, textarea"
    );
    for (let input of inputs) {
        if (input.value && input.value.trim() !== "") return true;
    }

    return false;
}

// ============================================
// TOOLTIPS AL LADO DEL LABEL
// ============================================

function moveTooltipsToLabels() {
    const tooltips = document.querySelectorAll(".field-tooltip");
    tooltips.forEach((tooltip) => {
        const col =
            tooltip.closest(".col-md-2") ||
            tooltip.closest(".col-md-3") ||
            tooltip.closest(".col-md-4") ||
            tooltip.closest(".col-md-6");
        if (col) {
            const label = col.querySelector("label");
            if (label) {
                tooltip.remove();
                label.appendChild(tooltip);
                tooltip.classList.add("tooltip-in-label");
            }
        }
    });
}

// ============================================
// CAMPOS CONDICIONALES (Si/No)
// ============================================

const OTRO_MULTI_PAIRS = [
    ["poblacion_destinataria", "poblacion_destinataria_otro"],
    ["modalidad_ingreso", "modalidad_ingreso_otro"],
    ["documentacion_ingreso", "documentacion_ingreso_otro"],
    ["requisitos_ingreso", "requisitos_ingreso_otro"],
    ["servicios_brindados", "servicios_brindados_otro"],
    ["tipos_actividades_formativas", "tipos_actividades_formativas_otro"],
    ["tipo_informacion_registrada", "tipo_informacion_registrada_otro"],
    ["infraestructura_disponible", "infraestructura_disponible_otro"],
    ["infraestructura_accesibilidad", "infraestructura_accesibilidad_otro"],
    ["articulaciones_institucionales", "articulaciones_institucionales_otro"],
];

const OTRO_SELECT_PAIRS = [
    ["id_tipo_gestion", "tipo_gestion_otra", "otra"],
    ["id_tipo_dispositivo", "tipo_dispositivo_otro", "otro"],
    ["id_tiempo_permanencia_promedio", "tiempo_permanencia_otro", "otro"],
    ["id_modo_registro", "modo_registro_otro", "otro"],
];

function initializeConditionalFields() {
    bindConditional(
        "id_ofrece_actividades_formativas",
        "actividades-detalle"
    );
    bindConditional(
        "id_registra_informacion_personas",
        "registro-detalle"
    );
    OTRO_MULTI_PAIRS.forEach(([listName, otroField]) =>
        bindOtroForMulti(listName, otroField)
    );
    OTRO_SELECT_PAIRS.forEach(([selectId, otroField, triggerValue]) =>
        bindOtroForSelect(selectId, otroField, triggerValue)
    );
}

function bindConditional(selectId, detailId) {
    const select = document.getElementById(selectId);
    const detail = document.getElementById(detailId);
    if (!select || !detail) return;

    const toggle = () => {
        if (select.value === "si") {
            detail.classList.remove("d-none");
        } else {
            detail.classList.add("d-none");
        }
    };

    toggle();
    select.addEventListener("change", toggle);
}

function bindOtroForMulti(listName, otroFieldName) {
    const wrapper = document.getElementById(`wrapper-${otroFieldName}`);
    if (!wrapper) return;

    const otroCheckbox = document.querySelector(
        `input[name="${listName}"][value="otro"]`
    );
    if (!otroCheckbox) return;

    const apply = (clearValue) => {
        const show = otroCheckbox.checked;
        wrapper.classList.toggle("d-none", !show);
        if (!show && clearValue) {
            const input = wrapper.querySelector(
                "input[type='text'], input:not([type]), textarea"
            );
            if (input) input.value = "";
        }
    };

    otroCheckbox.addEventListener("change", () => apply(true));
    apply(false);
}

function bindOtroForSelect(selectId, otroFieldName, triggerValue) {
    const select = document.getElementById(selectId);
    const wrapper = document.getElementById(`wrapper-${otroFieldName}`);
    if (!select || !wrapper) return;

    const apply = (clearValue) => {
        const show = select.value === triggerValue;
        wrapper.classList.toggle("d-none", !show);
        if (!show && clearValue) {
            const input = wrapper.querySelector(
                "input[type='text'], input:not([type]), textarea"
            );
            if (input) input.value = "";
        }
    };

    select.addEventListener("change", () => apply(true));
    apply(false);
}

// ============================================
// AJAX PROVINCIA → MUNICIPIO
// ============================================

function initializeMunicipioAjax() {
    const provinciaSelect = document.getElementById("id_provincia");
    const municipioSelect = document.getElementById("id_municipio");

    if (!provinciaSelect || !municipioSelect) return;

    const loadMunicipiosUrl = window.ajaxLoadMunicipiosUrl;
    if (!loadMunicipiosUrl) return;

    const resetMunicipios = () => {
        municipioSelect.innerHTML = '<option value="">---------</option>';
    };

    provinciaSelect.addEventListener("change", () => {
        const provinciaId = provinciaSelect.value;
        resetMunicipios();
        if (!provinciaId) return;

        fetch(`${loadMunicipiosUrl}?provincia_id=${encodeURIComponent(provinciaId)}`)
            .then((r) => r.json())
            .then((data) => {
                data.forEach((m) => {
                    const opt = document.createElement("option");
                    opt.value = m.id;
                    opt.textContent = m.nombre;
                    municipioSelect.appendChild(opt);
                });
            })
            .catch(resetMunicipios);
    });
}

// ============================================
// SLOTS DE DOCUMENTOS
// ============================================

function initializeDocumentSlots() {
    document.querySelectorAll(".doc-slot").forEach((slot) => {
        const fieldName = slot.dataset.field;
        const fileInput = slot.querySelector(".doc-widget-hidden input[type='file']");
        if (!fileInput) return;

        // Selección de nuevo archivo
        fileInput.addEventListener("change", () => handleDocFileChange(slot, fieldName, fileInput));

        // Botón "Eliminar archivo guardado"
        const btnEliminar = slot.querySelector(".btn-eliminar-doc");
        if (btnEliminar) {
            btnEliminar.addEventListener("click", () => handleDocEliminar(slot));
        }

        // Botón "Quitar preview"
        const btnQuitar = slot.querySelector(".btn-quitar-preview");
        if (btnQuitar) {
            btnQuitar.addEventListener("click", () => handleDocQuitarPreview(slot, fileInput));
        }

        // Click en overlay "Marcado para eliminar" = desmarcar
        const overlay = slot.querySelector(".doc-eliminar-overlay");
        if (overlay) {
            overlay.addEventListener("click", () => handleDocEliminar(slot));
        }
    });
}

function handleDocFileChange(slot, fieldName, fileInput) {
    const file = fileInput.files[0];
    const preview = document.getElementById("preview-" + fieldName);
    if (!preview) return;

    if (!file) {
        preview.classList.add("d-none");
        return;
    }

    const ext = file.name.split(".").pop().toLowerCase();
    const icon = preview.querySelector(".doc-preview-icon i");
    if (ext === "pdf") {
        icon.className = "fas fa-file-pdf doc-icon-pdf";
    } else if (["jpg", "jpeg", "png"].includes(ext)) {
        icon.className = "fas fa-file-image doc-icon-img";
    } else {
        icon.className = "fas fa-file-alt doc-icon-other";
    }

    preview.querySelector(".doc-preview-name").textContent = file.name;
    preview.querySelector(".doc-preview-size").textContent = formatFileSize(file.size);
    preview.classList.remove("d-none");
}

function handleDocEliminar(slot) {
    const clearCheckbox = slot.querySelector(".doc-widget-hidden input[type='checkbox']");
    const overlay = slot.querySelector(".doc-eliminar-overlay");
    if (!clearCheckbox || !overlay) return;

    clearCheckbox.checked = !clearCheckbox.checked;
    overlay.classList.toggle("d-none", !clearCheckbox.checked);
}

function handleDocQuitarPreview(slot, fileInput) {
    fileInput.value = "";
    const fieldName = slot.dataset.field;
    const preview = document.getElementById("preview-" + fieldName);
    if (preview) preview.classList.add("d-none");
    updateProgress();
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

// ============================================
// BOTÓN AÑADIR ARCHIVO (slots dinámicos hasta 5)
// ============================================

const ADDITIONAL_DOC_FIELDS = [
    "documentacion_dispositivo_adicional_1",
    "documentacion_dispositivo_adicional_2",
    "documentacion_dispositivo_adicional_3",
    "documentacion_dispositivo_adicional_4",
];

function initializeAddDocButton() {
    const btn = document.getElementById("btn-add-doc");
    if (!btn) return;

    const additionalSlots = ADDITIONAL_DOC_FIELDS.map((field) =>
        document.querySelector(`.doc-slot[data-field="${field}"]`)
    ).filter(Boolean);

    const updateButtonVisibility = () => {
        const hasHidden = additionalSlots.some((s) =>
            s.classList.contains("d-none")
        );
        btn.classList.toggle("d-none", !hasHidden);
    };

    btn.addEventListener("click", () => {
        const nextHidden = additionalSlots.find((s) =>
            s.classList.contains("d-none")
        );
        if (nextHidden) {
            nextHidden.classList.remove("d-none");
            updateButtonVisibility();
        }
    });

    updateButtonVisibility();
}

// ============================================
// EXPONER GLOBALMENTE
// ============================================

window.toggleSection = toggleSection;
