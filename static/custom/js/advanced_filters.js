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

    const rowsContainer = document.getElementById('filters-rows');
    const addBtn = document.getElementById('add-filter');
    const logicSelect = document.getElementById('filters-logic');
    const hiddenInput = document.getElementById('filters-input');

    if (!rowsContainer || !addBtn || !logicSelect || !hiddenInput) {
        console.warn('AdvancedFilters: faltan elementos requeridos en el DOM.');
        return;
    }

    // La primera fila de filtro vive dentro de la barra de búsqueda (lupa incluida),
    // segun el prototipo. "+ Filtro" agrega las filas siguientes en #filters-rows.
    const primaryRefs = {
        fieldSel: document.getElementById('filters-primary-field'),
        opSel: document.getElementById('filters-primary-op'),
        valueInput: document.getElementById('filters-primary-value'),
        selectValue: document.getElementById('filters-primary-select'),
        emptyModeSel: document.getElementById('filters-primary-empty'),
    };

    const hasPrimary = Object.keys(primaryRefs).every(key => primaryRefs[key]);
    if (!hasPrimary) {
        console.warn('AdvancedFilters: falta la fila primaria en la barra de búsqueda.');
        return;
    }

    const operatorLabels = Object.assign(
        {
            contains: 'Contiene',
            ncontains: 'No contiene',
            eq: 'Igual a',
            ne: 'Distinto de',
            gt: 'Mayor a',
            lt: 'Menor a',
            empty: 'Vacío',
        },
        config.operatorLabels || {}
    );

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

    const emptyModeOptions = [
        { value: 'both', label: 'Nulos o vacíos' },
        { value: 'null', label: 'Solo nulos' },
        { value: 'blank', label: 'Solo vacíos' },
    ];

    const fields = Array.isArray(config.fields) ? config.fields : [];
    if (!fields.length) {
        console.warn('AdvancedFilters: no hay campos configurados.');
        return;
    }

    const operatorsByType = Object.assign(
        {
            text: ['contains', 'ncontains', 'eq', 'ne', 'empty'],
            number: ['eq', 'ne', 'gt', 'lt', 'empty'],
            date: ['eq', 'ne', 'gt', 'lt', 'empty'],
            boolean: ['eq', 'ne'],
            choice: ['eq', 'ne'],
        },
        config.operators || {}
    );

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

    function createSelect(className, options) {
        const select = document.createElement('select');
        select.className = className;
        if (Array.isArray(options)) {
            populateOptions(select, options);
        }
        return select;
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

    // Unifica el ocultado: las filas dinámicas usan style.display y la fila
    // primaria el atributo hidden (es hija flex de la barra de búsqueda).
    function setVisible(el, visible) {
        el.hidden = !visible;
        el.style.display = visible ? '' : 'none';
    }

    function tryInitSelect2(el, opts) {
        if (window.jQuery && window.jQuery.fn && window.jQuery.fn.select2) {
            const $el = window.jQuery(el);
            if (!$el.data('select2')) {
                $el.select2(Object.assign({ width: '100%' }, opts || {}));
            }
        }
    }

    function tryDestroySelect2(el) {
        if (window.jQuery && window.jQuery.fn && window.jQuery.fn.select2) {
            const $el = window.jQuery(el);
            if ($el.data('select2')) {
                $el.select2('destroy');
            }
        }
    }

    function bindSelect2FieldEvents(el, handler) {
        if (window.jQuery && window.jQuery.fn && window.jQuery.fn.select2) {
            window.jQuery(el)
                .off('select2:select.advancedFilters select2:clear.advancedFilters')
                .on(
                    'select2:select.advancedFilters select2:clear.advancedFilters',
                    handler
                );
        }
    }

    function getFieldDefinition(name) {
        return fieldsByName[name];
    }

    function getOperatorsFor(fieldType) {
        const ops = operatorsByType[fieldType];
        if (!Array.isArray(ops) || !ops.length) {
            return operatorsByType.text;
        }
        return ops;
    }

    function getOperatorOptions(fieldType) {
        return getOperatorsFor(fieldType).map(op => ({
            value: op,
            label: operatorLabels[op] || op,
        }));
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
        input.removeAttribute('pattern');

        if (fieldDef.type === 'number') {
            input.type = 'number';
            const attrs = fieldDef.input || {};
            input.step = attrs.step || '1';
            if (attrs.min !== undefined) {
                input.min = attrs.min;
            }
            if (attrs.max !== undefined) {
                input.max = attrs.max;
            }
        } else if (fieldDef.type === 'date') {
            input.type = 'date';
            const attrs = fieldDef.input || {};
            if (attrs.min !== undefined) {
                input.min = attrs.min;
            }
            if (attrs.max !== undefined) {
                input.max = attrs.max;
            }
        } else {
            input.type = 'text';
        }
    }

    function disableBlankOption(emptyModeSel, disabled) {
        Array.from(emptyModeSel.options).forEach(opt => {
            if (opt.value === 'blank') {
                opt.disabled = disabled;
            }
        });
        if (disabled && emptyModeSel.value === 'blank') {
            emptyModeSel.value = 'both';
        }
    }

    /**
     * Conecta la lógica de un filtro (campo -> operadores -> valor) sobre un
     * conjunto de elementos ya existentes. Lo usan tanto la fila primaria de la
     * barra como las filas que agrega "+ Filtro".
     *
     * @param {Object} refs elementos del filtro
     * @param {Object} options useSelect2: la barra usa selects nativos estilados
     */
    function wireRow(refs, options) {
        const useSelect2 = !options || options.useSelect2 !== false;
        const { fieldSel, opSel, valueInput, selectValue, emptyModeSel } = refs;

        function currentFieldDef() {
            return getFieldDefinition(fieldSel.value) || fields[0];
        }

        function refreshOperators(preserveCurrent) {
            const fieldDef = currentFieldDef();
            const options = getOperatorOptions(fieldDef.type);
            const previous = preserveCurrent ? opSel.value : null;
            populateOptions(opSel, options);

            const defaultOp = defaultOpByType[fieldDef.type] || options[0]?.value;
            opSel.value = options.some(opt => opt.value === previous)
                ? previous
                : defaultOp;
        }

        function refreshSelectOptions(fieldDef, prefillValue) {
            const options = getChoiceOptions(fieldDef);
            if (!options.length) {
                selectValue.innerHTML = '';
                return;
            }

            populateOptions(selectValue, options);
            if (prefillValue !== undefined) {
                selectValue.value = prefillValue;
                if (selectValue.value !== prefillValue) {
                    // si el valor no existe, agregarlo temporalmente
                    selectValue.appendChild(createOption(prefillValue, prefillValue));
                    selectValue.value = prefillValue;
                }
            }
        }

        function adjustVisibility(prefillValue) {
            const fieldDef = currentFieldDef();
            const operator = opSel.value;
            const type = fieldDef.type;

            if (operator === 'empty') {
                setVisible(valueInput, false);
                if (useSelect2) {
                    tryDestroySelect2(selectValue);
                }
                setVisible(selectValue, false);
                setVisible(emptyModeSel, true);
                disableBlankOption(
                    emptyModeSel,
                    type === 'number' || type === 'boolean' || type === 'date'
                );
                return;
            }

            setVisible(emptyModeSel, false);

            if (type === 'choice' || type === 'boolean') {
                if (useSelect2) {
                    tryDestroySelect2(selectValue);
                }
                refreshSelectOptions(fieldDef, prefillValue);
                setVisible(selectValue, true);
                if (useSelect2) {
                    tryInitSelect2(selectValue, { width: '100%' });
                }
                setVisible(valueInput, false);
                return;
            }

            if (useSelect2) {
                tryDestroySelect2(selectValue);
            }
            setVisible(selectValue, false);
            setVisible(valueInput, true);
            applyInputAttributes(valueInput, fieldDef);

            if (prefillValue !== undefined) {
                valueInput.value = prefillValue;
            }
        }

        function handleFieldChange() {
            const fieldDef = currentFieldDef();
            refreshOperators(false);
            adjustVisibility();
            if (fieldDef.type !== 'choice' && fieldDef.type !== 'boolean') {
                valueInput.value = '';
            } else {
                selectValue.value = getChoiceOptions(fieldDef)[0]?.value || '';
            }
        }

        function applyPrefill(prefill) {
            if (prefill) {
                if (prefill.field && fieldsByName[prefill.field]) {
                    fieldSel.value = prefill.field;
                }
                refreshOperators(true);
                if (prefill.op) {
                    opSel.value = prefill.op;
                }
                adjustVisibility(prefill.op === 'empty' ? undefined : prefill.value);

                if (opSel.value === 'empty' && prefill.empty_mode) {
                    emptyModeSel.value = prefill.empty_mode;
                } else if (prefill.value !== undefined) {
                    const fieldDef = currentFieldDef();
                    if (fieldDef.type === 'choice' || fieldDef.type === 'boolean') {
                        refreshSelectOptions(fieldDef, prefill.value);
                    } else {
                        valueInput.value = String(prefill.value);
                    }
                }
                return;
            }

            fieldSel.value = fieldOptions[0].value;
            refreshOperators(false);
            adjustVisibility();
        }

        refs.handleFieldChange = handleFieldChange;
        refs.applyPrefill = applyPrefill;

        fieldSel.addEventListener('change', handleFieldChange);
        opSel.addEventListener('change', () => adjustVisibility());

        return refs;
    }

    function initPrimaryRow(prefill) {
        // El prototipo muestra "Buscar por" como estado en reposo, no el nombre
        // del primer campo. Se agrega como opcion placeholder; si el usuario
        // busca sin elegir, readRow() cae al primer campo configurado.
        populateOptions(primaryRefs.fieldSel, [
            { value: '', label: 'Buscar por' },
        ].concat(fieldOptions));
        populateOptions(primaryRefs.emptyModeSel, emptyModeOptions);
        // Selects nativos: el estilo de la barra los dibuja, select2 lo rompería.
        wireRow(primaryRefs, { useSelect2: false });
        primaryRefs.applyPrefill(prefill);
        if (!prefill) {
            // applyPrefill deja seleccionado el primer campo; volvemos al
            // placeholder para que en reposo se lea "Buscar por".
            primaryRefs.fieldSel.value = '';
        }
    }

    function addRow(prefill) {
        const refs = {
            fieldSel: createSelect('form-select', fieldOptions),
            opSel: createSelect('form-select'),
            valueInput: document.createElement('input'),
            selectValue: createSelect('form-select form-select-sm'),
            emptyModeSel: createSelect('form-select form-select-sm', emptyModeOptions),
        };

        refs.valueInput.type = 'text';
        refs.valueInput.className = 'form-control form-control-sm';
        refs.valueInput.placeholder = 'Valor';
        setVisible(refs.selectValue, false);
        setVisible(refs.emptyModeSel, false);

        const row = document.createElement('div');
        row.className = 'filters-row';

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-sm btn-outline-danger';
        removeBtn.textContent = '-';
        removeBtn.addEventListener('click', () => {
            tryDestroySelect2(refs.fieldSel);
            tryDestroySelect2(refs.selectValue);
            row.remove();
        });

        wireRow(refs);

        row.appendChild(refs.fieldSel);
        row.appendChild(refs.opSel);
        row.appendChild(refs.valueInput);
        row.appendChild(refs.selectValue);
        row.appendChild(refs.emptyModeSel);
        row.appendChild(removeBtn);
        rowsContainer.appendChild(row);

        refs.applyPrefill(prefill);

        row._advancedFilterRefs = refs;

        tryInitSelect2(refs.fieldSel, { width: '100%' });
        bindSelect2FieldEvents(refs.fieldSel, refs.handleFieldChange);
    }

    function readRow(refs) {
        // '' es el placeholder "Buscar por": se busca por el primer campo.
        const field = refs.fieldSel.value || fieldOptions[0].value;
        const op = refs.opSel.value;
        const fieldDef = getFieldDefinition(field);
        if (!fieldDef || !field || !op) {
            return null;
        }

        if (op === 'empty') {
            return { field, op, empty_mode: refs.emptyModeSel.value || 'both' };
        }

        if (fieldDef.type === 'choice' || fieldDef.type === 'boolean') {
            const selected = refs.selectValue.value;
            return selected !== '' ? { field, op, value: selected } : null;
        }

        const rawValue = refs.valueInput.value.trim();
        return rawValue !== '' ? { field, op, value: rawValue } : null;
    }

    function collectItems() {
        const items = [];
        const primary = readRow(primaryRefs);
        if (primary) {
            items.push(primary);
        }

        Array.from(rowsContainer.children).forEach(row => {
            const refs = row._advancedFilterRefs;
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
            logic: logicSelect.value || 'AND',
            items: collectItems(),
        };
    }

    // Expuesto para favorite_filters.js: la fila primaria ya no vive en
    // #filters-rows, asi que recorrer ese contenedor la dejaria afuera.
    window.AdvancedFilters = { collectPayload };

    // Panel avanzado: en reposo la barra debe verse igual al prototipo, asi que
    // operador, AND/OR y Favoritos viven plegados hasta que el usuario los pide.
    const advancedPanel = document.getElementById('filters-advanced');

    function openAdvanced() {
        if (!advancedPanel || !advancedPanel.hidden) {
            return;
        }
        advancedPanel.hidden = false;
        addBtn.setAttribute('aria-expanded', 'true');
    }

    addBtn.addEventListener('click', () => {
        openAdvanced();
        addRow();
    });

    // Si el estado que llega por URL no es representable en la barra sola
    // (mas de un filtro, u operador distinto del default del campo), el panel
    // arranca abierto: si no, el usuario no veria por que filtra asi.
    function necesitaPanelAbierto(items) {
        if (items.length > 1) {
            return true;
        }
        const primero = items[0];
        if (!primero) {
            return false;
        }
        const fieldDef = getFieldDefinition(primero.field);
        if (!fieldDef) {
            return false;
        }
        return primero.op !== (defaultOpByType[fieldDef.type] || 'contains');
    }

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

            logicSelect.value = parsed.logic === 'OR' ? 'OR' : 'AND';
            initPrimaryRow(parsed.items[0]);
            parsed.items.slice(1).forEach(item => addRow(item));
            if (necesitaPanelAbierto(parsed.items)) {
                openAdvanced();
            }
            return true;
        } catch (error) {
            console.warn('AdvancedFilters: no se pudo reconstruir filtros desde la URL.', error);
            return false;
        }
    }

    if (!loadFromQuerystring()) {
        initPrimaryRow();
    }

    // Inicializar Select2 en filas ya existentes una vez que jQuery y Select2 estén
    // disponibles. La fila primaria queda fuera a propósito: usa selects nativos.
    window.addEventListener('load', function () {
        rowsContainer.querySelectorAll('.filters-row').forEach(function (row) {
            var refs = row._advancedFilterRefs;
            if (!refs) { return; }
            tryInitSelect2(refs.fieldSel, { width: '100%' });
            bindSelect2FieldEvents(refs.fieldSel, refs.handleFieldChange);
            if (!refs.selectValue.hidden) {
                tryInitSelect2(refs.selectValue, { width: '100%' });
            }
        });
    });
})();
