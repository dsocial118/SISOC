/**
 * Funcionalidades para el modal de búsqueda de localidades.
 */

document.addEventListener('DOMContentLoaded', () => {
  const provinciasDataEl = document.getElementById('provincias-data');
  let provincias = [];
  if (provinciasDataEl) {
    try {
      provincias = JSON.parse(provinciasDataEl.textContent);
    } catch (e) {
      console.error('Error al parsear provincias', e);
    }
  }

  const provinciaSelect = document.getElementById('filtro-provincia');
  const municipioSelect = document.getElementById('filtro-municipio');
  const localidadSelect = document.getElementById('filtro-localidad');
  const tablaLocalidades = document.getElementById('tabla-localidades');
  const textoBusqueda = document.getElementById('filtro-texto');

  let localidadesData = [];

  /**
   * Llena el select de provincias con los datos del contexto.
   */
  function poblarProvincias() {
    if (!provinciaSelect) return;
    provinciaSelect.innerHTML = '<option value="">Todas</option>';
    provincias.forEach((p) => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = `${p.id} - ${p.nombre}`;
      provinciaSelect.appendChild(opt);
    });
  }

  /**
   * Renderiza la tabla de localidades y actualiza selects de municipio y localidad.
   *
   * @param {Array} data - Datos recibidos del servidor.
   */
  function renderLocalidades(data) {
    localidadesData = data;
    municipioSelect.innerHTML = '<option value="">Todos</option>';
    localidadSelect.innerHTML = '<option value="">Todas</option>';

    const municipiosUnicos = new Map();

    data.forEach((item) => {


      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${item.provincia_id} - ${item.provincia_nombre}</td><td>${item.localidad_id} - ${item.localidad_nombre}</td><td>${item.municipio_id} - ${item.municipio_nombre}</td>`;
      tablaLocalidades.appendChild(tr);


      if (!municipiosUnicos.has(item.municipio_id)) {
        municipiosUnicos.set(item.municipio_id, item.municipio_nombre);
      }

      const locOpt = document.createElement('option');
      locOpt.value = item.localidad_id;
      locOpt.textContent = `${item.localidad_id} - ${item.localidad_nombre}`;
      localidadSelect.appendChild(locOpt);
    });

    municipiosUnicos.forEach((nombre, id) => {
      const opt = document.createElement('option');
      opt.value = id;
      opt.textContent = `${id} - ${nombre}`;
      municipioSelect.appendChild(opt);
    });

    filtrarTabla();
  }

  function pintarTabla(data) {
    tablaLocalidades.innerHTML = '';
    data.forEach((item) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${item.provincia_id} - ${item.provincia_nombre}</td><td>${item.localidad_id} - ${item.localidad_nombre}</td><td>${item.municipio_id} - ${item.municipio_nombre}</td>`;
      tablaLocalidades.appendChild(tr);
    });
  }

  function filtrarTabla() {
    const query = textoBusqueda ? textoBusqueda.value.toLowerCase() : '';
    const filtradas = localidadesData.filter((item) => {
      return (
        `${item.provincia_id} - ${item.provincia_nombre}`
          .toLowerCase()
          .includes(query) ||
        `${item.localidad_id} - ${item.localidad_nombre}`
          .toLowerCase()
          .includes(query) ||
        `${item.municipio_id} - ${item.municipio_nombre}`
          .toLowerCase()
          .includes(query)
      );
    });
    pintarTabla(filtradas);
  }

  /**
   * Solicita al servidor las localidades filtradas y actualiza la tabla.
   */
  function actualizarLocalidades() {
    const params = new URLSearchParams();
    if (provinciaSelect.value) params.append('provincia', provinciaSelect.value);
    if (municipioSelect.value) params.append('municipio', municipioSelect.value);

    fetch(`${window.EXPEDIENTE_LOCALIDADES_URL}?${params.toString()}`)
      .then((resp) => resp.json())
      .then((data) => renderLocalidades(data));
  }

  poblarProvincias();
  provinciaSelect.addEventListener('change', () => {
    municipioSelect.innerHTML = '<option value="">Todos</option>';
    localidadSelect.innerHTML = '<option value="">Todas</option>';
    actualizarLocalidades();
  });
  municipioSelect.addEventListener('change', actualizarLocalidades);
  if (textoBusqueda) {
    textoBusqueda.addEventListener('input', filtrarTabla);
  }
});

/**
 * Obtiene el valor de una cookie dada su clave.
 *
 * @param {string} name - Nombre de la cookie.
 * @returns {string|null} Valor de la cookie o null si no existe.
 */
function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^|; )' + name + '=([^;]*)'));
  return match ? decodeURIComponent(match[2]) : null;
}

// Exponer getCookie por si se requieren encabezados CSRF.
window.getCookie = getCookie;
