/**
 * DESTINATARIO CDI FORM - JAVASCRIPT
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

const TOTAL_SECTIONS = 10;

function initializeProgressTracking() {
    updateProgress();
    const form = document.getElementById("destinatarioForm");
    if (form) {
        form.addEventListener("input",  updateProgress);
        form.addEventListener("change", updateProgress);
    }
}

function updateProgress() {
    const sections = {
        registro:      checkSectionRegistro(),
        nino:          checkSectionNino(),
        responsable1:  checkSectionResponsable1(),
        responsable2:  checkSectionResponsable2(),
        domicilio:     checkSectionDomicilio(),
        cultura:       checkSectionCultura(),
        discapacidad:  checkSectionDiscapacidad(),
        salud:         checkSectionSalud(),
        nutricion:     checkSectionNutricion(),
        vacunacion:    checkSectionVacunacion(),
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

function checkSectionRegistro() {
    return val("id_tipo_registro") !== "" || val("id_fecha_registro") !== "";
}

function checkSectionNino() {
    return val("id_nombre") !== "" && val("id_apellido") !== "" && val("id_dni") !== "";
}

function checkSectionResponsable1() {
    return val("id_responsable_legal_1_relacion") !== "" && val("id_responsable_legal_1_apellido") !== "";
}

function checkSectionResponsable2() {
    // sección opcional: completa si está vacía o si tiene relación + apellido
    const relacion  = val("id_responsable_legal_2_relacion");
    const apellido  = val("id_responsable_legal_2_apellido");
    const hasSomeData = hasSectionData("responsable2");
    if (!hasSomeData) return true;
    return relacion !== "" && apellido !== "";
}

function checkSectionDomicilio() {
    return val("id_calle_domicilio") !== "" || val("id_localidad_domicilio") !== "";
}

function checkSectionCultura() {
    const checked = document.querySelectorAll("#id_grupo_pertenencia input[type=checkbox]:checked");
    return checked.length > 0;
}

function checkSectionDiscapacidad() {
    return val("id_tiene_discapacidad") !== "";
}

function checkSectionSalud() {
    return val("id_cobertura_salud") !== "";
}

function checkSectionNutricion() {
    return val("id_lactancia") !== "" || val("id_diagnostico_peso") !== "";
}

function checkSectionVacunacion() {
    const dosisCodes = [
        "bcg", "neumococo", "quintuple", "polio", "rotavirus", "meningococo",
        "antigripal", "hepatitis_a", "triple_viral", "varicela",
        "triple_bacteriana_celular", "triple_bacteriana_acelular",
        "sincicial_respiratorio", "fiebre_amarilla",
    ];
    return dosisCodes.some(function (code) {
        return val("id_vacuna_" + code + "_dosis") !== "";
    }) || val("id_recibe_apoyo_desarrollo") !== "";
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

function toggleVisible(el, show) {
    if (el) el.classList.toggle("d-none", !show);
}

function getCheckedValues(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return [];
    return [...container.querySelectorAll("input[type=checkbox]:checked")].map(cb => cb.value);
}

function initializeConditionalFields() {
    const tieneDiscapSelect = document.getElementById("id_tiene_discapacidad");
    const bloqueDiscap      = document.getElementById("bloque-discapacidad");
    const posee_cudSelect   = document.getElementById("id_posee_cud");
    const rowNumeroCud      = document.getElementById("row-numero-cud");
    const rowPuebloOrig     = document.getElementById("row-pueblo-originario");

    function applyPuebloOriginario() {
        const vals = getCheckedValues("id_grupo_pertenencia");
        toggleVisible(rowPuebloOrig, vals.includes("indigena"));
    }

    function applyDiscapacidad() {
        if (!tieneDiscapSelect) return;
        toggleVisible(bloqueDiscap, tieneDiscapSelect.value === "si");
    }

    function applyNumeroCud() {
        if (!posee_cudSelect) return;
        toggleVisible(rowNumeroCud, posee_cudSelect.value === "si");
    }

    // Estado inicial
    applyPuebloOriginario();
    applyDiscapacidad();
    applyNumeroCud();

    // Listeners
    if (tieneDiscapSelect) tieneDiscapSelect.addEventListener("change", applyDiscapacidad);
    if (posee_cudSelect)   posee_cudSelect.addEventListener("change",   applyNumeroCud);

    document.querySelectorAll("#id_grupo_pertenencia input[type=checkbox]").forEach(function (cb) {
        cb.addEventListener("change", applyPuebloOriginario);
    });
}

// ─────────────────────────────────────────────────────────
// GEOGRAFÍA DOMICILIO
// ─────────────────────────────────────────────────────────

function initializeGeography() {
    const provinciaSelect  = document.getElementById("id_provincia_domicilio");
    const municipioSelect  = document.getElementById("id_municipio_domicilio");
    const localidadSelect  = document.getElementById("id_localidad_domicilio");
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
// CÁLCULO DE EDAD (con unidad meses/años)
// ─────────────────────────────────────────────────────────

function initializeAgeCalculation() {
    const fechaNacInput  = document.getElementById("id_fecha_nacimiento");
    const edadInput      = document.getElementById("id_edad_calculada");
    const edadUnidadSel  = document.getElementById("id_edad_unidad");
    if (!fechaNacInput || !edadInput) return;

    function calcular(value) {
        if (!value) { edadInput.value = ""; return; }
        const nac = new Date(value + "T00:00:00");
        if (isNaN(nac.getTime())) { edadInput.value = ""; return; }
        const hoy    = new Date();
        let anios    = hoy.getFullYear() - nac.getFullYear();
        const mes    = hoy.getMonth() - nac.getMonth();
        if (mes < 0 || (mes === 0 && hoy.getDate() < nac.getDate())) anios--;

        if (anios < 1) {
            // calcular en meses
            let meses = (hoy.getFullYear() - nac.getFullYear()) * 12 + (hoy.getMonth() - nac.getMonth());
            if (hoy.getDate() < nac.getDate()) meses--;
            edadInput.value = meses >= 0 ? meses : 0;
            if (edadUnidadSel) edadUnidadSel.value = "meses";
        } else {
            edadInput.value = anios;
            if (edadUnidadSel) edadUnidadSel.value = "anios";
        }
    }

    calcular(fechaNacInput.value);
    fechaNacInput.addEventListener("change", function () { calcular(this.value); });
}
