document.addEventListener("DOMContentLoaded", function () {
    var provinciaSelect = document.getElementById("id_provincia");
    var municipioSelect = document.getElementById("id_municipio");
    var localidadSelect = document.getElementById("id_localidad");
    var referenteSelect = document.getElementById("id_referente");
    var referenteSearchInput = document.getElementById("id_referente_search");
    var referenteSearchResults = document.getElementById("referente-search-results");
    var addContactoBtn = document.getElementById("add-contacto-btn");
    var contactosContainer = document.getElementById("contactos-formset");
    var totalFormsInput = document.getElementById("id_contactos-TOTAL_FORMS");

    function getReferenteOptionById(id) {
        if (!window.referenteSearchOptions || !id) {
            return null;
        }

        return window.referenteSearchOptions.find(function (option) {
            return option.id === String(id);
        }) || null;
    }

    function getMatchingReferenteOptions(term) {
        var normalizedTerm = (term || "").trim().toLowerCase();
        if (!normalizedTerm || !window.referenteSearchOptions) {
            return [];
        }

        return window.referenteSearchOptions.filter(function (option) {
            return option.username.toLowerCase().includes(normalizedTerm);
        }).slice(0, 8);
    }

    function closeReferenteResults() {
        if (referenteSearchResults) {
            referenteSearchResults.hidden = true;
            referenteSearchResults.innerHTML = "";
        }
    }

    function selectReferenteOption(option) {
        if (!referenteSelect || !referenteSearchInput || !option) {
            return;
        }

        referenteSelect.value = option.id;
        referenteSearchInput.value = option.label;
        referenteSearchInput.setCustomValidity("");
        closeReferenteResults();
    }

    function renderReferenteResults(matches) {
        if (!referenteSearchResults) {
            return;
        }

        if (!matches.length) {
            referenteSearchResults.innerHTML =
                '<div class="referente-search-empty">No hay usuarios CFP para ese username.</div>';
            referenteSearchResults.hidden = false;
            return;
        }

        referenteSearchResults.innerHTML = matches.map(function (option) {
            return (
                '<button type="button" class="referente-search-option" data-referente-id="' +
                option.id +
                '">' +
                option.label +
                "</button>"
            );
        }).join("");
        referenteSearchResults.hidden = false;

        referenteSearchResults.querySelectorAll(".referente-search-option").forEach(function (button) {
            button.addEventListener("click", function () {
                var option = getReferenteOptionById(button.dataset.referenteId);
                selectReferenteOption(option);
            });
        });
    }

    function syncReferenteSelectFromSearch() {
        if (!referenteSelect || !referenteSearchInput) {
            return;
        }

        var searchTerm = referenteSearchInput.value;
        if (!searchTerm.trim()) {
            referenteSelect.value = "";
            referenteSearchInput.setCustomValidity("");
            closeReferenteResults();
            return;
        }

        referenteSelect.value = "";
        referenteSearchInput.setCustomValidity("");
        renderReferenteResults(getMatchingReferenteOptions(searchTerm));
    }

    function syncReferenteSearchFromSelect() {
        if (!referenteSelect || !referenteSearchInput) {
            return;
        }

        var selectedOption = referenteSelect.options[referenteSelect.selectedIndex];
        if (selectedOption && selectedOption.value) {
            referenteSearchInput.value = selectedOption.textContent.trim();
        } else {
            referenteSearchInput.value = "";
        }
        referenteSearchInput.setCustomValidity("");
        closeReferenteResults();
    }

    if (referenteSelect && referenteSearchInput) {
        syncReferenteSearchFromSelect();
        referenteSearchInput.addEventListener("input", syncReferenteSelectFromSearch);
        referenteSearchInput.addEventListener("focus", function () {
            if (referenteSearchInput.value.trim() && !referenteSelect.value) {
                renderReferenteResults(
                    getMatchingReferenteOptions(referenteSearchInput.value)
                );
            }
        });
        referenteSearchInput.addEventListener("blur", function () {
            window.setTimeout(closeReferenteResults, 150);
        });
        referenteSelect.form.addEventListener("submit", function (event) {
            if (!referenteSelect.value) {
                referenteSearchInput.setCustomValidity(
                    "Seleccioná un referente válido de la lista."
                );
                referenteSearchInput.reportValidity();
                event.preventDefault();
            } else {
                referenteSearchInput.setCustomValidity("");
            }
        });
    }

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
