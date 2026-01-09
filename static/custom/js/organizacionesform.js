document.addEventListener("DOMContentLoaded", function () {
    const tipoEntidadSelect = document.getElementById("id_tipo_entidad");
    const provinciaSelect = document.getElementById("id_provincia");
    const municipioSelect = document.getElementById("id_municipio");
    const localidadSelect = document.getElementById("id_localidad");
    const subtipoEntidadSelect = document.getElementById("id_subtipo_entidad");

    // ============================================
    // AJAX PARA UBICACIÓN (PROVINCIA, MUNICIPIO, LOCALIDAD)
    // ============================================

    if (provinciaSelect) {
        provinciaSelect.addEventListener("change", async function () {
            await cargarOpciones(
                `${ajaxLoadMunicipiosUrl}?provincia_id=${this.value}`,
                "municipio"
            ).then(async () => {
                await cargarOpciones(
                    `${ajaxLoadLocalidadesUrl}?municipio_id=${municipioSelect.options[0].value}`,
                    "localidad"
                );
            });
        });
    }

    if (municipioSelect) {
        municipioSelect.addEventListener("change", async function () {
            await cargarOpciones(
                `${ajaxLoadLocalidadesUrl}?municipio_id=${this.value}`,
                "localidad"
            );
        });
    }

    async function cargarOpciones(url, select) {
        try {
            const response = await fetch(url);
            const data = await response.json();
            if (select === "municipio") {
                municipioSelect.innerHTML = "";
                localidadSelect.innerHTML = "";
                data.forEach((item) => crearOpcion(item, municipioSelect));
            }

            if (select === "localidad") {
                localidadSelect.innerHTML = "";
                data.forEach((item) => crearOpcion(item, localidadSelect));
            }
        } catch (error) {
            console.error("Error al cargar opciones:", error);
        }
    }

    function crearOpcion({ id, nombre, nombre_region }, select) {
        const option = document.createElement("option");
        option.value = id;
        option.textContent = nombre || nombre_region;
        select.appendChild(option);
    }

    // ============================================
    // AJAX PARA SUBTIPO ENTIDAD
    // ============================================

    if (subtipoEntidadSelect) {
        subtipoEntidadSelect.innerHTML = "";
    }

    function RenderSubtipoEntidad() {
        if (!subtipoEntidadSelect) return;

        subtipoEntidadSelect.innerHTML = "";
        const tipoEntidadId = this.value ? this.value : tipoEntidadSelect.value;

        if (!tipoEntidadId) return;

        fetch(`/organizaciones/subtipos-entidad/ajax/?tipo_entidad=${tipoEntidadId}`, {
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        })
            .then(response => response.json())
            .then(result => {
                result.forEach(subtipo => {
                    const option = document.createElement("option");
                    option.value = subtipo.id;
                    option.textContent = subtipo.text;
                    subtipoEntidadSelect.appendChild(option);
                });
                // Actualizar progreso después de cargar subtipos
                updateProgress();
            })
            .catch(error => console.error("Error al cargar subtipos entidad:", error));
    }

    RenderSubtipoEntidad();

    if (tipoEntidadSelect) {
        tipoEntidadSelect.addEventListener("change", function () {
            RenderSubtipoEntidad();
        });
    }

    // ============================================
    // SISTEMA DE PROGRESO Y SECCIONES COLAPSABLES
    // ============================================

    const sections = ["basic", "contacto", "ubicacion", "vigencia"];
    const completedLabel = document.getElementById("completedSections");
    const progressBar = document.getElementById("progressBarFill");

    // Función para verificar si un campo está lleno
    function fieldFilled(field) {
        if (field.type === "checkbox" || field.type === "radio") {
            return field.checked;
        }
        if (field.type === "select-one" || field.tagName === "SELECT") {
            return field.value && field.value !== "" && field.value !== "0";
        }
        return field.value && field.value.trim() !== "";
    }

    // Actualizar el estado de una sección
    function updateSectionStatus(sectionId) {
        const statusBadge = document.getElementById("status-" + sectionId);
        const sectionBody = document.getElementById("section-" + sectionId);
        if (!sectionBody) return false;

        // Obtener todos los campos visibles (incluyendo los de crispy forms)
        const allFields = Array.from(
            sectionBody.querySelectorAll("input:not([type='hidden']), select, textarea")
        );

        // Verificar si hay al menos un campo con valor
        const hasAnyFieldFilled = allFields.some(field => fieldFilled(field));

        let state = "empty";
        let isComplete = false;

        if (hasAnyFieldFilled) {
            state = "complete";
            isComplete = true;
        } else {
            state = "empty";
            isComplete = false;
        }

        if (statusBadge) {
            statusBadge.classList.remove("complete", "incomplete", "empty");
            statusBadge.classList.add(state);

            if (state === "complete") {
                statusBadge.innerHTML = '<i class="fas fa-check-circle"></i> Completo';
            } else {
                statusBadge.innerHTML = '<i class="fas fa-circle"></i> Sin completar';
            }
        }

        return isComplete;
    }

    // Actualizar el progreso global
    function updateProgress() {
        let completed = 0;
        sections.forEach((sectionId) => {
            if (updateSectionStatus(sectionId)) {
                completed += 1;
            }
        });

        if (completedLabel) {
            completedLabel.textContent = completed;
        }
        if (progressBar) {
            const percent = sections.length ? (completed / sections.length) * 100 : 0;
            progressBar.style.width = `${percent}%`;
        }
    }

    // Agregar event listeners a todos los campos
    sections.forEach((sectionId) => {
        const sectionBody = document.getElementById("section-" + sectionId);
        if (!sectionBody) return;
        const fields = sectionBody.querySelectorAll("input, select, textarea");
        fields.forEach((field) => {
            field.addEventListener("input", updateProgress);
            field.addEventListener("change", updateProgress);
        });
    });

    // Actualizar progreso inicial con un pequeño delay para asegurar que todo esté cargado
    setTimeout(() => {
        updateProgress();
    }, 300);
});

// ============================================
// FUNCIÓN PARA TOGGLE DE SECCIONES
// ============================================

function toggleSection(sectionId) {
    const sectionBody = document.getElementById("section-" + sectionId);
    const sectionHeader = document.querySelector(`[data-section="${sectionId}"] .section-header`);

    if (!sectionBody) {
        console.error("No se encontró la sección:", sectionId);
        return;
    }

    // Toggle manual más robusto
    if (sectionBody.classList.contains("show")) {
        // Cerrar la sección
        sectionBody.style.height = sectionBody.scrollHeight + "px";

        // Forzar reflow
        sectionBody.offsetHeight;

        sectionBody.classList.add("collapsing");
        sectionBody.classList.remove("collapse", "show");
        sectionBody.style.height = "0";

        setTimeout(() => {
            sectionBody.classList.remove("collapsing");
            sectionBody.classList.add("collapse");
            sectionBody.style.height = "";
        }, 300);

        if (sectionHeader) {
            sectionHeader.classList.add("collapsed");
        }
    } else {
        // Abrir la sección
        sectionBody.classList.remove("collapse");
        sectionBody.classList.add("collapsing");
        sectionBody.style.height = "0";

        // Forzar reflow
        sectionBody.offsetHeight;

        const height = sectionBody.scrollHeight;
        sectionBody.style.height = height + "px";

        setTimeout(() => {
            sectionBody.classList.remove("collapsing");
            sectionBody.classList.add("collapse", "show");
            sectionBody.style.height = "";
        }, 300);

        if (sectionHeader) {
            sectionHeader.classList.remove("collapsed");
        }
    }
}
