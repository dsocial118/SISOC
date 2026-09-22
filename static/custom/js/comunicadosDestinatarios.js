/**
 * COMUNICADOS - SELECCION PERSONALIZADA DE DESTINATARIOS (issue #2505)
 *
 * Cada panel (comedores / organizaciones) arma filtros combinables con los
 * mismos campos que el listado correspondiente, los manda al backend y permite
 * elegir resultados de a uno o todos los que matchean. Los filtros se pueden
 * cambiar y volver a buscar: la seleccion ya hecha se conserva.
 */
(function () {
    "use strict";

    function leerJSON(id) {
        var el = document.getElementById(id);
        if (!el) return null;
        try {
            return JSON.parse(el.textContent);
        } catch (error) {
            console.error("Destinatarios: JSON invalido en #" + id, error);
            return null;
        }
    }

    var CONFIGS = leerJSON("destinatarios-filters-config") || {};
    var URLS = leerJSON("destinatarios-urls") || {};
    var SELECCIONADOS = leerJSON("destinatarios-seleccionados") || {};

    var ETIQUETA_OPERADOR = {
        contains: "contiene",
        ncontains: "no contiene",
        eq: "es igual a",
        ne: "es distinto de",
        gt: "mayor que",
        lt: "menor que",
        gte: "mayor o igual",
        lte: "menor o igual",
        empty: "está vacío",
    };

    var OPCIONES_BOOLEANAS = [
        { value: "true", label: "Sí" },
        { value: "false", label: "No" },
    ];

    function crearOpcion(value, label) {
        var option = document.createElement("option");
        option.value = value;
        option.textContent = label;
        return option;
    }

    function poblar(select, opciones) {
        select.innerHTML = "";
        opciones.forEach(function (opcion) {
            select.appendChild(crearOpcion(opcion.value, opcion.label));
        });
    }

    function mostrar(el, visible) {
        if (!el) return;
        el.hidden = !visible;
    }

    function PanelDestinatarios(root) {
        this.root = root;
        this.universo = root.dataset.universo;
        this.config = CONFIGS[this.universo] || {};
        this.urls = URLS[this.universo] || {};
        this.campos = Array.isArray(this.config.fields) ? this.config.fields : [];
        this.operadores = this.config.operators || {};
        this.camposPorNombre = this.campos.reduce(function (acc, campo) {
            if (campo && campo.name) acc[campo.name] = campo;
            return acc;
        }, {});

        this.refs = {
            filas: root.querySelector('[data-rol="filas"]'),
            template: root.querySelector('[data-rol="fila-template"]'),
            agregarFiltro: root.querySelector('[data-rol="agregar-filtro"]'),
            limpiar: root.querySelector('[data-rol="limpiar"]'),
            buscar: root.querySelector('[data-rol="buscar"]'),
            resumen: root.querySelector('[data-rol="resumen"]'),
            agregarTodos: root.querySelector('[data-rol="agregar-todos"]'),
            lista: root.querySelector('[data-rol="lista"]'),
            paginacion: root.querySelector('[data-rol="paginacion"]'),
            seleccionados: root.querySelector('[data-rol="seleccionados"]'),
            contador: root.querySelector('[data-rol="contador"]'),
            inputs: root.querySelector('[data-rol="inputs"]'),
            limpiarSeleccion: root.querySelector('[data-rol="limpiar-seleccion"]'),
        };

        // id -> nombre. Es la unica fuente de verdad de lo elegido.
        this.seleccion = new Map();
        (SELECCIONADOS[this.universo] || []).forEach(
            function (item) {
                this.seleccion.set(String(item.id), item.nombre);
            }.bind(this)
        );

        this.ultimaBusqueda = null;
        this.paginaActual = 1;
        this.cargando = false;
    }

    PanelDestinatarios.prototype.init = function () {
        if (!this.refs.filas || !this.refs.template || !this.campos.length) {
            return;
        }
        this.refs.agregarFiltro.addEventListener(
            "click",
            function () {
                this.crearFila();
            }.bind(this)
        );
        this.refs.limpiar.addEventListener("click", this.limpiarFiltros.bind(this));
        this.refs.buscar.addEventListener(
            "click",
            function () {
                this.buscar(1);
            }.bind(this)
        );
        this.refs.agregarTodos.addEventListener(
            "click",
            this.agregarTodosLosResultados.bind(this)
        );
        this.refs.limpiarSeleccion.addEventListener(
            "click",
            function () {
                this.seleccion.clear();
                this.renderSeleccion();
                this.renderResultados();
            }.bind(this)
        );

        this.crearFila();
        this.renderSeleccion();
    };

    // --- Filtros -----------------------------------------------------------

    PanelDestinatarios.prototype.crearFila = function () {
        var fragmento = this.refs.template.content.cloneNode(true);
        var fila = fragmento.querySelector(".destinatarios-filtro-row");
        var refs = {
            campo: fila.querySelector('[data-rol="campo"]'),
            operador: fila.querySelector('[data-rol="operador"]'),
            valor: fila.querySelector('[data-rol="valor"]'),
            valorSelect: fila.querySelector('[data-rol="valor-select"]'),
            quitar: fila.querySelector('[data-rol="quitar"]'),
        };

        poblar(
            refs.campo,
            this.campos.map(function (campo) {
                return { value: campo.name, label: campo.label };
            })
        );
        if (this.config.defaultField && this.camposPorNombre[this.config.defaultField]) {
            refs.campo.value = this.config.defaultField;
        }

        var ajustar = this.ajustarFila.bind(this, refs);
        refs.campo.addEventListener("change", function () {
            refs.valor.value = "";
            ajustar();
        });
        refs.quitar.addEventListener(
            "click",
            function () {
                fila.remove();
                this.renumerar();
            }.bind(this)
        );
        refs.valor.addEventListener(
            "keydown",
            function (event) {
                if (event.key === "Enter") {
                    event.preventDefault();
                    this.buscar(1);
                }
            }.bind(this)
        );

        fila._refs = refs;
        this.refs.filas.appendChild(fila);
        ajustar();
        this.renumerar();
        return refs;
    };

    PanelDestinatarios.prototype.ajustarFila = function (refs) {
        var campo = this.camposPorNombre[refs.campo.value] || this.campos[0];
        var tipo = campo.type || "text";
        var ops = this.operadores[tipo] || ["eq"];

        poblar(
            refs.operador,
            ops.map(function (op) {
                return { value: op, label: ETIQUETA_OPERADOR[op] || op };
            })
        );

        var esVacio = refs.operador.value === "empty";
        if (tipo === "choice" || tipo === "boolean") {
            var opciones =
                tipo === "boolean"
                    ? OPCIONES_BOOLEANAS
                    : Array.isArray(campo.choices)
                      ? campo.choices
                      : [];
            poblar(refs.valorSelect, [{ value: "", label: "Seleccionar" }].concat(opciones));
            mostrar(refs.valorSelect, !esVacio);
            mostrar(refs.valor, false);
        } else {
            mostrar(refs.valorSelect, false);
            mostrar(refs.valor, !esVacio);
            refs.valor.type = tipo === "number" ? "number" : tipo === "date" ? "date" : "text";
            if (tipo === "number" && campo.input && campo.input.step) {
                refs.valor.step = campo.input.step;
            } else {
                refs.valor.removeAttribute("step");
            }
        }

        refs.operador.onchange = function () {
            var vacio = refs.operador.value === "empty";
            if (tipo === "choice" || tipo === "boolean") {
                mostrar(refs.valorSelect, !vacio);
            } else {
                mostrar(refs.valor, !vacio);
            }
        };
    };

    PanelDestinatarios.prototype.renumerar = function () {
        var filas = Array.from(this.refs.filas.children);
        filas.forEach(function (fila, indice) {
            if (!fila._refs) return;
            fila._refs.valor.placeholder = "Valor del filtro " + (indice + 1);
            mostrar(fila._refs.quitar, filas.length > 1);
        });
        if (!filas.length) {
            this.crearFila();
        }
    };

    PanelDestinatarios.prototype.limpiarFiltros = function () {
        this.refs.filas.innerHTML = "";
        this.crearFila();
        this.ultimaBusqueda = null;
        this.refs.lista.innerHTML = "";
        this.refs.paginacion.innerHTML = "";
        mostrar(this.refs.agregarTodos, false);
        this.refs.resumen.textContent = "Usá los filtros y presioná Buscar.";
    };

    PanelDestinatarios.prototype.recolectarFiltros = function () {
        var items = [];
        Array.from(this.refs.filas.children).forEach(
            function (fila) {
                var refs = fila._refs;
                if (!refs) return;
                var field = refs.campo.value;
                var campo = this.camposPorNombre[field];
                if (!campo) return;
                var op = refs.operador.value;
                if (op === "empty") {
                    items.push({ field: field, op: op });
                    return;
                }
                var tipo = campo.type || "text";
                var valor =
                    tipo === "choice" || tipo === "boolean"
                        ? refs.valorSelect.value
                        : refs.valor.value.trim();
                if (valor !== "") {
                    items.push({ field: field, op: op, value: valor });
                }
            }.bind(this)
        );
        return { logic: "AND", items: items };
    };

    // --- Busqueda ----------------------------------------------------------

    PanelDestinatarios.prototype.construirUrl = function (base, pagina) {
        var url = new URL(base, window.location.origin);
        url.searchParams.set("filters", JSON.stringify(this.ultimaBusqueda));
        if (pagina) {
            url.searchParams.set("page", String(pagina));
        }
        return url.toString();
    };

    PanelDestinatarios.prototype.buscar = function (pagina) {
        if (this.cargando || !this.urls.buscar) return;
        this.ultimaBusqueda = this.recolectarFiltros();
        this.paginaActual = pagina || 1;
        this.cargando = true;
        this.refs.resumen.textContent = "Buscando...";

        fetch(this.construirUrl(this.urls.buscar, this.paginaActual), {
            headers: { "X-Requested-With": "XMLHttpRequest" },
            credentials: "same-origin",
        })
            .then(function (response) {
                if (!response.ok) throw new Error("HTTP " + response.status);
                return response.json();
            })
            .then(
                function (data) {
                    this.ultimoResultado = data;
                    this.renderResultados();
                }.bind(this)
            )
            .catch(
                function (error) {
                    console.error("Destinatarios: error al buscar.", error);
                    this.refs.resumen.textContent =
                        "No se pudo completar la búsqueda. Intentá nuevamente.";
                    this.refs.lista.innerHTML = "";
                    this.refs.paginacion.innerHTML = "";
                }.bind(this)
            )
            .finally(
                function () {
                    this.cargando = false;
                }.bind(this)
            );
    };

    PanelDestinatarios.prototype.agregarTodosLosResultados = function () {
        if (this.cargando || !this.urls.todos || !this.ultimaBusqueda) return;
        this.cargando = true;
        this.refs.agregarTodos.disabled = true;

        fetch(this.construirUrl(this.urls.todos, null), {
            headers: { "X-Requested-With": "XMLHttpRequest" },
            credentials: "same-origin",
        })
            .then(function (response) {
                if (!response.ok) throw new Error("HTTP " + response.status);
                return response.json();
            })
            .then(
                function (data) {
                    if (data.truncado) {
                        this.refs.resumen.textContent =
                            "Son " +
                            data.total +
                            " resultados y el máximo para agregar de una vez es " +
                            data.max_seleccion_masiva +
                            ". Afiná los filtros.";
                        return;
                    }
                    (data.results || []).forEach(
                        function (item) {
                            this.seleccion.set(String(item.id), item.nombre);
                        }.bind(this)
                    );
                    this.renderSeleccion();
                    this.renderResultados();
                }.bind(this)
            )
            .catch(
                function (error) {
                    console.error("Destinatarios: error al agregar todos.", error);
                }.bind(this)
            )
            .finally(
                function () {
                    this.cargando = false;
                    this.refs.agregarTodos.disabled = false;
                }.bind(this)
            );
    };

    // --- Render ------------------------------------------------------------

    PanelDestinatarios.prototype.renderResultados = function () {
        var data = this.ultimoResultado;
        if (!data) return;

        var total = data.total || 0;
        this.refs.resumen.textContent =
            total === 0
                ? "No se encontraron resultados con esos filtros."
                : total + " resultado(s) encontrado(s).";
        mostrar(this.refs.agregarTodos, total > 0);

        this.refs.lista.innerHTML = "";
        (data.results || []).forEach(
            function (item) {
                this.refs.lista.appendChild(this.filaResultado(item));
            }.bind(this)
        );

        this.renderPaginacion(data);
    };

    PanelDestinatarios.prototype.filaResultado = function (item) {
        var id = String(item.id);
        var elegido = this.seleccion.has(id);

        var fila = document.createElement("div");
        fila.className = "comedor-row";

        var info = document.createElement("span");
        info.className = "comedor-nombre";
        info.textContent = item.nombre;
        if (item.detalle) {
            var detalle = document.createElement("small");
            detalle.className = "destinatarios-detalle";
            detalle.textContent = item.detalle;
            info.appendChild(document.createElement("br"));
            info.appendChild(detalle);
        }

        var boton = document.createElement("button");
        boton.type = "button";
        if (elegido) {
            boton.className = "btn btn-sm btn-outline-danger";
            boton.innerHTML = '<i class="fas fa-times"></i> Quitar';
        } else {
            boton.className = "btn btn-sm btn-outline-warning";
            boton.innerHTML = '<i class="fas fa-plus"></i> Agregar';
        }
        boton.addEventListener(
            "click",
            function () {
                if (this.seleccion.has(id)) {
                    this.seleccion.delete(id);
                } else {
                    this.seleccion.set(id, item.nombre);
                }
                this.renderSeleccion();
                this.renderResultados();
            }.bind(this)
        );

        fila.appendChild(info);
        fila.appendChild(boton);
        return fila;
    };

    PanelDestinatarios.prototype.renderPaginacion = function (data) {
        this.refs.paginacion.innerHTML = "";
        var pagina = data.page || 1;
        if (pagina <= 1 && !data.has_more) return;

        var crearBoton = function (texto, destino, habilitado) {
            var boton = document.createElement("button");
            boton.type = "button";
            boton.className = "btn btn-sm btn-outline-light";
            boton.textContent = texto;
            boton.disabled = !habilitado;
            boton.addEventListener(
                "click",
                function () {
                    this.buscar(destino);
                }.bind(this)
            );
            return boton;
        }.bind(this);

        this.refs.paginacion.appendChild(crearBoton("Anterior", pagina - 1, pagina > 1));
        var indicador = document.createElement("span");
        indicador.className = "destinatarios-pagina";
        indicador.textContent = "Página " + pagina;
        this.refs.paginacion.appendChild(indicador);
        this.refs.paginacion.appendChild(
            crearBoton("Siguiente", pagina + 1, Boolean(data.has_more))
        );
    };

    PanelDestinatarios.prototype.renderSeleccion = function () {
        this.refs.contador.textContent = String(this.seleccion.size);
        this.refs.seleccionados.innerHTML = "";

        if (!this.seleccion.size) {
            var vacio = document.createElement("p");
            vacio.className = "small mb-0";
            vacio.style.color = "#6b7280";
            vacio.textContent = "No hay destinatarios seleccionados.";
            this.refs.seleccionados.appendChild(vacio);
        } else {
            this.seleccion.forEach(
                function (nombre, id) {
                    var badge = document.createElement("span");
                    badge.className =
                        "badge me-1 mb-1 d-inline-flex align-items-center gap-1";
                    badge.appendChild(document.createTextNode(nombre + " "));

                    var cerrar = document.createElement("button");
                    cerrar.type = "button";
                    cerrar.className = "btn-close btn-close-white";
                    cerrar.style.fontSize = "0.55em";
                    cerrar.setAttribute("aria-label", "Quitar " + nombre);
                    cerrar.addEventListener(
                        "click",
                        function () {
                            this.seleccion.delete(id);
                            this.renderSeleccion();
                            this.renderResultados();
                        }.bind(this)
                    );
                    badge.appendChild(cerrar);
                    this.refs.seleccionados.appendChild(badge);
                }.bind(this)
            );
        }

        // Inputs ocultos: lo que realmente viaja en el POST.
        this.refs.inputs.innerHTML = "";
        this.seleccion.forEach(
            function (_nombre, id) {
                var input = document.createElement("input");
                input.type = "hidden";
                input.name = this.universo;
                input.value = id;
                this.refs.inputs.appendChild(input);
            }.bind(this)
        );
    };

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll(".destinatarios-panel").forEach(function (root) {
            new PanelDestinatarios(root).init();
        });
    });
})();
