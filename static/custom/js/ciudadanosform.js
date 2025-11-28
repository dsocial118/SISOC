(function (window, document) {
    "use strict";

    const SELECTORS = {
        provincia: "#id_provincia",
        municipio: "#id_municipio",
        localidad: "#id_localidad",
        nacionalidad: "#id_nacionalidad",
        form: "form[data-ajax-municipios-url][data-ajax-localidades-url]",
    };

    const UI = {
        provincia: { wrapper: "#provincia-field", dropdownParent: "#provincia-field" },
        municipio: { wrapper: "#municipio-field", loader: "#municipio-loader", dropdownParent: "#municipio-field" },
        localidad: { wrapper: "#localidad-field", loader: "#localidad-loader", dropdownParent: "#localidad-field" },
    };

    const PLACEHOLDERS = {
        provincia: "Seleccione una provincia",
        municipio: "Seleccione un municipio",
        localidad: "Seleccione una localidad",
        nacionalidad: "Seleccione una nacionalidad",
    };

    function getConfig() {
        const form = document.querySelector(SELECTORS.form);
        const ajaxMunicipios = typeof window.ajaxLoadMunicipiosUrl !== "undefined"
            ? window.ajaxLoadMunicipiosUrl
            : form?.dataset.ajaxMunicipiosUrl;
        const ajaxLocalidades = typeof window.ajaxLoadLocalidadesUrl !== "undefined"
            ? window.ajaxLoadLocalidadesUrl
            : form?.dataset.ajaxLocalidadesUrl;
        if (!ajaxMunicipios || !ajaxLocalidades) return null;

        return {
            ajaxMunicipiosUrl: ajaxMunicipios,
            ajaxLocalidadesUrl: ajaxLocalidades,
            selectors: {
                provincia: SELECTORS.provincia,
                municipio: SELECTORS.municipio,
                localidad: SELECTORS.localidad,
            },
            ui: UI,
            placeholders: PLACEHOLDERS,
        };
    }

    function initNacionalidadSelect(config) {
        if (!window.jQuery || !window.jQuery.fn || !window.jQuery.fn.select2) {
            return;
        }
        const $nacionalidad = window.jQuery(SELECTORS.nacionalidad);
        if (!$nacionalidad.length) return;
        $nacionalidad.select2({
            placeholder: config.placeholders.nacionalidad,
            allowClear: true,
            width: "100%",
        });
    }

    async function initUbicacion(config) {
        const runConfig = {
            ...config,
            ui: {
                provincia: config.ui.provincia,
                municipio: {
                    wrapper: "#municipio-field",
                    loader: "#municipio-loader",
                    dropdownParent: "#municipio-field",
                },
                localidad: {
                    wrapper: "#localidad-field",
                    loader: "#localidad-loader",
                    dropdownParent: "#localidad-field",
                },
            },
            autoPrefetch: true,
        };

        const initHelper = window.setupUbicacionSelects || window.initUbicacionSelects;
        if (typeof initHelper === "function") {
            await initHelper(runConfig);
            return;
        }
    }

    document.addEventListener("DOMContentLoaded", async function () {
        const config = getConfig();
        if (!config) return;

        // Emular el comportamiento de comedores: pequeño delay antes de inicializar
        setTimeout(async () => {
            await initUbicacion(config);
            initNacionalidadSelect(config);
        }, 500);
    });
})(window, document);
