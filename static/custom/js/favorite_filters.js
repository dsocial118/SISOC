(function () {
    const formulario = document.getElementById('filters-form');
    if (!formulario) {
        return;
    }

    const seccion = formulario.dataset.seccionFiltrosFavoritos;
    const urlListado = formulario.dataset.urlFiltrosFavoritos;
    const plantillaUrlDetalle = formulario.dataset.plantillaUrlFiltroFavorito;
    if (!seccion || !urlListado || !plantillaUrlDetalle) {
        return;
    }

    const modal = document.getElementById('modal-filtros-favoritos');
    const botonAbrir = document.getElementById('abrir-filtros-favoritos');
    const inputNombre = document.getElementById('nombre-filtro-favorito');
    const botonGuardar = document.getElementById('guardar-filtro-favorito');
    const errorNodo = document.getElementById('error-filtro-favorito');
    const listaNodo = document.getElementById('lista-filtros-favoritos');
    const vacioNodo = document.getElementById('filtros-favoritos-vacio');

    const contenedorFilas = document.getElementById('filters-rows');
    const selectorLogica = document.getElementById('filters-logic');

    const claveActivo = `filtrosFavoritosActivos:${seccion}`;

    function leerConfiguracion() {
        const idConfig = formulario.dataset.configId;
        if (!idConfig) {
            return null;
        }
        const scriptConfig = document.getElementById(idConfig);
        if (!scriptConfig) {
            return null;
        }
        try {
            return JSON.parse(scriptConfig.textContent);
        } catch (error) {
            console.warn('FiltrosFavoritos: configuracion JSON invalida.', error);
            return null;
        }
    }

    const configuracion = leerConfiguracion();
    const campos = Array.isArray(configuracion && configuracion.fields) ? configuracion.fields : [];
    const camposPorNombre = campos.reduce((acc, campo) => {
        if (campo && campo.name) {
            acc[campo.name] = campo;
        }
        return acc;
    }, {});

    function obtenerTokenCSRF() {
        const match = document.cookie.match(/(?:^|;)\s*csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    }

    function mostrarError(mensaje) {
        if (!errorNodo) {
            return;
        }
        errorNodo.textContent = mensaje;
        errorNodo.classList.remove('d-none');
    }

    function limpiarError() {
        if (!errorNodo) {
            return;
        }
        errorNodo.textContent = '';
        errorNodo.classList.add('d-none');
    }

    function construirUrlDetalle(id) {
        const url = plantillaUrlDetalle.replace(/0\/?$/, `${id}/`);
        return url;
    }

    function construirCargaFiltros() {
        if (!contenedorFilas || !selectorLogica || !Object.keys(camposPorNombre).length) {
            return null;
        }

        const elementos = [];
        const filas = contenedorFilas.children;

        for (let i = 0; i < filas.length; i += 1) {
            const refs = filas[i]._advancedFilterRefs;
            if (!refs) {
                continue;
            }

            const campo = refs.fieldSel.value;
            const operador = refs.opSel.value;
            const definicionCampo = camposPorNombre[campo];
            if (!definicionCampo || !campo || !operador) {
                continue;
            }

            if (operador === 'empty') {
                elementos.push({
                    field: campo,
                    op: operador,
                    empty_mode: refs.emptyModeSel.value || 'both',
                });
                continue;
            }

            if (definicionCampo.type === 'choice' || definicionCampo.type === 'boolean') {
                const seleccionado = refs.selectValue.value;
                if (seleccionado !== '') {
                    elementos.push({ field: campo, op: operador, value: seleccionado });
                }
                continue;
            }

            const valor = refs.valueInput.value.trim();
            if (valor !== '') {
                elementos.push({ field: campo, op: operador, value: valor });
            }
        }

        const logica = selectorLogica.value || 'AND';
        return { logic: logica, items: elementos };
    }

    async function leerRespuestaJson(respuesta) {
        const texto = await respuesta.text();
        if (!texto) {
            return null;
        }
        try {
            return JSON.parse(texto);
        } catch (error) {
            return null;
        }
    }

    function renderizarFavoritos(favoritos) {
        if (!listaNodo || !vacioNodo) {
            return;
        }

        listaNodo.innerHTML = '';

        if (!favoritos.length) {
            vacioNodo.textContent = 'No hay favoritos guardados.';
            vacioNodo.style.display = 'block';
            return;
        }

        vacioNodo.style.display = 'none';

        favoritos.forEach((favorito) => {
            const elemento = document.createElement('div');
            elemento.className = 'list-group-item d-flex flex-wrap justify-content-between align-items-center gap-2';

            const nombreNodo = document.createElement('div');
            nombreNodo.textContent = favorito.nombre || '';

            const acciones = document.createElement('div');
            acciones.className = 'btn-group btn-group-sm';

            const botonAplicar = document.createElement('button');
            botonAplicar.type = 'button';
            botonAplicar.className = 'btn btn-success';
            botonAplicar.textContent = 'Aplicar';
            botonAplicar.addEventListener('click', () => aplicarFavorito(favorito.id));

            const botonEliminar = document.createElement('button');
            botonEliminar.type = 'button';
            botonEliminar.className = 'btn btn-outline-danger';
            botonEliminar.textContent = 'Eliminar';
            botonEliminar.addEventListener('click', () => eliminarFavorito(favorito.id));

            acciones.appendChild(botonAplicar);
            acciones.appendChild(botonEliminar);

            elemento.appendChild(nombreNodo);
            elemento.appendChild(acciones);
            listaNodo.appendChild(elemento);
        });
    }

    async function cargarFavoritos(opciones) {
        const ajustes = opciones || {};
        const forzar = Boolean(ajustes.forzar);
        if (!listaNodo || !vacioNodo) {
            return;
        }

        limpiarError();
        vacioNodo.textContent = 'Cargando...';
        vacioNodo.style.display = 'block';
        listaNodo.innerHTML = '';

        try {
            const url = `${urlListado}?seccion=${encodeURIComponent(seccion)}${forzar ? '&refrescar=1' : ''}`;
            const respuesta = await fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });
            const data = await leerRespuestaJson(respuesta);
            if (!respuesta.ok) {
                throw new Error((data && data.error) || 'No se pudo cargar los favoritos.');
            }
            if (!data) {
                throw new Error('Respuesta invalida del servidor.');
            }
            const favoritos = Array.isArray(data.favoritos) ? data.favoritos : [];
            renderizarFavoritos(favoritos);
        } catch (error) {
            vacioNodo.textContent = 'No se pudo cargar los favoritos.';
            mostrarError(error.message || 'No se pudo cargar los favoritos.');
        }
    }

    async function guardarFavorito() {
        limpiarError();
        if (!inputNombre) {
            return;
        }
        const nombre = inputNombre.value.trim();
        if (!nombre) {
            mostrarError('El nombre es obligatorio.');
            return;
        }

        const carga = construirCargaFiltros();
        if (!carga) {
            mostrarError('No se pudo leer los filtros actuales.');
            return;
        }

        try {
            const respuesta = await fetch(urlListado, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': obtenerTokenCSRF(),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: JSON.stringify({
                    seccion,
                    nombre,
                    filtros: carga,
                }),
            });
            const data = await leerRespuestaJson(respuesta);
            if (!respuesta.ok) {
                throw new Error((data && data.error) || 'No se pudo guardar el favorito.');
            }
            if (!data) {
                throw new Error('Respuesta invalida del servidor.');
            }
            inputNombre.value = '';
            await cargarFavoritos({ forzar: true });
        } catch (error) {
            mostrarError(error.message || 'No se pudo guardar el favorito.');
        }
    }

    async function aplicarFavorito(id, opciones) {
        const ajustes = opciones || {};
        limpiarError();

        try {
            const url = `${construirUrlDetalle(id)}?seccion=${encodeURIComponent(seccion)}`;
            const respuesta = await fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });
            const data = await leerRespuestaJson(respuesta);
            if (!respuesta.ok) {
                throw new Error((data && data.error) || 'No se pudo aplicar el favorito.');
            }
            if (!data) {
                throw new Error('Respuesta invalida del servidor.');
            }

            guardarFavoritoActivo({ id: data.id, nombre: data.nombre });

            const urlAccion = formulario.getAttribute('action') || window.location.pathname;
            const parametroFiltros = encodeURIComponent(JSON.stringify(data.filtros));
            window.location.assign(`${urlAccion}?filters=${parametroFiltros}`);
        } catch (error) {
            if (ajustes.silencioso) {
                limpiarFavoritoActivo();
                console.warn('FiltrosFavoritos:', error.message || error);
                return;
            }
            mostrarError(error.message || 'No se pudo aplicar el favorito.');
        }
    }

    async function eliminarFavorito(id) {
        limpiarError();
        if (!window.confirm('¿Eliminar filtro permanentemente?')) {
            return;
        }

        try {
            const respuesta = await fetch(construirUrlDetalle(id), {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': obtenerTokenCSRF(),
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });
            const data = await leerRespuestaJson(respuesta);
            if (!respuesta.ok) {
                throw new Error((data && data.error) || 'No se pudo eliminar el favorito.');
            }
            if (!data) {
                throw new Error('Respuesta invalida del servidor.');
            }
            const activo = leerFavoritoActivo();
            if (activo && String(activo.id) === String(id)) {
                limpiarFavoritoActivo();
            }
            await cargarFavoritos();
        } catch (error) {
            mostrarError(error.message || 'No se pudo eliminar el favorito.');
        }
    }

    function guardarFavoritoActivo(valor) {
        try {
            localStorage.setItem(claveActivo, JSON.stringify(valor));
        } catch (error) {
            // Sin almacenamiento disponible.
        }
    }

    function leerFavoritoActivo() {
        try {
            const raw = localStorage.getItem(claveActivo);
            if (!raw) {
                return null;
            }
            return JSON.parse(raw);
        } catch (error) {
            return null;
        }
    }

    function limpiarFavoritoActivo() {
        try {
            localStorage.removeItem(claveActivo);
        } catch (error) {
            // Sin almacenamiento disponible.
        }
    }

    function tieneParametroFiltros() {
        const params = new URLSearchParams(window.location.search);
        return params.has('filters');
    }

    function conectarEnlacesRestablecer() {
        const enlaces = document.querySelectorAll('[data-restablecer-filtros-favoritos="true"]');
        enlaces.forEach((link) => {
            link.addEventListener('click', () => limpiarFavoritoActivo());
        });
    }

    if (botonAbrir) {
        botonAbrir.addEventListener('click', () => cargarFavoritos());
    }
    if (botonGuardar) {
        botonGuardar.addEventListener('click', () => guardarFavorito());
    }

    if (modal) {
        modal.addEventListener('shown.bs.modal', () => {
            if (inputNombre) {
                inputNombre.focus();
            }
        });
    }

    conectarEnlacesRestablecer();

    const activo = leerFavoritoActivo();
    if (activo && activo.id && !tieneParametroFiltros()) {
        aplicarFavorito(activo.id, { silencioso: true });
    }
})();
