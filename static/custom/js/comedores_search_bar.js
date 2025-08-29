
(function () {
    /**
     * Comedores Search Bar (filtros combinables)
     * - Construye dinámicamente filas de filtros (campo/op/valor) y serializa
     *   a un único parámetro GET `filters` para que el backend lo procese.
     * - Mantiene compatibilidad con la UI existente.
     */
    const TEXT_FIELDS = [
        { value: 'nombre', label: 'Nombre' },
        { value: 'estado', label: 'Estado' },
        { value: 'calle', label: 'Calle' },
        { value: 'piso', label: 'Piso' },
        { value: 'departamento', label: 'Departamento' },
        { value: 'manzana', label: 'Manzana' },
        { value: 'lote', label: 'Lote' },
        { value: 'entre_calle_1', label: 'Entre calle 1' },
        { value: 'entre_calle_2', label: 'Entre calle 2' },
        { value: 'partido', label: 'Partido' },
        { value: 'barrio', label: 'Barrio' },
        { value: 'organizacion', label: 'Organización (nombre)' },
        { value: 'programa', label: 'Programa (nombre)' },
        { value: 'tipocomedor', label: 'Tipo de comedor (nombre)' },
        { value: 'dupla', label: 'Dupla (nombre)' },
        { value: 'provincia', label: 'Provincia (nombre)' },
        { value: 'municipio', label: 'Municipio (nombre)' },
        { value: 'localidad', label: 'Localidad (nombre)' },
        { value: 'referente', label: 'Referente (nombre)' },
        { value: 'codigo_de_proyecto', label: 'Código de proyecto' }
    ];
    const NUMBER_FIELDS = [
        { value: 'id', label: 'ID' },
        { value: 'id_externo', label: 'ID Externo' },
        { value: 'comienzo', label: 'Comienzo (año)' },
        { value: 'numero', label: 'Número' },
        { value: 'codigo_postal', label: 'Código Postal' },
        { value: 'latitud', label: 'Latitud' },
        { value: 'longitud', label: 'Longitud' }
    ];

    const TEXT_OPS = [
        { value: 'contains', label: 'Contiene' },
        { value: 'ncontains', label: 'No contiene' },
        { value: 'eq', label: 'Igual a' },
        { value: 'ne', label: 'Distinto de' },
        { value: 'empty', label: 'Vacío' }
    ];
    const NUM_OPS = [
        { value: 'eq', label: 'Igual a' },
        { value: 'ne', label: 'Distinto de' },
        { value: 'gt', label: 'Mayor a' },
        { value: 'lt', label: 'Menor a' },
        { value: 'empty', label: 'Vacío' }
    ];

    const rowsContainer = document.getElementById('filters-rows');
    const addBtn = document.getElementById('add-filter');
    const form = document.getElementById('filters-form');
    const logicSelect = document.getElementById('filters-logic');
    const hiddenInput = document.getElementById('filters-input');

    /** Crea un <select> con opciones dadas y clases de estilo */
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

    /** Opciones de campo disponibles (texto + numéricos) */
    function fieldOptions() {
        const groupLabel = (txt) => ({ value: '', label: `-- ${txt} --`, disabled: true });
        return [
            ...TEXT_FIELDS,
            ...NUMBER_FIELDS
        ];
    }

    /**
     * Agrega una fila de filtros.
     * - Si `prefill` está presente, setea valores iniciales.
     * - Ajusta operadores y visibilidad de controles según tipo/operador.
     */
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
            { value: 'both', label: 'Nulos o vacíos' },
            { value: 'null', label: 'Solo nulos' },
            { value: 'blank', label: 'Solo vacíos' }
        ], 'form-select');
        emptyModeSel.style.display = 'none';

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-sm btn-outline-danger';
        removeBtn.textContent = '–';

        // Helpers
        function isNumberField(f) {
            return NUMBER_FIELDS.some(n => n.value === f);
        }

        /** Recalcula operadores válidos según el tipo del campo */
        function refreshOps() {
            const field = fieldSel.value;
            const isNum = isNumberField(field);
            // replace options
            opSel.innerHTML = '';
            const ops = isNum ? NUM_OPS : TEXT_OPS;
            ops.forEach(opt => {
                const o = document.createElement('option');
                o.value = opt.value;
                o.textContent = opt.label;
                opSel.appendChild(o);
            });
            // default op
            opSel.value = isNum ? 'eq' : 'contains';
            adjustValueVisibility();
        }

        /** Muestra/oculta controles de valor vs. empty_mode */
        function adjustValueVisibility() {
            const op = opSel.value;
            const field = fieldSel.value;
            const isNum = isNumberField(field);
            if (op === 'empty') {
                valueInput.style.display = 'none';
                emptyModeSel.style.display = 'inline-block';
                if (isNum) {
                    // blank no aplica, ocultarlo
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
                // tipo input
                if (isNum) {
                    valueInput.type = (field === 'latitud' || field === 'longitud') ? 'number' : 'number';
                    valueInput.step = (field === 'latitud' || field === 'longitud') ? 'any' : '1';
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

        // Prefill
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
            // defaults
            fieldSel.value = 'nombre';
            refreshOps();
            opSel.value = 'contains';
            adjustValueVisibility();
            valueInput.value = '';
        }
    }

    addBtn.addEventListener('click', () => addRow());

    // Serializa las filas al payload `filters` antes de enviar
    form.addEventListener('submit', (e) => {
        // construir payload
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

    // Pre-cargar desde querystring si existe
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
