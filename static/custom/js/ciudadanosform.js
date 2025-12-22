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
            initializeSelect2AutoFocus();
        }, 500);
    });

    // ============================================
    // AUTO FOCUS EN SELECT2 SEARCH
    // ============================================

    /**
     * Inicializa el auto-focus en el campo de búsqueda de Select2
     * Cuando se abre un select2, automáticamente enfoca el input de búsqueda
     */
    function initializeSelect2AutoFocus() {
        if (!window.jQuery) return;

        window.jQuery(document).ready(function() {
            // MÉTODO 1: Listener global para capturar todos los eventos select2:open
            window.jQuery(document).on('select2:open', function() {
                // Ejecutar el enfoque de manera inmediata y con retry
                focusSelect2SearchField();
            });

            // MÉTODO 2: Observer para detectar nuevos dropdowns de Select2 en el DOM
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    mutation.addedNodes.forEach(function(node) {
                        // Si se agrega un dropdown de select2, enfocar su campo de búsqueda
                        if (node.nodeType === 1 && node.classList && node.classList.contains('select2-container--open')) {
                            focusSelect2SearchField();
                        }
                        // También verificar si es el dropdown que se abre
                        if (node.nodeType === 1 && node.classList && node.classList.contains('select2-dropdown')) {
                            focusSelect2SearchField();
                        }
                    });
                });
            });

            // Observar cambios en el body
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        });
    }

    /**
     * Función auxiliar para enfocar el campo de búsqueda de Select2 activo
     */
    function focusSelect2SearchField() {
        // Ejecutar inmediatamente
        attemptFocus();

        // Y también con un pequeño delay como backup
        setTimeout(attemptFocus, 10);
        setTimeout(attemptFocus, 50);
    }

    /**
     * Intenta enfocar el campo de búsqueda visible
     */
    function attemptFocus() {
        // Buscar TODOS los campos de búsqueda
        const searchFields = document.querySelectorAll('.select2-search__field');

        // Encontrar el que está visible
        for (let field of searchFields) {
            const isVisible = field.offsetParent !== null &&
                             window.getComputedStyle(field).display !== 'none' &&
                             window.getComputedStyle(field).visibility !== 'hidden';

            if (isVisible) {
                field.focus();
                return; // Salir después de enfocar el primero visible
            }
        }
    }

})(window, document);
