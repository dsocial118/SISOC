document.addEventListener("DOMContentLoaded", function () {
    var provinciaSelect = document.getElementById("id_provincia");
    var municipioSelect = document.getElementById("id_municipio");
    var localidadSelect = document.getElementById("id_localidad");
    var addContactoBtn = document.getElementById("add-contacto-btn");
    var contactosContainer = document.getElementById("contactos-formset");
    var totalFormsInput = document.getElementById("id_contactos-TOTAL_FORMS");

    function buildEmptyOption(label) {
        var option = document.createElement("option");
        option.value = "";
        option.textContent = label;
        return option;
    }

    function loadOptions(url, targetSelect, emptyLabel, mapValue) {
        if (!targetSelect) {
            return;
        }
        targetSelect.innerHTML = "";
        targetSelect.appendChild(buildEmptyOption(emptyLabel));

        fetch(url)
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                data.forEach(function (item) {
                    var option = document.createElement("option");
                    option.value = item.id;
                    option.textContent = item.nombre;
                    if (mapValue) {
                        option.dataset.municipioId = item.id;
                    }
                    targetSelect.appendChild(option);
                });
            });
    }

    if (provinciaSelect && municipioSelect) {
        provinciaSelect.addEventListener("change", function () {
            if (!this.value) {
                municipioSelect.innerHTML = "";
                municipioSelect.appendChild(buildEmptyOption("Seleccionar municipio..."));
                localidadSelect.innerHTML = "";
                localidadSelect.appendChild(buildEmptyOption("Seleccionar localidad..."));
                return;
            }
            loadOptions(
                ajaxLoadMunicipiosUrl + "?provincia_id=" + this.value,
                municipioSelect,
                "Seleccionar municipio...",
                true
            );
        });
    }

    if (municipioSelect && localidadSelect) {
        municipioSelect.addEventListener("change", function () {
            if (!this.value) {
                localidadSelect.innerHTML = "";
                localidadSelect.appendChild(buildEmptyOption("Seleccionar localidad..."));
                return;
            }
            loadOptions(
                ajaxLoadLocalidadesUrl + "?municipio_id=" + this.value,
                localidadSelect,
                "Seleccionar localidad..."
            );
        });
    }

    function reindexContactForms() {
        var forms = contactosContainer.querySelectorAll(".contacto-form-item");
        forms.forEach(function (item, index) {
            item.dataset.formIndex = String(index);
            item.querySelectorAll("input, select, textarea, label").forEach(function (element) {
                ["name", "id", "for"].forEach(function (attribute) {
                    var value = element.getAttribute(attribute);
                    if (!value) {
                        return;
                    }
                    element.setAttribute(
                        attribute,
                        value.replace(/contactos-(\d+|__prefix__)-/g, "contactos-" + index + "-")
                    );
                });
            });
        });

        if (totalFormsInput) {
            totalFormsInput.value = forms.length;
        }
    }

    function bindRemoveButtons(scope) {
        scope.querySelectorAll(".remove-contacto-btn").forEach(function (button) {
            button.onclick = function () {
                var items = contactosContainer.querySelectorAll(".contacto-form-item");
                if (items.length <= 1) {
                    return;
                }
                button.closest(".contacto-form-item").remove();
                reindexContactForms();
            };
        });
    }

    if (addContactoBtn && contactosContainer && totalFormsInput) {
        addContactoBtn.addEventListener("click", function () {
            var formIndex = Number(totalFormsInput.value || 0);
            var wrapper = document.createElement("div");
            wrapper.className = "border rounded p-3 mb-3 contacto-form-item";
            wrapper.dataset.formIndex = String(formIndex);
            wrapper.innerHTML = contactoEmptyFormHtml.replace(/__prefix__/g, String(formIndex));
            contactosContainer.appendChild(wrapper);
            reindexContactForms();
            bindRemoveButtons(wrapper);
        });

        bindRemoveButtons(contactosContainer);
        reindexContactForms();
    }
});