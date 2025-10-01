(function () {
    /**
     * Beneficiarios Search Bar (filtros combinables)
     * Replica la logica de comedores pero con campos y etiquetas propias.
     */
    const TEXT_FIELDS = [
        { value: 'apellido', label: 'Apellido' },
        { value: 'nombre', label: 'Nombre' },
        { value: 'domicilio', label: 'Domicilio' },
        { value: 'barrio', label: 'Barrio' },
        { value: 'correo_electronico', label: 'Correo electronico' },
        { value: 'responsable_apellido', label: 'Apellido del responsable' },
        { value: 'responsable_nombre', label: 'Nombre del responsable' },
        { value: 'provincia', label: 'Provincia' },
        { value: 'municipio', label: 'Municipio' },
        { value: 'localidad', label: 'Localidad' }
    ];
    const NUMBER_FIELDS = [
        { value: 'dni', label: 'DNI' },
        { value: 'cuil', label: 'CUIL' },
        { value: 'codigo_postal', label: 'Codigo postal' },
        { value: 'altura', label: 'Altura' }
    ];
    const CHOICE_FIELDS = {
        genero: {
            label: 'Genero',
            options: [
                { value: 'F', label: 'Femenino' },
                { value: 'M', label: 'Masculino' },
                { value: 'X', label: 'Otro/No binario' },
            ],
        },
    };

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
    const CHOICE_OPS = [
        { value: 'eq', label: 'Igual a' },
        { value: 'ne', label: 'Distinto de' },
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

    function choiceFieldOptions() {
        return Object.keys(CHOICE_FIELDS).map(key => ({
            value: key,
            label: CHOICE_FIELDS[key].label,
        }));
    }

    function fieldOptions() {
        return [
            ...TEXT_FIELDS,
            ...NUMBER_FIELDS,
            ...choiceFieldOptions(),
        ];
    }

    function isChoiceField(field) {
        return Object.prototype.hasOwnProperty.call(CHOICE_FIELDS, field);
    }

    function getChoiceOptions(field) {
        return isChoiceField(field) ? CHOICE_FIELDS[field].options : [];
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

        const choiceValueSel = createSelect([], 'form-select form-select-sm');
        choiceValueSel.style.display = 'none';

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
            const isChoice = isChoiceField(field);
            opSel.innerHTML = '';
            const ops = isNum ? NUM_OPS : (isChoice ? CHOICE_OPS : TEXT_OPS);
            ops.forEach(opt => {
                const o = document.createElement('option');
                o.value = opt.value;
                o.textContent = opt.label;
                opSel.appendChild(o);
            });
            if (isChoice) {
                opSel.value = 'eq';
            } else {
                opSel.value = isNum ? 'eq' : 'contains';
            }

            if (isChoice) {
                const choiceOpts = getChoiceOptions(field);
                choiceValueSel.innerHTML = '';
                choiceOpts.forEach(opt => {
                    const option = document.createElement('option');
                    option.value = opt.value;
                    option.textContent = opt.label;
                    choiceValueSel.appendChild(option);
                });
                if (choiceOpts.length) {
                    choiceValueSel.value = choiceOpts[0].value;
                }
            }
            adjustValueVisibility();
        }

        function adjustValueVisibility() {
            const op = opSel.value;
            const field = fieldSel.value;
            const isNum = isNumberField(field);
            const isChoice = isChoiceField(field);

            if (isChoice) {
                valueInput.style.display = 'none';
                emptyModeSel.style.display = 'none';
                choiceValueSel.style.display = 'inline-block';
                return;
            }

            choiceValueSel.style.display = 'none';

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
        row.appendChild(choiceValueSel);
        row.appendChild(emptyModeSel);
        row.appendChild(removeBtn);
        rowsContainer.appendChild(row);

        row._fieldSel = fieldSel;
        row._opSel = opSel;
        row._valueInput = valueInput;
        row._choiceSel = choiceValueSel;
        row._emptyModeSel = emptyModeSel;

        if (prefill) {
            if (prefill.field) fieldSel.value = prefill.field;
            refreshOps();
            if (prefill.op) opSel.value = prefill.op;
            adjustValueVisibility();
            if (prefill.op === 'empty') {
                emptyModeSel.value = (prefill.empty_mode || 'both');
            } else if (typeof prefill.value !== 'undefined') {
                if (isChoiceField(fieldSel.value)) {
                    choiceValueSel.value = prefill.value;
                } else {
                    valueInput.value = prefill.value;
                }
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
            const fieldSel = row._fieldSel;
            const opSel = row._opSel;
            const valueInput = row._valueInput;
            const choiceSel = row._choiceSel;
            const emptyModeSel = row._emptyModeSel;

            const field = fieldSel.value;
            const op = opSel.value;

            if (op === 'empty') {
                items.push({ field, op, empty_mode: emptyModeSel.value });
            } else if (isChoiceField(field)) {
                const selected = choiceSel.value;
                if (selected) {
                    items.push({ field, op, value: selected });
                }
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
