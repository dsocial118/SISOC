$(document).ready(function () {
    const addFirmanteButton = document.getElementById("add-firmante");
    const firmantesContainer = document.getElementById("firmantes-container");
    const totalForms = document.querySelector("#id_firmantes-TOTAL_FORMS");
    const tipoOrgSelect = document.getElementById("id_tipo_organizacion");

    if (!addFirmanteButton || !firmantesContainer || !totalForms) {
        console.warn("No se encontraron los elementos necesarios para el manejo de firmantes.");
        return;
    }

    const rolesPorTipoOrg = {
        "Personería jurídica": ["Presidente", "Tesorero", "Secretario"],
        "Personería jurídica eclesiástica": ["Obispo", "Apoderado 1", "Apoderado 2"],
        "Asociación de hecho": ["Firmante 1", "Firmante 2"]
    };

    function actualizarRoles() {
        if (!tipoOrgSelect || !firmantesContainer) return;
        const tipoOrgTexto = tipoOrgSelect.options[tipoOrgSelect.selectedIndex]?.text;
        const rolesValidos = rolesPorTipoOrg[tipoOrgTexto];

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
            } else {
                alert("Debe haber al menos un firmante.");
            }
        }
    });

    if (tipoOrgSelect) {
        tipoOrgSelect.addEventListener("change", actualizarRoles);
    }

    actualizarRoles();
});