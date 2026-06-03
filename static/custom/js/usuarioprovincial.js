document.addEventListener('DOMContentLoaded', function () {
  const provincialCheck = document.getElementById('id_es_usuario_provincial');
  const legacyProvinciaSelect = document.getElementById('id_provincia');
  const hiddenInput = document.getElementById('id_territorial_scopes');
  const panel = document.getElementById('territorial-scopes-panel');
  const list = document.getElementById('territorial-scopes-list');
  const addButton = document.getElementById('add-territorial-scope');
  const form = hiddenInput ? hiddenInput.closest('form') : null;

  if (!provincialCheck || !legacyProvinciaSelect || !hiddenInput || !panel || !list || !addButton) {
    return;
  }

  const municipiosUrl = panel.dataset.municipiosUrl;
  const localidadesUrl = panel.dataset.localidadesUrl;
  let rowCounter = 0;

  const escapeHtml = (value) => String(value || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');

  const provinceOptions = Array.from(legacyProvinciaSelect.options)
    .filter((option) => option.value)
    .map((option) => ({
      id: option.value,
      nombre: option.textContent,
    }));

  const parseJson = (value, fallback) => {
    try {
      const parsed = JSON.parse(value || '');
      return Array.isArray(parsed) ? parsed : fallback;
    } catch (error) {
      return fallback;
    }
  };

  const initialScript = document.getElementById('territorial-scopes-initial');
  const initialScopes = hiddenInput.value
    ? parseJson(hiddenInput.value, [])
    : parseJson(initialScript ? initialScript.textContent : '', []);

  const setSelectOptions = (select, options, placeholder, selectedValue) => {
    select.innerHTML = `<option value="">${escapeHtml(placeholder)}</option>${options
      .map((option) => {
        const selected = String(option.id) === String(selectedValue || '') ? ' selected' : '';
        return `<option value="${escapeHtml(option.id)}"${selected}>${escapeHtml(option.nombre)}</option>`;
      })
      .join('')}`;
    select.disabled = options.length === 0;
  };

  const refreshSelect2 = (select) => {
    if (window.jQuery && window.jQuery.fn && window.jQuery.fn.select2) {
      const $select = window.jQuery(select);
      if (!$select.data('select2')) {
        $select.select2({ width: '100%' });
      }
      $select.trigger('change.select2');
    }
  };

  const bindSelectChange = (select, handler) => {
    if (window.jQuery) {
      window.jQuery(select).on('change.territorialScopes', handler);
      return;
    }
    select.addEventListener('change', handler);
  };

  const fetchOptions = async (url, params) => {
    const requestUrl = new URL(url, window.location.origin);
    Object.entries(params).forEach(([key, value]) => {
      if (value) {
        requestUrl.searchParams.set(key, value);
      }
    });
    const response = await fetch(requestUrl.toString(), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });
    if (!response.ok) {
      return [];
    }
    return response.json();
  };

  const syncHiddenInput = () => {
    if (!provincialCheck.checked) {
      hiddenInput.value = '[]';
      return;
    }

    const scopes = Array.from(list.querySelectorAll('[data-territorial-scope-row]'))
      .map((row) => ({
        provincia_id: row.querySelector('[data-scope-provincia]')?.value || null,
        municipio_id: row.querySelector('[data-scope-municipio]')?.value || null,
        localidad_id: row.querySelector('[data-scope-localidad]')?.value || null,
      }));
    hiddenInput.value = JSON.stringify(scopes);
  };

  const loadMunicipios = async (row, selectedValue = null) => {
    const provinciaSelect = row.querySelector('[data-scope-provincia]');
    const municipioSelect = row.querySelector('[data-scope-municipio]');
    const localidadSelect = row.querySelector('[data-scope-localidad]');
    const provinciaId = provinciaSelect.value;

    setSelectOptions(localidadSelect, [], 'Seleccione municipio primero', null);
    localidadSelect.disabled = true;

    if (!provinciaId) {
      setSelectOptions(municipioSelect, [], 'Seleccione provincia primero', null);
      municipioSelect.disabled = true;
      syncHiddenInput();
      refreshSelect2(municipioSelect);
      refreshSelect2(localidadSelect);
      return;
    }

    const municipios = await fetchOptions(municipiosUrl, { provincia_id: provinciaId });
    setSelectOptions(municipioSelect, municipios, 'Todos los municipios', selectedValue);
    municipioSelect.disabled = false;
    syncHiddenInput();
    refreshSelect2(municipioSelect);
    refreshSelect2(localidadSelect);
  };

  const loadLocalidades = async (row, selectedValue = null) => {
    const municipioSelect = row.querySelector('[data-scope-municipio]');
    const localidadSelect = row.querySelector('[data-scope-localidad]');
    const municipioId = municipioSelect.value;

    if (!municipioId) {
      setSelectOptions(localidadSelect, [], 'Seleccione municipio primero', null);
      localidadSelect.disabled = true;
      syncHiddenInput();
      refreshSelect2(localidadSelect);
      return;
    }

    const localidades = await fetchOptions(localidadesUrl, { municipio_id: municipioId });
    setSelectOptions(localidadSelect, localidades, 'Todas las localidades', selectedValue);
    localidadSelect.disabled = false;
    syncHiddenInput();
    refreshSelect2(localidadSelect);
  };

  const addScopeRow = (scope = {}) => {
    rowCounter += 1;
    const rowId = `territorial-scope-${rowCounter}`;
    const row = document.createElement('tr');
    row.dataset.territorialScopeRow = rowId;
    row.innerHTML = `
      <td>
        <select class="form-control form-control-sm" data-scope-provincia aria-label="Provincia">
        </select>
      </td>
      <td>
        <select class="form-control form-control-sm" data-scope-municipio aria-label="Municipio" disabled>
          <option value="">Seleccione provincia primero</option>
        </select>
      </td>
      <td>
        <select class="form-control form-control-sm" data-scope-localidad aria-label="Localidad" disabled>
          <option value="">Seleccione municipio primero</option>
        </select>
      </td>
      <td class="text-right">
        <button type="button" class="btn btn-outline-danger btn-sm" data-scope-remove>
          <i class="fas fa-trash" aria-hidden="true"></i>
          <span class="sr-only">Quitar alcance</span>
        </button>
      </td>
    `;

    list.appendChild(row);
    const provinciaSelect = row.querySelector('[data-scope-provincia]');
    const municipioSelect = row.querySelector('[data-scope-municipio]');
    const localidadSelect = row.querySelector('[data-scope-localidad]');

    setSelectOptions(provinciaSelect, provinceOptions, 'Seleccione provincia', scope.provincia_id);
    refreshSelect2(provinciaSelect);

    bindSelectChange(provinciaSelect, async () => {
      await loadMunicipios(row);
      syncHiddenInput();
    });
    bindSelectChange(municipioSelect, async () => {
      await loadLocalidades(row);
      syncHiddenInput();
    });
    bindSelectChange(localidadSelect, syncHiddenInput);
    row.querySelector('[data-scope-remove]').addEventListener('click', () => {
      row.remove();
      syncHiddenInput();
    });

    if (scope.provincia_id) {
      loadMunicipios(row, scope.municipio_id).then(() => {
        if (scope.municipio_id) {
          loadLocalidades(row, scope.localidad_id).then(syncHiddenInput);
        } else {
          syncHiddenInput();
        }
      });
    } else {
      syncHiddenInput();
    }
  };

  const togglePanel = () => {
    panel.style.display = provincialCheck.checked ? '' : 'none';
    syncHiddenInput();
  };

  initialScopes.forEach((scope) => addScopeRow(scope));
  addButton.addEventListener('click', () => addScopeRow());
  provincialCheck.addEventListener('change', togglePanel);
  if (form) {
    form.addEventListener('submit', syncHiddenInput);
  }

  togglePanel();
});
