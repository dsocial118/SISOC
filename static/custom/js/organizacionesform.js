$(document).ready(function () {
    const addFirmanteButton = document.getElementById("add-firmante");
    const firmantesContainer = document.getElementById("firmantes-container");
    const totalForms = document.querySelector("#id_firmantes-TOTAL_FORMS");
    const tipoOrgSelect = document.getElementById("id_tipo_organizacion");

    const rolesPorTipoOrg = {
        "Personería jurídica": ["Presidente", "Tesorero", "Secretario"],
        "Personería jurídica eclesiástica": ["Obispo", "Apoderado 1", "Apoderado 2"],
        "Asociación de hecho": ["Firmante 1", "Firmante 2"]
    };

    function actualizarRoles() {
        const tipoOrgTexto = tipoOrgSelect.options[tipoOrgSelect.selectedIndex]?.text;
        const rolesValidos = rolesPorTipoOrg[tipoOrgTexto];

        const selectsRol = firmantesContainer.querySelectorAll("select[name$='-rol']");
        selectsRol.forEach(function (select) {
            const opciones = Array.from(select.options);

            // Mostrar solo las opciones válidas, ocultar el resto
            opciones.forEach(function (opcion) {
                if (opcion.value === "") {
                    opcion.hidden = false;
                    return;
                }
                if (!rolesValidos) {
                    opcion.hidden = true;
                } else {
                    // Agregar leyenda "Titular de la tarjeta" a "Firmante 1"
                    if (opcion.text === "Firmante 1" || opcion.text === "Firmante 1 (Titular de la tarjeta)") {
                        opcion.text = "Firmante 1 (Titular de la tarjeta)";
                    }
                    opcion.hidden = !rolesValidos.includes(opcion.text.replace(" (Titular de la tarjeta)", ""));
                }
            });

            // Resetear si la opción no es válida
            if (!rolesValidos || !rolesValidos.includes(select.options[select.selectedIndex]?.text.replace(" (Titular de la tarjeta)", ""))) {
                select.selectedIndex = 0;
            }

            // Deshabilitar el select si no hay tipo de organización
            select.disabled = !rolesValidos;
        });
    }

    // Clonado del formulario de firmante
    addFirmanteButton.addEventListener("click", function () {
        const emptyFormTemplate = document.getElementById("empty-form").innerHTML;
        const formHtml = emptyFormTemplate.replace(/__prefix__/g, totalForms.value);

        const tempDiv = document.createElement("div");
        tempDiv.innerHTML = formHtml;

        const newForm = tempDiv.firstElementChild;
        firmantesContainer.appendChild(newForm);

        totalForms.value = parseInt(totalForms.value) + 1;

        actualizarRoles(); // Para actualizar roles según tipo de organización
    });

    // Eliminación de firmante
    firmantesContainer.addEventListener("click", function (e) {
        if (e.target.classList.contains("remove-firmante")) {
            if (firmantesContainer.children.length > 1) {
                e.target.closest(".form-row").remove();
                totalForms.value = parseInt(totalForms.value) - 1;
            } else {
                alert("Debe haber al menos un firmante.");
            }
        }
    });

    // Evento de cambio del tipo de organización
    tipoOrgSelect.addEventListener("change", actualizarRoles);

    // Ejecutar al cargar para editar
    actualizarRoles();
});