(function () {
    /**
     * Centros Search Bar (filtros combinables)
     */
    const TEXT_FIELDS = [
        { value: 'nombre', label: 'Nombre' },
        { value: 'tipo', label: 'Tipo' },
        { value: 'faro_asociado', label: 'Faro asociado' },
        { value: 'codigo', label: 'Codigo' },
        { value: 'organizacion_asociada', label: 'Organizacion asociada' },
        { value: 'provincia', label: 'Provincia' },
        { value: 'municipio', label: 'Municipio' },
        { value: 'localidad', label: 'Localidad' },
        { value: 'calle', label: 'Calle' },
        { value: 'domicilio_actividad', label: 'Domicilio de actividades' },
        { value: 'telefono', label: 'Telefono' },
        { value: 'celular', label: 'Celular' },
        { value: 'correo', label: 'Correo' },
        { value: 'sitio_web', label: 'Sitio Web' },
        { value: 'link_redes', label: 'Link redes' },
        { value: 'nombre_referente', label: 'Nombre del referente' },
        { value: 'apellido_referente', label: 'Apellido del referente' },
        { value: 'telefono_referente', label: 'Telefono del referente' },
        { value: 'correo_referente', label: 'Correo del referente' },
    ];

    const NUMBER_FIELDS = [
        { value: 'numero', label: 'Numero' },
    ];

    const BOOL_FIELDS = [
        { value: 'activo', label: 'Activo' },
    ];

    const TEXT_OPS = [
        { value: 'contains', label: 'Contiene' },
        { value: 'ncontains', label: 'No contiene' },
        { value: 'eq', label: 'Igual a' },
        { value: 'ne', label: 'Distinto de' },
        { value: 'empty', label: 'Vacio' },
    ];

    const NUM_OPS = [
        { value: 'eq', label: 'Igual a' },
        { value: 'ne', label: 'Distinto de' },
        { value: 'gt', label: 'Mayor a' },
        { value: 'lt', label: 'Menor a' },
        { value: 'empty', label: 'Vacio' },
    ];

    const BOOL_OPS = [
        { value: 'eq', label: 'Igual a' },
        { value: 'ne', label: 'Distinto de' },
        { value: 'empty', label: 'Vacio' },
    ];

    const rowsContainer = document.getElementById('filters-rows');
    const addBtn = document.getElementById('add-filter');
    const form = document.getElementById('filters-form');
    const logicSelect = document.getElementById('filters-logic');
    const hiddenInput = document.getElementById('filters-input');

    function createSelect(options, className) {
        const sel = document.createElement('select');
        sel.className = className;
        options.forEach(opt => {
            const o = document.createElement('option');
            o.value = opt.value;
            o.textContent = opt.label;
            sel.appendChild(o);
        });
        return sel;
    }

    function fieldOptions() {
        return [...TEXT_FIELDS, ...NUMBER_FIELDS, ...BOOL_FIELDS];
    }

    function isNumberField(field) {
        return NUMBER_FIELDS.some(item => item.value === field);
    }

    function isBooleanField(field) {
        return BOOL_FIELDS.some(item => item.value === field);
    }

    function normalizeBooleanValue(value) {
        if (typeof value === 'boolean') {
            return value ? 'true' : 'false';
        }
        return String(value).trim().toLowerCase();
    }

    function addRow(prefill) {
        const row = document.createElement('div');
        row.className = 'filters-row';

        const fieldSel = createSelect(fieldOptions(), 'form-select');
        const opSel = createSelect(TEXT_OPS, 'form-select');
        const valueInput = document.createElement('input');
        valueInput.type = 'text';
        valueInput.className = 'form-control form-control-sm';
        valueInput.placeholder = 'Valor';

        const boolValueSel = createSelect(
            [
                { value: 'true', label: 'Si' },
                { value: 'false', label: 'No' },
            ],
            'form-select form-select-sm'
        );
        boolValueSel.style.display = 'none';

        const emptyModeSel = createSelect([
            { value: 'both', label: 'Nulos o vacios' },
            { value: 'null', label: 'Solo nulos' },
            { value: 'blank', label: 'Solo vacios' },
        ], 'form-select');
        emptyModeSel.style.display = 'none';

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-sm btn-outline-danger';
        removeBtn.textContent = '-';

        function refreshOps() {
            const field = fieldSel.value;
            const ops = isNumberField(field)
                ? NUM_OPS
                : isBooleanField(field)
                    ? BOOL_OPS
                    : TEXT_OPS;

            opSel.innerHTML = '';
            ops.forEach(opt => {
                const o = document.createElement('option');
                o.value = opt.value;
                o.textContent = opt.label;
                opSel.appendChild(o);
            });

            if (isNumberField(field)) {
                opSel.value = 'eq';
            } else if (isBooleanField(field)) {
                opSel.value = 'eq';
            } else {
                opSel.value = 'contains';
            }

            adjustValueVisibility();
        }

        function adjustValueVisibility() {
            const op = opSel.value;
            const field = fieldSel.value;
            const numeric = isNumberField(field);
            const booleanField = isBooleanField(field);

            if (booleanField) {
                valueInput.style.display = 'none';
                boolValueSel.style.display = op === 'empty' ? 'none' : 'inline-block';
            } else {
                boolValueSel.style.display = 'none';
            }

            if (op === 'empty') {
                valueInput.style.display = 'none';
                emptyModeSel.style.display = 'inline-block';
                if (numeric || booleanField) {
                    [...emptyModeSel.options].forEach(opt => {
                        opt.disabled = opt.value === 'blank';
                    });
                    emptyModeSel.value = 'both';
                } else {
                    [...emptyModeSel.options].forEach(opt => {
                        opt.disabled = false;
                    });
                    if (!['both', 'null', 'blank'].includes(emptyModeSel.value)) {
                        emptyModeSel.value = 'both';
                    }
                }
            } else {
                emptyModeSel.style.display = 'none';
                if (numeric) {
                    valueInput.style.display = 'inline-block';
                    valueInput.type = 'number';
                    valueInput.step = '1';
                } else if (!booleanField) {
                    valueInput.style.display = 'inline-block';
                    valueInput.type = 'text';
                    valueInput.removeAttribute('step');
                }
            }
        }

        fieldSel.addEventListener('change', refreshOps);
        opSel.addEventListener('change', adjustValueVisibility);
        removeBtn.addEventListener('click', () => row.remove());

        row.appendChild(fieldSel);
        row.appendChild(opSel);
        row.appendChild(valueInput);
        row.appendChild(boolValueSel);
        row.appendChild(emptyModeSel);
        row.appendChild(removeBtn);
        rowsContainer.appendChild(row);

        if (prefill) {
            if (prefill.field) {
                fieldSel.value = prefill.field;
            }
            refreshOps();

            if (prefill.op) {
                opSel.value = prefill.op;
            }
            adjustValueVisibility();

            if (prefill.op === 'empty') {
                emptyModeSel.value = prefill.empty_mode || 'both';
            } else if (typeof prefill.value !== 'undefined') {
                if (isBooleanField(fieldSel.value)) {
                    boolValueSel.value = normalizeBooleanValue(prefill.value);
                } else {
                    valueInput.value = prefill.value;
                }
            }
        } else {
            fieldSel.value = 'nombre';
            refreshOps();
            opSel.value = 'contains';
            adjustValueVisibility();
        }
    }

    addBtn.addEventListener('click', () => addRow());

    form.addEventListener('submit', () => {
        const items = [];
        const rows = rowsContainer.children;

        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            const elements = row.querySelectorAll('select, input');
            const fieldSel = elements[0];
            const opSel = elements[1];
            const valueInput = elements[2];
            const boolValueSel = elements[3];
            const emptyModeSel = elements[4];

            const field = fieldSel.value;
            const op = opSel.value;

            if (op === 'empty') {
                items.push({ field, op, empty_mode: emptyModeSel.value });
            } else if (isBooleanField(field)) {
                const boolValue = boolValueSel.value;
                if (boolValue) {
                    items.push({ field, op, value: boolValue });
                }
            } else {
                const rawValue = valueInput.value.trim();
                if (rawValue !== '') {
                    items.push({ field, op, value: rawValue });
                }
            }
        }

        const logic = logicSelect.value || 'AND';
        hiddenInput.value = JSON.stringify({ logic, items });
    });

    try {
        const params = new URLSearchParams(window.location.search);
        const raw = params.get('filters');
        if (raw) {
            const parsed = JSON.parse(raw);
            if (parsed && Array.isArray(parsed.items) && parsed.items.length) {
                logicSelect.value = parsed.logic === 'OR' ? 'OR' : 'AND';
                parsed.items.forEach(item => addRow(item));
                return;
            }
        }
    } catch (err) {
        // fallback to default row
    }

    addRow();
})();
