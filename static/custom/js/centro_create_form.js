document.addEventListener("DOMContentLoaded", function () {
    var provinciaSelect = document.getElementById("id_provincia");
    var municipioSelect = document.getElementById("id_municipio");
    var localidadSelect = document.getElementById("id_localidad");
    var referentesSelect = document.getElementById("id_referentes");
    var revisoresSelect = document.getElementById("id_revisores");
    var addContactoBtn = document.getElementById("add-contacto-btn");
    var contactosContainer = document.getElementById("contactos-formset");
    var totalFormsInput = document.getElementById("id_contactos-TOTAL_FORMS");

    function getOptionById(options, id) {
        return (options || []).find(function (option) {
            return option.id === String(id);
        }) || null;
    }

    function escapeHtml(value) {
        return String(value || "").replace(/[&<>"']/g, function (character) {
            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"
            }[character];
        });
    }

    function getSelectedValues(selectElement) {
        if (!selectElement) {
            return [];
        }
        return Array.from(selectElement.selectedOptions).map(function (option) {
            return option.value;
        });
    }

    function getMatchingUserOptions(options, term, selectedValues) {
        var normalizedTerm = (term || "").trim().toLowerCase();
        if (!normalizedTerm || !options) {
            return [];
        }

        return options.filter(function (option) {
            var matchesTerm = option.username.toLowerCase().includes(normalizedTerm) ||
                option.label.toLowerCase().includes(normalizedTerm);
            return matchesTerm && selectedValues.indexOf(option.id) === -1;
        }).slice(0, 8);
    }

    function closeUserResults(resultsElement) {
        if (resultsElement) {
            resultsElement.hidden = true;
            resultsElement.innerHTML = "";
        }
    }

    function renderSelectedChips(config) {
        if (!config.selectedContainer || !config.selectElement) {
            return;
        }
        var selectedValues = getSelectedValues(config.selectElement);
        config.selectedContainer.innerHTML = selectedValues.map(function (id) {
            var option = getOptionById(config.options, id);
            if (!option) {
                return "";
            }
            var escapedId = escapeHtml(option.id);
            var escapedLabel = escapeHtml(option.label);
            return (
                '<span class="referente-selected-chip">' +
                escapedLabel +
                '<button type="button" class="referente-chip-remove" aria-label="Quitar" data-user-id="' +
                escapedId +
                '">&times;</button></span>'
            );
        }).join("");

        config.selectedContainer.querySelectorAll(".referente-chip-remove").forEach(function (button) {
            button.addEventListener("click", function () {
                var optionElement = config.selectElement.querySelector(
                    'option[value="' + button.dataset.userId + '"]'
                );
                if (optionElement) {
                    optionElement.selected = false;
                }
                renderSelectedChips(config);
            });
        });
    }

    function selectUserOption(config, option) {
        if (!config.selectElement || !config.searchInput || !option) {
            return;
        }

        var optionElement = config.selectElement.querySelector(
            'option[value="' + option.id + '"]'
        );
        if (optionElement) {
            optionElement.selected = true;
        }
        config.searchInput.value = "";
        config.searchInput.setCustomValidity("");
        renderSelectedChips(config);
        closeUserResults(config.resultsElement);
    }

    function renderUserResults(config, matches) {
        if (!config.resultsElement) {
            return;
        }

        if (!matches.length) {
            config.resultsElement.innerHTML =
                '<div class="referente-search-empty">' +
                escapeHtml(config.emptyMessage) +
                "</div>";
            config.resultsElement.hidden = false;
            return;
        }

        config.resultsElement.innerHTML = matches.map(function (option) {
            var escapedId = escapeHtml(option.id);
            var escapedLabel = escapeHtml(option.label);
            return (
                '<button type="button" class="referente-search-option" data-user-id="' +
                escapedId +
                '">' +
                escapedLabel +
                "</button>"
            );
        }).join("");
        config.resultsElement.hidden = false;

        config.resultsElement.querySelectorAll(".referente-search-option").forEach(function (button) {
            button.addEventListener("click", function () {
                selectUserOption(config, getOptionById(config.options, button.dataset.userId));
            });
        });
    }

    function syncUserSelectFromSearch(config) {
        if (!config.selectElement || !config.searchInput) {
            return;
        }

        var searchTerm = config.searchInput.value;
        if (!searchTerm.trim()) {
            config.searchInput.setCustomValidity("");
            closeUserResults(config.resultsElement);
            return;
        }

        config.searchInput.setCustomValidity("");
        renderUserResults(
            config,
            getMatchingUserOptions(
                config.options,
                searchTerm,
                getSelectedValues(config.selectElement)
            )
        );
    }

    function bindUserMultiSearch(config) {
        if (!config.selectElement || !config.searchInput) {
            return;
        }
        renderSelectedChips(config);
        config.searchInput.addEventListener("input", function () {
            syncUserSelectFromSearch(config);
        });
        config.searchInput.addEventListener("focus", function () {
            if (config.searchInput.value.trim()) {
                renderUserResults(
                    config,
                    getMatchingUserOptions(
                        config.options,
                        config.searchInput.value,
                        getSelectedValues(config.selectElement)
                    )
                );
            }
        });
        config.searchInput.addEventListener("blur", function () {
            window.setTimeout(function () {
                closeUserResults(config.resultsElement);
            }, 150);
        });
        config.selectElement.form.addEventListener("submit", function (event) {
            if (config.required && getSelectedValues(config.selectElement).length === 0) {
                config.searchInput.setCustomValidity(
                    "Selecciona al menos un usuario valido de la lista."
                );
                config.searchInput.reportValidity();
                event.preventDefault();
            } else {
                config.searchInput.setCustomValidity("");
            }
        });
    }

    bindUserMultiSearch({
        selectElement: referentesSelect,
        searchInput: document.getElementById("id_referentes_search"),
        resultsElement: document.getElementById("referentes-search-results"),
        selectedContainer: document.getElementById("referentes-selected-items"),
        options: window.referenteSearchOptions || [],
        emptyMessage: "No hay usuarios CFP para esa busqueda.",
        required: true
    });

    bindUserMultiSearch({
        selectElement: revisoresSelect,
        searchInput: document.getElementById("id_revisores_search"),
        resultsElement: document.getElementById("revisores-search-results"),
        selectedContainer: document.getElementById("revisores-selected-items"),
        options: window.revisorSearchOptions || [],
        emptyMessage: "No hay usuarios CFPRevisor para esa busqueda.",
        required: false
    });

    function buildEmptyOption(label) {
        var option = document.createElement("option");
        option.value = "";
        option.textContent = label;
        return option;
    }

    function refreshSelect2(targetSelect) {
        if (!targetSelect || !window.refreshSelect2Element) {
            return;
        }

        window.refreshSelect2Element(targetSelect);
    }

    // Select2 dispara eventos "change" de jQuery, que no ejecutan listeners
    // nativos (addEventListener). Se bindea via jQuery cuando existe para
    // cubrir ambos casos; los handlers jQuery tambien reciben el change nativo.
    function bindSelectChange(selectElement, handler) {
        if (!selectElement) {
            return;
        }
        if (window.jQuery) {
            window.jQuery(selectElement).on("change", handler);
            return;
        }
        selectElement.addEventListener("change", handler);
    }

    function loadOptions(url, targetSelect, emptyLabel, mapValue) {
        if (!targetSelect) {
            return;
        }
        targetSelect.innerHTML = "";
        targetSelect.appendChild(buildEmptyOption(emptyLabel));
        refreshSelect2(targetSelect);

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
                refreshSelect2(targetSelect);
            });
    }

    if (provinciaSelect && municipioSelect) {
        bindSelectChange(provinciaSelect, function () {
            if (!this.value) {
                municipioSelect.innerHTML = "";
                municipioSelect.appendChild(buildEmptyOption("Seleccionar municipio..."));
                localidadSelect.innerHTML = "";
                localidadSelect.appendChild(buildEmptyOption("Seleccionar localidad..."));
                refreshSelect2(municipioSelect);
                refreshSelect2(localidadSelect);
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
        bindSelectChange(municipioSelect, function () {
            if (!this.value) {
                localidadSelect.innerHTML = "";
                localidadSelect.appendChild(buildEmptyOption("Seleccionar localidad..."));
                refreshSelect2(localidadSelect);
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
