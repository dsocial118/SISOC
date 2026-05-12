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
});

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
// EXPONER GLOBALMENTE
// ============================================

window.toggleSection = toggleSection;
