(function () {
    /**
     * Beneficiarios Search Bar (filtros combinables)
     * Replica la logica de comedores pero con campos y etiquetas propias.
     */
    const TEXT_FIELDS = [
        { value: 'first_name', label: 'Apellido' },
        { value: 'last_name', label: 'Nombre' },
        { value: 'username', label: 'Usuario' },
        { value: 'email', label: 'Email' },
        { value: 'rol', label: 'Rol' },
    ];
    const NUMBER_FIELDS = [
    ];

    const TEXT_OPS = [
        { value: 'contains', label: 'Contiene' },
        { value: 'ncontains', label: 'No contiene' },
        { value: 'eq', label: 'Igual a' },
        { value: 'ne', label: 'Distinto de' },
        { value: 'empty', label: 'Vacio' }
    ];
    const NUM_OPS = [
        { value: 'eq', label: 'Igual a' },
        { value: 'ne', label: 'Distinto de' },
        { value: 'gt', label: 'Mayor a' },
        { value: 'lt', label: 'Menor a' },
        { value: 'empty', label: 'Vacio' }
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
        return [
            ...TEXT_FIELDS,
            ...NUMBER_FIELDS
        ];
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

        const emptyModeSel = createSelect([
            { value: 'both', label: 'Nulos o vacios' },
            { value: 'null', label: 'Solo nulos' },
            { value: 'blank', label: 'Solo vacios' }
        ], 'form-select');
        emptyModeSel.style.display = 'none';

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-sm btn-outline-danger';
        removeBtn.textContent = '-';

        function isNumberField(f) {
            return NUMBER_FIELDS.some(n => n.value === f);
        }

        function refreshOps() {
            const field = fieldSel.value;
            const isNum = isNumberField(field);
            opSel.innerHTML = '';
            const ops = isNum ? NUM_OPS : TEXT_OPS;
            ops.forEach(opt => {
                const o = document.createElement('option');
                o.value = opt.value;
                o.textContent = opt.label;
                opSel.appendChild(o);
            });
            opSel.value = isNum ? 'eq' : 'contains';
            adjustValueVisibility();
        }

        function adjustValueVisibility() {
            const op = opSel.value;
            const field = fieldSel.value;
            const isNum = isNumberField(field);
            if (op === 'empty') {
                valueInput.style.display = 'none';
                emptyModeSel.style.display = 'inline-block';
                if (isNum) {
                    [...emptyModeSel.options].forEach(opt => {
                        if (opt.value === 'blank') opt.disabled = true;
                        if (opt.value !== 'null' && opt.value !== 'both') opt.disabled = true;
                    });
                    emptyModeSel.value = 'both';
                } else {
                    [...emptyModeSel.options].forEach(opt => { opt.disabled = false; });
                    if (!['both', 'null', 'blank'].includes(emptyModeSel.value)) {
                        emptyModeSel.value = 'both';
                    }
                }
            } else {
                valueInput.style.display = 'inline-block';
                emptyModeSel.style.display = 'none';
                if (isNum) {
                    valueInput.type = 'number';
                    valueInput.step = '1';
                } else {
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
        row.appendChild(emptyModeSel);
        row.appendChild(removeBtn);
        rowsContainer.appendChild(row);

        if (prefill) {
            if (prefill.field) fieldSel.value = prefill.field;
            refreshOps();
            if (prefill.op) opSel.value = prefill.op;
            adjustValueVisibility();
            if (prefill.op === 'empty') {
                emptyModeSel.value = (prefill.empty_mode || 'both');
            } else if (typeof prefill.value !== 'undefined') {
                valueInput.value = prefill.value;
            }
        } else {
            fieldSel.value = 'apellido';
            refreshOps();
            opSel.value = 'contains';
            adjustValueVisibility();
            valueInput.value = '';
        }
    }

    addBtn.addEventListener('click', () => addRow());

    form.addEventListener('submit', () => {
        const items = [];
        const rows = rowsContainer.children;
        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            const [fieldSel, opSel, valueInput, emptyModeSel] = row.querySelectorAll('select, input');
            const field = fieldSel.value;
            const op = opSel.value;
            if (op === 'empty') {
                items.push({ field, op, empty_mode: emptyModeSel.value });
            } else {
                const value = valueInput.value.trim();
                if (value !== '') {
                    items.push({ field, op, value });
                }
            }
        }
        const logic = logicSelect.value || 'AND';
        const payload = { logic, items };
        hiddenInput.value = JSON.stringify(payload);
    });

    try {
        const params = new URLSearchParams(window.location.search);
        const raw = params.get('filters');
        if (raw) {
            const parsed = JSON.parse(raw);
            if (parsed && Array.isArray(parsed.items) && parsed.items.length) {
                logicSelect.value = (parsed.logic === 'OR') ? 'OR' : 'AND';
                parsed.items.forEach(it => addRow(it));
            } else {
                addRow();
            }
        } else {
            addRow();
        }
    } catch (err) {
        addRow();
    }
})();
