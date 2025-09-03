document.addEventListener("DOMContentLoaded", function () {
    const addFirmanteButton = document.getElementById("add-firmante");
    const firmantesContainer = document.getElementById("firmantes-container");
    const totalForms = document.querySelector("#id_firmantes-TOTAL_FORMS");
    const tipoEntidadSelect = document.getElementById("id_tipo_entidad");
    const provinciaSelect = document.getElementById("id_provincia");
    const municipioSelect = document.getElementById("id_municipio");
    const localidadSelect = document.getElementById("id_localidad");

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





    if (!addFirmanteButton || !firmantesContainer || !totalForms) {
        console.warn("No se encontraron los elementos necesarios para el manejo de firmantes.");
        return;
    }

    // FIXME: Eliminar comentarios de GPT
    // Ajusta los roles según tu lógica de negocio
    const rolesPorTipoEntidad = {
        "Personería jurídica": ["Presidente", "Tesorero", "Secretario"],
        "Personería jurídica eclesiástica": ["Obispo", "Apoderado 1", "Apoderado 2"],
        "Asociación de hecho": ["Firmante 1", "Firmante 2"]
    };

    function actualizarRoles() {
        if (!tipoEntidadSelect || !firmantesContainer) return;
        const tipoEntidadTexto = tipoEntidadSelect.options[tipoEntidadSelect.selectedIndex]?.text;
        const rolesValidos = rolesPorTipoEntidad[tipoEntidadTexto];

        const selectsRol = firmantesContainer.querySelectorAll("select[name$='-rol']");
        selectsRol.forEach(function (select) {
            if (!select) return;
            const opciones = Array.from(select.options);

            opciones.forEach(function (opcion) {
                if (opcion.value === "") {
                    opcion.hidden = false;
                    return;
                }
                if (!rolesValidos) {
                    opcion.hidden = true;
                } else {
                    if (opcion.text === "Firmante 1" || opcion.text === "Firmante 1 (Titular de la tarjeta)") {
                        opcion.text = "Firmante 1 (Titular de la tarjeta)";
                    }
                    opcion.hidden = !rolesValidos.includes(opcion.text.replace(" (Titular de la tarjeta)", ""));
                }
            });

            if (!rolesValidos || !rolesValidos.includes(select.options[select.selectedIndex]?.text.replace(" (Titular de la tarjeta)", ""))) {
                select.selectedIndex = 0;
            }

            select.disabled = !rolesValidos;
        });
    }

    // FIXME: Utilizar otro nombre para la variable el q no se entiende
    function reindexFirmantes() {
        if (!firmantesContainer || !totalForms) return;
        const forms = firmantesContainer.querySelectorAll('.form-row');
        forms.forEach((form, idx) => {
            form.querySelectorAll('input, select, textarea, label').forEach(el => {
                if (el.name) {
                    el.name = el.name.replace(/firmantes-\d+-/, `firmantes-${idx}-`);
                }
                if (el.id) {
                    el.id = el.id.replace(/firmantes-\d+-/, `firmantes-${idx}-`);
                }
                if (el.htmlFor) {
                    el.htmlFor = el.htmlFor.replace(/firmantes-\d+-/, `firmantes-${idx}-`);
                }
            });
        });
        totalForms.value = forms.length;
    }

    addFirmanteButton.addEventListener("click", function () {
        const emptyFormDiv = document.getElementById("empty-form");
        if (!emptyFormDiv) return;
        const emptyFormTemplate = emptyFormDiv.innerHTML;
        const formHtml = emptyFormTemplate.replace(/__prefix__/g, totalForms.value);

        const tempDiv = document.createElement("div");
        tempDiv.innerHTML = formHtml;

        const newForm = tempDiv.firstElementChild;
        if (!newForm) return;

        const deleteInput = newForm.querySelector("input[type='checkbox'][name$='-DELETE']");
        if (deleteInput) {
            deleteInput.checked = false;
        }

        firmantesContainer.appendChild(newForm);

        reindexFirmantes();
        actualizarRoles();
    });

    firmantesContainer.addEventListener("click", function (e) {
        if (e.target.classList.contains("remove-firmante")) {
            if (firmantesContainer.querySelectorAll('.form-row').length > 1) {
                e.target.closest(".form-row").remove();
                reindexFirmantes();
                actualizarRoles();
            } else {
                alert("Debe haber al menos un firmante.");
            }
        }
    });

    if (tipoEntidadSelect) {
        tipoEntidadSelect.addEventListener("change", actualizarRoles);
    }

    actualizarRoles();
});

document.querySelector("form").addEventListener("submit", function (e) {
    // Elimina el empty-form si está dentro del form
    const emptyFormDiv = document.getElementById("empty-form");
    if (emptyFormDiv && emptyFormDiv.parentNode) {
        emptyFormDiv.parentNode.removeChild(emptyFormDiv);
    }

    // Limpia firmantes vacíos
    const forms = firmantesContainer.querySelectorAll('.form-row');
    forms.forEach(form => {
        const nombreInput = form.querySelector("input[name$='-nombre']");
        if (nombreInput && !nombreInput.value.trim()) {
            form.remove();
        }
    });
    reindexFirmantes();
});
