(function (window, document, $) {
    function readAvisosData() {
        const script = document.getElementById("pas-avisos-por-estado");
        if (!script) {
            return {};
        }
        try {
            return JSON.parse(script.textContent) || {};
        } catch (error) {
            console.error("No se pudo leer la configuracion de avisos PAS:", error);
            return {};
        }
    }

    function initSelect2(select) {
        if (!$ || !$.fn || !$.fn.select2 || !select) {
            return;
        }
        const $select = $(select);
        const $modal = $select.closest(".modal");
        const options = {
            width: "100%",
            allowClear: true,
            minimumResultsForSearch: 0,
            placeholder: select.multiple ? "Seleccione avisos" : "Seleccione una opcion",
        };
        if ($modal.length) {
            options.dropdownParent = $modal;
        }
        if ($select.data("select2")) {
            $select.select2("destroy");
        }
        $select.select2(options);
    }

    function populateAvisos(avisosSelect, avisos) {
        const selected = new Set(Array.from(avisosSelect.selectedOptions).map(opt => opt.value));
        avisosSelect.innerHTML = "";
        avisos.forEach((aviso) => {
            const option = document.createElement("option");
            option.value = aviso.id;
            option.textContent = aviso.text;
            if (selected.has(String(aviso.id))) {
                option.selected = true;
            }
            avisosSelect.appendChild(option);
        });
        initSelect2(avisosSelect);
        if ($ && $.fn && $.fn.select2) {
            $(avisosSelect).trigger("change.select2");
        }
    }

    function bindEstadoAvisos() {
        const data = readAvisosData();
        const estadoSelects = document.querySelectorAll("#id_estado");
        estadoSelects.forEach((estadoSelect) => {
            const form = estadoSelect.closest("form") || document;
            const avisosSelect = form.querySelector("#id_avisos");
            if (!avisosSelect) {
                return;
            }
            initSelect2(estadoSelect);
            initSelect2(avisosSelect);

            const refresh = () => {
                populateAvisos(avisosSelect, data[String(estadoSelect.value)] || []);
            };
            estadoSelect.addEventListener("change", refresh);
            if ($ && $.fn && $.fn.select2) {
                $(estadoSelect)
                    .off("select2:select.pas select2:clear.pas")
                    .on("select2:select.pas select2:clear.pas", refresh);
            }
            if (estadoSelect.value && avisosSelect.options.length === 0) {
                refresh();
            }
        });
    }

    function bindProvinciaMunicipio() {
        const provincia = document.getElementById("id_provincia");
        const municipio = document.getElementById("id_municipio");
        if (!provincia || !municipio || !window.ajaxLoadMunicipiosUrl) {
            return;
        }
        initSelect2(provincia);
        initSelect2(municipio);

        const resetMunicipio = () => {
            municipio.innerHTML = "";
            const option = document.createElement("option");
            option.value = "";
            option.textContent = "---------";
            municipio.appendChild(option);
        };

        const loadMunicipios = async () => {
            resetMunicipio();
            if (!provincia.value) {
                initSelect2(municipio);
                return;
            }
            try {
                const url = `${window.ajaxLoadMunicipiosUrl}?provincia_id=${encodeURIComponent(provincia.value)}`;
                const response = await fetch(url, {
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                    credentials: "same-origin",
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                const data = await response.json();
                data.forEach((item) => {
                    const option = document.createElement("option");
                    option.value = item.id;
                    option.textContent = item.nombre;
                    municipio.appendChild(option);
                });
            } catch (error) {
                console.error("Error al cargar municipios PAS:", error);
            } finally {
                initSelect2(municipio);
            }
        };

        provincia.addEventListener("change", loadMunicipios);
        if ($ && $.fn && $.fn.select2) {
            $(provincia)
                .off("select2:select.pasMunicipio select2:clear.pasMunicipio")
                .on("select2:select.pasMunicipio select2:clear.pasMunicipio", loadMunicipios);
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        bindEstadoAvisos();
        bindProvinciaMunicipio();
        document.querySelectorAll(".pas-select2").forEach(initSelect2);
    });
})(window, document, window.jQuery);
