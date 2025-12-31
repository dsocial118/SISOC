/**
 * Gestor reutilizable para selects de Provincia/Municipio/Localidad
 * Requiere jQuery + Select2 (opcional). Funciona aunque Select2 no esté presente.
 */
(function (window, document, $) {
    const DEFAULT_PLACEHOLDERS = {
        default: "Seleccione una opción",
        provincia: "Seleccione una provincia",
        municipio: "Seleccione un municipio",
        localidad: "Seleccione una localidad",
    };

    const EMPTY_OPTION_LABEL = "---------";
    const CACHE_STORAGE_KEY = "ubicacionSelectsCache";

    function createCacheStore() {
        const memory = { municipios: {}, localidades: {} };
        let storageSnapshot = null;

        const baseSnapshot = () => ({ municipios: {}, localidades: {} });

        const parseStorage = (raw) => {
            if (!raw) return baseSnapshot();
            try {
                const parsed = JSON.parse(raw);
                return {
                    municipios: parsed.municipios || {},
                    localidades: parsed.localidades || {},
                };
            } catch (error) {
                console.warn("[UbicacionSelects] No se pudo leer el cache, se reinicia:", error);
                return baseSnapshot();
            }
        };

        const readStorage = () => {
            if (storageSnapshot) return storageSnapshot;
            if (typeof sessionStorage === "undefined") {
                storageSnapshot = baseSnapshot();
                return storageSnapshot;
            }
            try {
                storageSnapshot = parseStorage(sessionStorage.getItem(CACHE_STORAGE_KEY));
            } catch (error) {
                storageSnapshot = baseSnapshot();
            }
            return storageSnapshot;
        };

        const writeStorage = (data) => {
            storageSnapshot = data;
            if (typeof sessionStorage === "undefined") return;
            try {
                sessionStorage.setItem(CACHE_STORAGE_KEY, JSON.stringify(storageSnapshot));
            } catch (error) {
                // Puede fallar en navegación privada o si se llena el storage; no es crítico.
            }
        };

        const get = (scope, key) => {
            if (!scope || !key) return null;
            if (memory[scope] && memory[scope][key]) {
                return memory[scope][key];
            }
            const storageData = readStorage();
            const value = storageData?.[scope]?.[key];
            if (value) {
                memory[scope][key] = value;
                return value;
            }
            return null;
        };

        const set = (scope, key, value) => {
            if (!scope || !key || !Array.isArray(value)) return;
            if (!memory[scope]) memory[scope] = {};
            memory[scope][key] = value;

            const storageData = readStorage();
            storageData[scope] = storageData[scope] || {};
            storageData[scope][key] = value;
            writeStorage(storageData);
        };

        return { get, set };
    }

    const ubicacionCache = createCacheStore();

    function defaultSorter(a, b) {
        const nameA = (a.nombre || a.nombre_region || "").toUpperCase();
        const nameB = (b.nombre || b.nombre_region || "").toUpperCase();
        return nameA.localeCompare(nameB);
    }

    function UbicacionSelects(config = {}) {
        this.config = Object.assign(
            {
                selectors: {
                    provincia: "#id_provincia",
                    municipio: "#id_municipio",
                    localidad: "#id_localidad",
                },
                ajaxMunicipiosUrl: null,
                ajaxLocalidadesUrl: null,
                placeholders: {},
                allowClear: {
                    provincia: true,
                    municipio: true,
                    localidad: true,
                },
                ui: {
                    provincia: {},
                    municipio: {},
                    localidad: {},
                },
                autoPrefetch: true,
                sorter: defaultSorter,
            },
            config
        );

        this.placeholders = Object.assign(
            {},
            DEFAULT_PLACEHOLDERS,
            this.config.placeholders || {}
        );

        this.ui = this.config.ui || {};
        this.sorter = typeof this.config.sorter === "function" ? this.config.sorter : defaultSorter;

        this.$ = $; // Referencia a jQuery (puede ser undefined)
        this.selects = {
            provincia: document.querySelector(this.config.selectors.provincia),
            municipio: document.querySelector(this.config.selectors.municipio),
            localidad: document.querySelector(this.config.selectors.localidad),
        };
        this.cache =
            ubicacionCache || {
                get: function () {
                    return null;
                },
                set: function () {},
            };
    }

    UbicacionSelects.prototype.init = async function () {
        if (!this.selects.provincia || !this.selects.municipio || !this.selects.localidad) {
            console.warn("[UbicacionSelects] No se encontraron los selects requeridos");
            return;
        }

        if (!this.config.ajaxMunicipiosUrl || !this.config.ajaxLocalidadesUrl) {
            console.warn("[UbicacionSelects] Debes definir ajaxMunicipiosUrl y ajaxLocalidadesUrl");
            return;
        }

        this.applySelect2("provincia");
        this.applySelect2("municipio");
        this.applySelect2("localidad");

        this.bindEvents();

        if (this.config.autoPrefetch) {
            await this.prefetchExistingValues();
        }
    };

    UbicacionSelects.prototype.bindEvents = function () {
        const handleProvinciaChange = () => {
            const provinciaId = this.selects.provincia.value;
            this.loadMunicipios(provinciaId);
        };

        const handleMunicipioChange = () => {
            const municipioId = this.selects.municipio.value;
            this.loadLocalidades(municipioId);
        };

        this.handlers = {
            provinciaChange: handleProvinciaChange,
            municipioChange: handleMunicipioChange,
        };

        this.selects.provincia.addEventListener("change", handleProvinciaChange);
        this.selects.municipio.addEventListener("change", handleMunicipioChange);

        if (this.$) {
            this.$(this.selects.provincia)
                .off("select2:select select2:clear", handleProvinciaChange)
                .on("select2:select select2:clear", handleProvinciaChange);

            this.$(this.selects.municipio)
                .off("select2:select select2:clear", handleMunicipioChange)
                .on("select2:select select2:clear", handleMunicipioChange);
        }
    };

    UbicacionSelects.prototype.prefetchExistingValues = async function () {
        const provinciaValue = this.selects.provincia.value;
        const municipioValue = this.selects.municipio.value;

        if (provinciaValue && this.shouldFetch("municipio")) {
            await this.loadMunicipios(provinciaValue, { preserveValue: true });
        }

        if (municipioValue && this.shouldFetch("localidad")) {
            await this.loadLocalidades(municipioValue, { preserveValue: true });
        }
    };

    UbicacionSelects.prototype.shouldFetch = function (key) {
        const selectEl = this.selects[key];
        if (!selectEl) return false;
        // Si sólo tiene la opción vacía, necesitamos cargar datos
        return selectEl.options.length <= 1;
    };

    UbicacionSelects.prototype.loadMunicipios = async function (provinciaId, options = {}) {
        this.resetSelect("municipio");
        this.resetSelect("localidad");

        if (!provinciaId) {
            return;
        }

        const cacheKey = String(provinciaId);
        const cachedMunicipios = this.cache.get("municipios", cacheKey);
        if (cachedMunicipios && Array.isArray(cachedMunicipios)) {
            this.populateSelect(
                this.selects.municipio,
                cachedMunicipios,
                this.selects.municipio.value,
                Boolean(options.preserveValue)
            );
            this.applySelect2("municipio");
            return;
        }

        const url = `${this.config.ajaxMunicipiosUrl}?provincia_id=${encodeURIComponent(provinciaId)}`;
        await this.fetchOptions(url, "municipio", {
            ...options,
            cacheScope: "municipios",
            cacheKey,
        });
    };

    UbicacionSelects.prototype.loadLocalidades = async function (municipioId, options = {}) {
        this.resetSelect("localidad");

        if (!municipioId) {
            return;
        }

        const cacheKey = String(municipioId);
        const cachedLocalidades = this.cache.get("localidades", cacheKey);
        if (cachedLocalidades && Array.isArray(cachedLocalidades)) {
            this.populateSelect(
                this.selects.localidad,
                cachedLocalidades,
                this.selects.localidad.value,
                Boolean(options.preserveValue)
            );
            this.applySelect2("localidad");
            return;
        }

        const url = `${this.config.ajaxLocalidadesUrl}?municipio_id=${encodeURIComponent(municipioId)}`;
        await this.fetchOptions(url, "localidad", {
            ...options,
            cacheScope: "localidades",
            cacheKey,
        });
    };

    UbicacionSelects.prototype.resetSelect = function (key) {
        const selectEl = this.selects[key];
        if (!selectEl) return;

        selectEl.innerHTML = "";
        const emptyOption = document.createElement("option");
        emptyOption.value = "";
        emptyOption.textContent = EMPTY_OPTION_LABEL;
        selectEl.appendChild(emptyOption);

        selectEl.value = "";
        selectEl.disabled = false;

        if (this.$ && this.$.fn && this.$.fn.select2) {
            this.$(selectEl).val("").trigger("change.select2");
        }
    };

    UbicacionSelects.prototype.fetchOptions = async function (url, key, options = {}) {
        const selectEl = this.selects[key];
        if (!selectEl) return;

        const preserveValue = Boolean(options.preserveValue);
        const previousValue = preserveValue ? selectEl.value : "";
        const cacheScope = options.cacheScope;
        const cacheKey = options.cacheKey;

        if (cacheScope && cacheKey) {
            const cachedData = this.cache.get(cacheScope, cacheKey);
            if (cachedData && Array.isArray(cachedData)) {
                this.populateSelect(selectEl, cachedData, previousValue, preserveValue);
                this.applySelect2(key);
                return;
            }
        }

        this.toggleLoader(key, true);
        selectEl.disabled = true;

        try {
            const response = await fetch(url, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
                credentials: "same-origin",
            });

            if (!response.ok) {
                throw new Error(`Error ${response.status}`);
            }

            const data = (await response.json()) || [];
            if (cacheScope && cacheKey && Array.isArray(data)) {
                this.cache.set(cacheScope, cacheKey, data);
            }
            this.populateSelect(selectEl, data, previousValue, preserveValue);
        } catch (error) {
            console.error(`[UbicacionSelects] Error cargando ${key}:`, error);
            this.populateSelect(selectEl, [], "", false);
        } finally {
            selectEl.disabled = false;
            this.applySelect2(key);
            this.toggleLoader(key, false);
        }
    };

    UbicacionSelects.prototype.populateSelect = function (
        selectEl,
        data,
        previousValue,
        preserveValue
    ) {
        const fragment = document.createDocumentFragment();
        const sortedData = data.slice().sort(this.sorter);

        sortedData.forEach((item) => {
            const option = document.createElement("option");
            option.value = item.id;
            option.textContent = item.nombre || item.nombre_region || "";
            fragment.appendChild(option);
        });

        // Mantener la opción vacía al inicio
        const emptyOption = selectEl.querySelector('option[value=""]');
        selectEl.innerHTML = "";
        if (emptyOption) {
            selectEl.appendChild(emptyOption);
        } else {
            const baseOption = document.createElement("option");
            baseOption.value = "";
            baseOption.textContent = EMPTY_OPTION_LABEL;
            selectEl.appendChild(baseOption);
        }

        selectEl.appendChild(fragment);

        if (preserveValue && previousValue) {
            selectEl.value = previousValue;
        } else {
            selectEl.value = "";
        }

        if (this.$ && this.$.fn && this.$.fn.select2) {
            this.$(selectEl).val(selectEl.value).trigger("change.select2");
        }
    };

    UbicacionSelects.prototype.applySelect2 = function (key) {
        if (!this.$ || !this.$.fn || !this.$.fn.select2) {
            return;
        }

        const selectEl = this.selects[key];
        if (!selectEl) return;

        const $select = this.$(selectEl);
        const currentValue = $select.val();

        if ($select.data("select2")) {
            $select.off("select2:open");
            $select.select2("destroy");
        }

        const uiConfig = this.ui[key] || {};
        const placeholder =
            this.placeholders[key] || this.placeholders.default || DEFAULT_PLACEHOLDERS.default;

        const options = Object.assign(
            {
                placeholder,
                allowClear:
                    typeof this.config.allowClear[key] === "boolean"
                        ? this.config.allowClear[key]
                        : true,
                width: "100%",
                minimumResultsForSearch: 0,
                dropdownAutoWidth: false,
            },
            uiConfig.select2Options || {}
        );

        if (uiConfig.dropdownParent) {
            const $parent = this.$(uiConfig.dropdownParent);
            if ($parent.length) {
                options.dropdownParent = $parent;
            }
        }

        $select.select2(options);

        $select.on("select2:open", function () {
            // Pequeño delay para asegurar que el DOM esté completamente renderizado
            setTimeout(function() {
                // Obtener el dropdown específico de este select2
                const selectId = $select.attr('id');
                const $dropdown = $(`[aria-controls="${selectId}"]`).closest('.select2-container').next('.select2-dropdown');

                // Si no se encuentra por aria-controls, buscar el último dropdown abierto
                const $targetDropdown = $dropdown.length > 0 ? $dropdown : $('.select2-dropdown:last');
                $targetDropdown.removeClass("select2-dropdown--above").addClass("select2-dropdown--below");

                // Obtener el contenedor específico de este select2
                const $container = $select.data('select2').$container;
                if ($container) {
                    $container.removeClass("select2-container--above").addClass("select2-container--below");
                }
            }, 10);
        });

        if (currentValue) {
            $select.val(currentValue).trigger("change.select2");
        }
    };

    UbicacionSelects.prototype.toggleLoader = function (key, show) {
        const uiConfig = this.ui[key] || {};

        if (uiConfig.loader) {
            const loader = document.querySelector(uiConfig.loader);
            if (loader) {
                loader.classList.toggle("d-none", !show);
            }
        }

        if (uiConfig.wrapper) {
            const wrapper = document.querySelector(uiConfig.wrapper);
            if (wrapper) {
                wrapper.classList.toggle("d-none", show);
            }
        }
    };

    window.UbicacionSelects = UbicacionSelects;
    window.initUbicacionSelects = async function (config) {
        const instance = new UbicacionSelects(config);
        await instance.init();
        return instance;
    };

    async function setupUbicacionSelects(config = {}) {
        const baseConfig = Object.assign(
            {
                selectors: {
                    provincia: "#id_provincia",
                    municipio: "#id_municipio",
                    localidad: "#id_localidad",
                },
                ajaxMunicipiosUrl: null,
                ajaxLocalidadesUrl: null,
                placeholders: {},
                allowClear: {
                    provincia: true,
                    municipio: true,
                    localidad: true,
                },
                ui: {
                    provincia: {},
                    municipio: {},
                    localidad: {},
                },
                autoPrefetch: true,
                sorter: defaultSorter,
            },
            config || {}
        );

        baseConfig.placeholders = Object.assign(
            {},
            DEFAULT_PLACEHOLDERS,
            baseConfig.placeholders || {}
        );

        baseConfig.ui = Object.assign(
            { provincia: {}, municipio: {}, localidad: {} },
            baseConfig.ui || {}
        );

        baseConfig.allowClear = Object.assign(
            { provincia: true, municipio: true, localidad: true },
            baseConfig.allowClear || {}
        );

        const selects = {
            provincia: document.querySelector(baseConfig.selectors.provincia),
            municipio: document.querySelector(baseConfig.selectors.municipio),
            localidad: document.querySelector(baseConfig.selectors.localidad),
        };

        const uiElements = {
            provincia: {
                wrapper: document.querySelector(baseConfig.ui.provincia.wrapper),
                loader: document.querySelector(baseConfig.ui.provincia.loader),
            },
            municipio: {
                wrapper: document.querySelector(baseConfig.ui.municipio.wrapper),
                loader: document.querySelector(baseConfig.ui.municipio.loader),
            },
            localidad: {
                wrapper: document.querySelector(baseConfig.ui.localidad.wrapper),
                loader: document.querySelector(baseConfig.ui.localidad.loader),
            },
        };

        const resetSelect = (selectEl) => {
            if (!selectEl) return;
            selectEl.innerHTML = "";
            const empty = document.createElement("option");
            empty.value = "";
            empty.textContent = EMPTY_OPTION_LABEL;
            selectEl.appendChild(empty);
        };

        const toggleLoader = (key, show) => {
            const uiCfg = uiElements[key];
            if (!uiCfg) return;
            if (uiCfg.wrapper) uiCfg.wrapper.classList.toggle("d-none", show);
            if (uiCfg.loader) uiCfg.loader.classList.toggle("d-none", !show);
        };

        const applySelect2Fallback = (key) => {
            if (!$ || !$.fn || !$.fn.select2) return;
            const selectEl = selects[key];
            if (!selectEl) return;
            const $select = $(selectEl);
            const options = {
                placeholder: baseConfig.placeholders[key],
                allowClear:
                    typeof baseConfig.allowClear[key] === "boolean"
                        ? baseConfig.allowClear[key]
                        : true,
                width: "100%",
                minimumResultsForSearch: 0,
            };

            const dropdownParent = baseConfig.ui[key]?.dropdownParent;
            if (dropdownParent) {
                const $parent = $(dropdownParent);
                if ($parent.length) {
                    options.dropdownParent = $parent;
                }
            }

            $select.select2(options);
        };

        const requestControllers = {
            municipio: null,
            localidad: null,
        };

        const fetchOptionsFallback = async (url, key, preserveValue = false, cacheMeta = {}) => {
            const target = selects[key];
            if (!target || !url) return;

            const previousValue = preserveValue ? target.value : "";
            const cacheScope = cacheMeta.cacheScope;
            const cacheKey = cacheMeta.cacheKey;

            if (cacheScope && cacheKey) {
                const cached = ubicacionCache.get(cacheScope, cacheKey);
                if (cached && Array.isArray(cached)) {
                    resetSelect(target);
                    cached.forEach((item) => {
                        const option = document.createElement("option");
                        option.value = item.id;
                        option.textContent = item.nombre || item.nombre_region || "";
                        target.appendChild(option);
                    });
                    if (previousValue) {
                        target.value = previousValue;
                    }
                    if ($ && $.fn && $.fn.select2) {
                        $(target).trigger("change.select2");
                    }
                    return;
                }
            }

            toggleLoader(key, true);
            try {
                if (requestControllers[key]) {
                    requestControllers[key].abort();
                }

                const controller = new AbortController();
                requestControllers[key] = controller;

                const response = await fetch(url, {
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                    credentials: "same-origin",
                    signal: controller.signal,
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                const data = await response.json();
                resetSelect(target);
                data.forEach((item) => {
                    const option = document.createElement("option");
                    option.value = item.id;
                    option.textContent = item.nombre || item.nombre_region || "";
                    target.appendChild(option);
                });
                if (cacheScope && cacheKey && Array.isArray(data)) {
                    ubicacionCache.set(cacheScope, cacheKey, data);
                }
                if (previousValue) {
                    target.value = previousValue;
                }
                if ($ && $.fn && $.fn.select2) {
                    $(target).trigger("change.select2");
                }
            } catch (error) {
                console.error(`[UbicacionSelects] Error cargando ${key} (fallback):`, error);
            } finally {
                toggleLoader(key, false);
            }
        };

        const loadMunicipiosFallback = async (provinciaId, preserveValue = false) => {
            resetSelect(selects.municipio);
            resetSelect(selects.localidad);
            if (!provinciaId) return;
            const url = `${baseConfig.ajaxMunicipiosUrl}?provincia_id=${encodeURIComponent(
                provinciaId
            )}`;
            await fetchOptionsFallback(url, "municipio", preserveValue, {
                cacheScope: "municipios",
                cacheKey: String(provinciaId),
            });
        };

        const loadLocalidadesFallback = async (municipioId, preserveValue = false) => {
            resetSelect(selects.localidad);
            if (!municipioId) return;
            const url = `${baseConfig.ajaxLocalidadesUrl}?municipio_id=${encodeURIComponent(
                municipioId
            )}`;
            await fetchOptionsFallback(url, "localidad", preserveValue, {
                cacheScope: "localidades",
                cacheKey: String(municipioId),
            });
        };

        let helperRan = false;
        let needsFallback = true;
        let helperInstance = null;

        if (typeof window.initUbicacionSelects === "function") {
            try {
                helperInstance = await window.initUbicacionSelects({
                    ...baseConfig,
                    autoPrefetch: baseConfig.autoPrefetch,
                });
                helperRan = true;
                const missingMunicipios =
                    selects.provincia &&
                    selects.provincia.value &&
                    selects.municipio &&
                    selects.municipio.options.length <= 1;
                const missingLocalidades =
                    selects.municipio &&
                    selects.municipio.value &&
                    selects.localidad &&
                    selects.localidad.options.length <= 1;
                needsFallback = missingMunicipios || missingLocalidades;
                if (!needsFallback) {
                    return { mode: "helper", instance: helperInstance };
                }
            } catch (error) {
                console.error("[UbicacionSelects] initUbicacionSelects falló, usando fallback:", error);
            }
        }

        if (!selects.provincia || !selects.municipio || !selects.localidad) {
            console.warn("[UbicacionSelects] Selects requeridos no encontrados para fallback");
            return { mode: helperRan ? "helper" : "none" };
        }

        const attachFallbackEvents = !helperRan || needsFallback;

        if (attachFallbackEvents) {
            if (selects.provincia) {
                selects.provincia.addEventListener("change", (event) => {
                    loadMunicipiosFallback(event.target.value);
                });
            }
            if (selects.municipio) {
                selects.municipio.addEventListener("change", (event) => {
                    loadLocalidadesFallback(event.target.value);
                });
            }
        }

        if (needsFallback) {
            if (
                selects.provincia &&
                selects.provincia.value &&
                selects.municipio &&
                selects.municipio.options.length <= 1
            ) {
                await loadMunicipiosFallback(selects.provincia.value, true);
            }
            if (
                selects.municipio &&
                selects.municipio.value &&
                selects.localidad &&
                selects.localidad.options.length <= 1
            ) {
                await loadLocalidadesFallback(selects.municipio.value, true);
            }
        }

        if (!helperRan) {
            applySelect2Fallback("provincia");
            applySelect2Fallback("municipio");
            applySelect2Fallback("localidad");
        }

        return {
            mode: helperRan ? "helper+fallback" : "fallback",
            instance: helperInstance,
        };
    }

    window.setupUbicacionSelects = setupUbicacionSelects;
})(window, document, window.jQuery);
