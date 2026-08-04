/**
 * Filtros avanzados de los listados.
 *
 * Modelo (definicion UX/UI del prototipo Figma): cada filtro es una barra
 * completa "campo + valor + lupa". "+ Filtro" agrega una fila, "- Filtro" la
 * quita y aparece recien desde la segunda.
 *
 * El selector de "tipo de coincidencia" se elimino por definicion: el operador
 * se deduce del tipo de campo (texto -> contiene, numero/fecha/choice -> igual).
 * Eso implica que ya no se puede buscar por campo vacio ni por rango; queda
 * asentado en docs/registro/cambios/2026-07-31-buscador-transversal-lupa-y-cta.md
 */
(function () {
    const form = document.getElementById('filters-form');
    if (!form) {
        return;
    }

    const configId = form.dataset.configId;
    if (!configId) {
        console.warn('AdvancedFilters: falta data-config-id en el formulario.');
        return;
    }

    const configScript = document.getElementById(configId);
    if (!configScript) {
        console.warn('AdvancedFilters: no se encontró el script con la configuración.');
        return;
    }

    let config;
    try {
        config = JSON.parse(configScript.textContent);
    } catch (error) {
        console.error('AdvancedFilters: configuración inválida.', error);
        return;
    }

    const rowsContainer = document.getElementById('poncho-filters-rows');
    const rowTemplate = document.getElementById('poncho-filter-row-template');
    const hiddenInput = document.getElementById('filters-input');

    if (!rowsContainer || !rowTemplate || !hiddenInput) {
        console.warn('AdvancedFilters: faltan elementos requeridos en el DOM.');
        return;
    }

    // AND/OR se retiro de la UI por definicion de UX/UI: los filtros se
    // combinan siempre con AND. El backend sigue aceptando el campo `logic`.
    const LOGICA_FIJA = 'AND';

    const defaultOpByType = Object.assign(
        {
            text: 'contains',
            number: 'eq',
            date: 'eq',
            boolean: 'eq',
            choice: 'eq',
        },
        config.defaultOperators || {}
    );

    const booleanOptions = config.booleanOptions || [
        { value: 'true', label: 'Sí' },
        { value: 'false', label: 'No' },
    ];

    const fields = Array.isArray(config.fields) ? config.fields : [];
    if (!fields.length) {
        console.warn('AdvancedFilters: no hay campos configurados.');
        return;
    }

    const fieldsByName = fields.reduce((acc, field) => {
        if (field && field.name) {
            acc[field.name] = field;
        }
        return acc;
    }, {});

    const fieldOptions = fields
        .filter(field => field && field.name && field.label)
        .map(field => ({ value: field.name, label: field.label }));

    if (!fieldOptions.length) {
        console.warn('AdvancedFilters: no hay campos válidos para mostrar.');
        return;
    }

    function createOption(value, label) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = label;
        return option;
    }

    function populateOptions(select, options) {
        select.innerHTML = '';
        options.forEach(opt => {
            select.appendChild(createOption(opt.value, opt.label));
        });
    }

    function setVisible(el, visible) {
        el.hidden = !visible;
        el.style.display = visible ? '' : 'none';
    }

    function getFieldDefinition(name) {
        return fieldsByName[name];
    }

    /** El operador ya no lo elige el usuario: sale del tipo de campo. */
    function operadorPara(fieldDef) {
        return defaultOpByType[fieldDef ? fieldDef.type : 'text'] || 'contains';
    }

    function getChoiceOptions(fieldDef) {
        if (Array.isArray(fieldDef.options) && fieldDef.options.length) {
            return fieldDef.options;
        }
        if (fieldDef.type === 'boolean') {
            return booleanOptions;
        }
        return Array.isArray(fieldDef.choices) ? fieldDef.choices : [];
    }

    function applyInputAttributes(input, fieldDef) {
        input.removeAttribute('step');
        input.removeAttribute('min');
        input.removeAttribute('max');

        const attrs = fieldDef.input || {};
        if (fieldDef.type === 'number') {
            input.type = 'number';
            input.step = attrs.step || '1';
        } else if (fieldDef.type === 'date') {
            input.type = 'date';
        } else {
            input.type = 'text';
        }
        if (attrs.min !== undefined) {
            input.min = attrs.min;
        }
        if (attrs.max !== undefined) {
            input.max = attrs.max;
        }
    }

    /** Renumera los placeholders: "Buscar por filtro 1", "... 2", ... */
    function renumerarFilas() {
        const filas = Array.from(rowsContainer.children);
        filas.forEach((fila, indice) => {
            const refs = fila._filtroRefs;
            if (!refs) {
                return;
            }
            refs.valueInput.placeholder = `Buscar por filtro ${indice + 1}`;
            // "- Filtro" no va en la primera fila
            setVisible(refs.quitarBtn, indice > 0);
        });
    }

    function crearFila(prefill) {
        const fragmento = rowTemplate.content.cloneNode(true);
        const fila = fragmento.querySelector('.poncho-search--row');

        const refs = {
            fieldSel: fila.querySelector('[data-rol="campo"]'),
            valueInput: fila.querySelector('[data-rol="valor"]'),
            selectValue: fila.querySelector('[data-rol="valor-select"]'),
            agregarBtn: fila.querySelector('[data-rol="agregar"]'),
            quitarBtn: fila.querySelector('[data-rol="quitar"]'),
        };

        populateOptions(
            refs.fieldSel,
            [{ value: '', label: 'Buscar por' }].concat(fieldOptions)
        );

        function campoActual() {
            return getFieldDefinition(refs.fieldSel.value) || fields[0];
        }

        function ajustarValor(prefillValue) {
            const fieldDef = campoActual();

            if (fieldDef.type === 'choice' || fieldDef.type === 'boolean') {
                const opciones = getChoiceOptions(fieldDef);
                populateOptions(refs.selectValue, opciones);
                if (prefillValue !== undefined) {
                    refs.selectValue.value = prefillValue;
                    if (refs.selectValue.value !== prefillValue) {
                        refs.selectValue.appendChild(
                            createOption(prefillValue, prefillValue)
                        );
                        refs.selectValue.value = prefillValue;
                    }
                }
                setVisible(refs.selectValue, true);
                setVisible(refs.valueInput, false);
                return;
            }

            setVisible(refs.selectValue, false);
            setVisible(refs.valueInput, true);
            applyInputAttributes(refs.valueInput, fieldDef);
            if (prefillValue !== undefined) {
                refs.valueInput.value = prefillValue;
            }
        }

        function alCambiarCampo() {
            refs.valueInput.value = '';
            ajustarValor();
        }

        refs.fieldSel.addEventListener('change', alCambiarCampo);

        refs.agregarBtn.addEventListener('click', () => crearFila());
        refs.quitarBtn.addEventListener('click', () => {
            fila.remove();
            renumerarFilas();
        });

        fila._filtroRefs = refs;
        rowsContainer.appendChild(fila);

        if (prefill && prefill.field && fieldsByName[prefill.field]) {
            refs.fieldSel.value = prefill.field;
            ajustarValor(prefill.value);
        } else {
            ajustarValor();
        }

        renumerarFilas();
        return refs;
    }

    function readRow(refs) {
        // '' es el placeholder "Buscar por": se busca por el primer campo.
        const field = refs.fieldSel.value || fieldOptions[0].value;
        const fieldDef = getFieldDefinition(field);
        if (!fieldDef) {
            return null;
        }

        const op = operadorPara(fieldDef);

        if (fieldDef.type === 'choice' || fieldDef.type === 'boolean') {
            const seleccionado = refs.selectValue.value;
            return seleccionado !== '' ? { field, op, value: seleccionado } : null;
        }

        const valor = refs.valueInput.value.trim();
        return valor !== '' ? { field, op, value: valor } : null;
    }

    function collectItems() {
        const items = [];
        Array.from(rowsContainer.children).forEach(fila => {
            const refs = fila._filtroRefs;
            if (!refs) {
                return;
            }
            const item = readRow(refs);
            if (item) {
                items.push(item);
            }
        });
        return items;
    }

    function collectPayload() {
        return {
            logic: LOGICA_FIJA,
            items: collectItems(),
        };
    }

    // Lo consume favorite_filters.js para no duplicar la serializacion.
    window.AdvancedFilters = { collectPayload };

    form.addEventListener('submit', () => {
        hiddenInput.value = JSON.stringify(collectPayload());
    });

    function loadFromQuerystring() {
        try {
            const params = new URLSearchParams(window.location.search);
            const raw = params.get('filters');
            if (!raw) {
                return false;
            }
            const parsed = JSON.parse(raw);
            if (!parsed || !Array.isArray(parsed.items) || !parsed.items.length) {
                return false;
            }

            parsed.items.forEach(item => crearFila(item));
            return true;
        } catch (error) {
            console.warn('AdvancedFilters: no se pudo reconstruir filtros desde la URL.', error);
            return false;
        }
    }

    if (!loadFromQuerystring()) {
        crearFila();
    }
})();
