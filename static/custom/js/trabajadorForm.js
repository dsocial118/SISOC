/**
 * TRABAJADOR CDI FORM - JAVASCRIPT
 * Secciones colapsables, barra de progreso, campos condicionales, geografía.
 */

document.addEventListener("DOMContentLoaded", function () {
    initializeCollapsibleSections();
    initializeProgressTracking();
    initializeConditionalFields();
    initializeGeography();
    initializeAgeCalculation();
});

// ─────────────────────────────────────────────────────────
// SECCIONES COLAPSABLES
// ─────────────────────────────────────────────────────────

function toggleSection(sectionId) {
    const body   = document.getElementById("section-" + sectionId);
    const header = document.querySelector(`[data-section="${sectionId}"] .section-header`);
    if (!body) return;
    $(body).collapse("toggle");
    if (header) header.classList.toggle("collapsed");
}

function initializeCollapsibleSections() {
    document.querySelectorAll(".section-header").forEach(function (header) {
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

        const body = header.nextElementSibling;
        if (body) {
            $(body).on("shown.bs.collapse",  function () { header.setAttribute("aria-expanded", "true"); });
            $(body).on("hidden.bs.collapse", function () { header.setAttribute("aria-expanded", "false"); });
        }
    });
}

// ─────────────────────────────────────────────────────────
// PROGRESO
// ─────────────────────────────────────────────────────────

const TOTAL_SECTIONS = 7;

function initializeProgressTracking() {
    updateProgress();
    const form = document.getElementById("trabajadorForm");
    if (form) {
        form.addEventListener("input",  updateProgress);
        form.addEventListener("change", updateProgress);
    }
}

function updateProgress() {
    const sections = {
        espacio_temporal: checkSectionEspacioTemporal(),
        fuerza_trabajo:   checkSectionFuerzaTrabajo(),
        formacion:        checkSectionFormacion(),
        contratacion:     checkSectionContratacion(),
        contacto:         checkSectionContacto(),
        identidad:        checkSectionIdentidad(),
        discapacidad:     checkSectionDiscapacidad(),
    };

    let completed = 0;
    Object.keys(sections).forEach(function (id) {
        const badge = document.getElementById("status-" + id);
        if (!badge) return;
        if (sections[id]) {
            completed++;
            badge.className = "status-badge complete";
            badge.innerHTML = '<i class="fas fa-check-circle"></i> Completada';
        } else if (hasSectionData(id)) {
            badge.className = "status-badge incomplete";
            badge.innerHTML = '<i class="fas fa-exclamation-circle"></i> Incompleta';
        } else {
            badge.className = "status-badge empty";
            badge.innerHTML = '<i class="fas fa-circle"></i> Sin completar';
        }
    });

    const pct  = (completed / TOTAL_SECTIONS) * 100;
    const bar  = document.getElementById("progressBarFill");
    const span = document.getElementById("completedSections");
    if (bar)  bar.style.width = pct + "%";
    if (span) span.textContent = completed;
}

function val(id) {
    const el = document.getElementById(id);
    return el ? el.value.trim() : "";
}

function checkSectionEspacioTemporal() {
    return val("id_fecha_carga") !== "";
}

function checkSectionFuerzaTrabajo() {
    return val("id_nombre") !== "" && val("id_apellido") !== "" && val("id_subcomponente") !== "";
}

function checkSectionFormacion() {
    return val("id_nivel_educativo") !== "";
}

function checkSectionContratacion() {
    return val("id_tipo_contratacion") !== "";
}

function checkSectionContacto() {
    return val("id_email") !== "" || val("id_telefono") !== "";
}

function checkSectionIdentidad() {
    const checked = document.querySelectorAll("#id_grupo_pertenencia input[type=checkbox]:checked");
    return checked.length > 0;
}

function checkSectionDiscapacidad() {
    return val("id_tiene_discapacidad") !== "";
}

function hasSectionData(sectionId) {
    const section = document.getElementById("section-" + sectionId);
    if (!section) return false;
    const inputs = section.querySelectorAll("input:not([type=hidden]):not([type=checkbox]), select, textarea");
    for (const input of inputs) {
        if (input.value && input.value.trim() !== "") return true;
    }
    const checkboxes = section.querySelectorAll("input[type=checkbox]:checked");
    return checkboxes.length > 0;
}

// ─────────────────────────────────────────────────────────
// CAMPOS CONDICIONALES
// ─────────────────────────────────────────────────────────

const NIVELES_HABILITAN_FORMACION = new Set([
    "secundario_completo", "superior_incompleto", "superior_en_curso", "superior_completo"
]);

function toggleVisible(el, show) {
    if (el) el.classList.toggle("d-none", !show);
}

function getCheckedValues(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return [];
    return [...container.querySelectorAll("input[type=checkbox]:checked")].map(cb => cb.value);
}

function initializeConditionalFields() {
    const subcomponenteSelect  = document.getElementById("id_subcomponente");
    const rowFuncionEgp        = document.getElementById("row-funcion-egp");
    const rowFuncionCdi        = document.getElementById("row-funcion-cdi");
    const rowSalaCdi           = document.getElementById("row-sala-cdi");
    const nivelEducativoSelect = document.getElementById("id_nivel_educativo");
    const rowFormacionAcad     = document.getElementById("row-formacion-academica");
    const tieneDiscapSelect    = document.getElementById("id_tiene_discapacidad");
    const bloqueDiscap         = document.getElementById("bloque-discapacidad");
    const tieneCudSelect       = document.getElementById("id_tiene_cud");
    const rowNumeroCud         = document.getElementById("row-numero-cud");
    const rowPuebloOriginario  = document.getElementById("row-pueblo-originario");

    function applyFunciones() {
        if (!subcomponenteSelect) return;
        const esCdi = subcomponenteSelect.value === "cdi";
        const esEgp = subcomponenteSelect.value === "egp";
        toggleVisible(rowFuncionEgp, esEgp);
        toggleVisible(rowFuncionCdi, esCdi);
        toggleVisible(rowSalaCdi,    esCdi);
    }

    function applyFormacion() {
        if (!nivelEducativoSelect) return;
        toggleVisible(rowFormacionAcad, NIVELES_HABILITAN_FORMACION.has(nivelEducativoSelect.value));
    }

    function applyPuebloOriginario() {
        const vals = getCheckedValues("id_grupo_pertenencia");
        toggleVisible(rowPuebloOriginario, vals.includes("indigena"));
    }

    function applyDiscapacidad() {
        if (!tieneDiscapSelect) return;
        toggleVisible(bloqueDiscap, tieneDiscapSelect.value === "si");
    }

    function applyNumeroCud() {
        if (!tieneCudSelect) return;
        toggleVisible(rowNumeroCud, tieneCudSelect.value === "si");
    }

    // Estado inicial
    applyFunciones();
    applyFormacion();
    applyPuebloOriginario();
    applyDiscapacidad();
    applyNumeroCud();

    // Listeners
    if (subcomponenteSelect)  subcomponenteSelect.addEventListener("change",  applyFunciones);
    if (nivelEducativoSelect) nivelEducativoSelect.addEventListener("change",  applyFormacion);
    if (tieneDiscapSelect)    tieneDiscapSelect.addEventListener("change",    applyDiscapacidad);
    if (tieneCudSelect)       tieneCudSelect.addEventListener("change",       applyNumeroCud);

    document.querySelectorAll("#id_grupo_pertenencia input[type=checkbox]").forEach(function (cb) {
        cb.addEventListener("change", applyPuebloOriginario);
    });
}

// ─────────────────────────────────────────────────────────
// GEOGRAFÍA CONTACTO
// ─────────────────────────────────────────────────────────

function initializeGeography() {
    const provinciaSelect  = document.getElementById("id_provincia_contacto");
    const municipioSelect  = document.getElementById("id_municipio_contacto");
    const localidadSelect  = document.getElementById("id_localidad_contacto");
    const initialMunicipio = municipioSelect ? municipioSelect.value : "";
    const initialLocalidad = localidadSelect ? localidadSelect.value : "";

    function buildEmptyOption(label) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = label;
        return opt;
    }

    function resetSelect(sel, label) {
        if (!sel) return;
        sel.innerHTML = "";
        sel.appendChild(buildEmptyOption(label));
    }

    async function loadOptions(url, sel, emptyLabel) {
        if (!sel || !url) return;
        const resp = await fetch(url, {
            headers: { "X-Requested-With": "XMLHttpRequest" },
            credentials: "same-origin",
        });
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        const data = await resp.json();
        resetSelect(sel, emptyLabel);
        data.forEach(function (item) {
            const opt = document.createElement("option");
            opt.value = item.id;
            opt.textContent = item.nombre || item.nombre_region || "";
            sel.appendChild(opt);
        });
    }

    if (provinciaSelect && municipioSelect) {
        provinciaSelect.addEventListener("change", async function () {
            try {
                resetSelect(municipioSelect, "Seleccionar municipio...");
                resetSelect(localidadSelect, "Seleccionar localidad...");
                if (!this.value) return;
                await loadOptions(
                    window.ajaxLoadMunicipiosUrl + "?provincia_id=" + this.value,
                    municipioSelect, "Seleccionar municipio..."
                );
            } catch (e) { console.error("Error al cargar municipios:", e); }
        });
    }

    if (municipioSelect && localidadSelect) {
        municipioSelect.addEventListener("change", async function () {
            try {
                resetSelect(localidadSelect, "Seleccionar localidad...");
                if (!this.value) return;
                await loadOptions(
                    window.ajaxLoadLocalidadesUrl + "?municipio_id=" + this.value,
                    localidadSelect, "Seleccionar localidad..."
                );
            } catch (e) { console.error("Error al cargar localidades:", e); }
        });
    }

    if (provinciaSelect && provinciaSelect.value) {
        loadOptions(
            window.ajaxLoadMunicipiosUrl + "?provincia_id=" + provinciaSelect.value,
            municipioSelect, "Seleccionar municipio..."
        ).then(function () {
            if (initialMunicipio) municipioSelect.value = initialMunicipio;
            if (municipioSelect && municipioSelect.value && localidadSelect) {
                return loadOptions(
                    window.ajaxLoadLocalidadesUrl + "?municipio_id=" + municipioSelect.value,
                    localidadSelect, "Seleccionar localidad..."
                ).then(function () {
                    if (initialLocalidad) localidadSelect.value = initialLocalidad;
                });
            }
        }).catch(function (e) { console.error("Error al precargar ubicación:", e); });
    }
}

// ─────────────────────────────────────────────────────────
// CÁLCULO DE EDAD
// ─────────────────────────────────────────────────────────

function initializeAgeCalculation() {
    const fechaNacInput = document.getElementById("id_fecha_nacimiento");
    const edadInput     = document.getElementById("id_edad_calculada");
    if (!fechaNacInput || !edadInput) return;

    function calcular(value) {
        if (!value) { edadInput.value = ""; return; }
        const nac = new Date(value + "T00:00:00");
        if (isNaN(nac.getTime())) { edadInput.value = ""; return; }
        const hoy = new Date();
        let edad = hoy.getFullYear() - nac.getFullYear();
        const mes = hoy.getMonth() - nac.getMonth();
        if (mes < 0 || (mes === 0 && hoy.getDate() < nac.getDate())) edad--;
        edadInput.value = edad >= 0 ? edad : "";
    }

    calcular(fechaNacInput.value);
    fechaNacInput.addEventListener("change", function () { calcular(this.value); });
}
