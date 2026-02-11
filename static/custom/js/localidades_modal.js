/**
 * Funcionalidades para el modal de búsqueda de localidades.
 */

document.addEventListener("DOMContentLoaded", () => {
  const provinciasDataEl = document.getElementById("provincias-data");
  let provincias = [];
  if (provinciasDataEl) {
    try {
      provincias = JSON.parse(provinciasDataEl.textContent);
    } catch (e) {
      console.error("Error al parsear provincias", e);
    }
  }

  const provinciaSelect = document.getElementById("filtro-provincia");
  const municipioSelect = document.getElementById("filtro-municipio");
  const localidadSelect = document.getElementById("filtro-localidad");
  const tablaLocalidades = document.getElementById("tabla-localidades");
  const textoBusqueda = document.getElementById("filtro-texto");

  let localidadesData = [];

  /**
   * Llena el select de provincias con los datos del contexto.
   */
  function poblarProvincias() {
    if (!provinciaSelect) return;
    provinciaSelect.innerHTML = '<option value="">Todas</option>';
    provincias.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = `${p.id} - ${p.nombre}`;
      provinciaSelect.appendChild(opt);
    });
  }

  /**
   * Pinta la tabla con los datos proporcionados.
   */
  function pintarTabla(data) {
    tablaLocalidades.innerHTML = "";
    data.forEach((item) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${item.provincia_id} - ${item.provincia_nombre}</td><td>${item.municipio_id} - ${item.municipio_nombre}</td><td>${item.localidad_id} - ${item.localidad_nombre}</td>`;
      tablaLocalidades.appendChild(tr);
    });
  }

  /**
   * Filtra la tabla por texto de búsqueda.
   */
  function filtrarTabla() {
    const query = textoBusqueda ? textoBusqueda.value.toLowerCase() : "";
    const filtradas = localidadesData.filter((item) => {
      return (
        `${item.provincia_id} - ${item.provincia_nombre}`
          .toLowerCase()
          .includes(query) ||
        `${item.municipio_id} - ${item.municipio_nombre}`
          .toLowerCase()
          .includes(query) ||
        `${item.localidad_id} - ${item.localidad_nombre}`
          .toLowerCase()
          .includes(query)
      );
    });
    pintarTabla(filtradas);
  }

  /**
   * Actualiza los selects de municipio y localidad basado en los datos.
   */
  function actualizarSelects(data) {
    // Actualizar municipios
    const municipiosUnicos = new Map();
    data.forEach((item) => {
      if (!municipiosUnicos.has(item.municipio_id)) {
        municipiosUnicos.set(item.municipio_id, item.municipio_nombre);
      }
    });

    const municipioActual = municipioSelect.value;
    municipioSelect.innerHTML = '<option value="">Todos</option>';
    municipiosUnicos.forEach((nombre, id) => {
      const opt = document.createElement("option");
      opt.value = id;
      opt.textContent = `${id} - ${nombre}`;
      municipioSelect.appendChild(opt);
    });

    // Restaurar selección de municipio si existe
    if (municipioActual && municipiosUnicos.has(parseInt(municipioActual))) {
      municipioSelect.value = municipioActual;
    }

    // Actualizar localidades
    localidadSelect.innerHTML = '<option value="">Todas</option>';
    data.forEach((item) => {
      const locOpt = document.createElement("option");
      locOpt.value = item.localidad_id;
      locOpt.textContent = `${item.localidad_id} - ${item.localidad_nombre}`;
      localidadSelect.appendChild(locOpt);
    });
  }

  /**
   * Solicita al servidor las localidades filtradas y actualiza la tabla.
   */
  function cargarLocalidades() {
    const params = new URLSearchParams();
    if (provinciaSelect.value) {
      params.append("provincia", provinciaSelect.value);
    }
    if (municipioSelect.value) {
      params.append("municipio", municipioSelect.value);
    }

    fetch(`${window.EXPEDIENTE_LOCALIDADES_URL}?${params.toString()}`)
      .then((resp) => resp.json())
      .then((data) => {
        localidadesData = data;
        actualizarSelects(data);
        pintarTabla(data);
      })
      .catch((error) => {
        console.error("Error al cargar localidades:", error);
      });
  }

  /**
   * Limpia todos los filtros y recarga todas las localidades.
   */
  function limpiarFiltros() {
    provinciaSelect.value = "";
    municipioSelect.value = "";
    localidadSelect.value = "";
    if (textoBusqueda) textoBusqueda.value = "";
    
    cargarLocalidades();
  }

  /**
   * Descarga los datos actuales de la tabla como CSV.
   */
  function descargarLocalidades() {
    if (localidadesData.length === 0) {
      alert("No hay datos para descargar");
      return;
    }

    // Crear CSV con BOM UTF-8 para Excel
    const BOM = "\uFEFF";
    let csv = BOM + "Provincia ID,Provincia,Municipio ID,Municipio,Localidad ID,Localidad\n";
    localidadesData.forEach((item) => {
      csv += `${item.provincia_id},${item.provincia_nombre},${item.municipio_id},${item.municipio_nombre},${item.localidad_id},${item.localidad_nombre}\n`;
    });

    // Crear blob y descargar
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", "localidades.csv");
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // Inicializar
  poblarProvincias();

  // Eventos
  provinciaSelect.addEventListener("change", () => {
    municipioSelect.value = "";
    localidadSelect.value = "";
    if (textoBusqueda) textoBusqueda.value = "";
    cargarLocalidades();
  });

  municipioSelect.addEventListener("change", cargarLocalidades);

  if (textoBusqueda) {
    textoBusqueda.addEventListener("input", filtrarTabla);
  }

  // Botón limpiar filtros
  const btnLimpiar = document.getElementById("btn-limpiar-filtros");
  if (btnLimpiar) {
    btnLimpiar.addEventListener("click", limpiarFiltros);
  }

  // Botón descargar localidades
  const btnDescargar = document.getElementById("btn-descargar-localidades");
  if (btnDescargar) {
    btnDescargar.addEventListener("click", descargarLocalidades);
  }

  // Cargar datos al abrir el modal
  const modal = document.getElementById("localidadesModal");
  if (modal) {
    modal.addEventListener("shown.bs.modal", () => {
      if (localidadesData.length === 0) {
        cargarLocalidades();
      }
    });
  }
});

/**
 * Obtiene el valor de una cookie dada su clave.
 */
function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^|; )" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[2]) : null;
}

window.getCookie = getCookie;