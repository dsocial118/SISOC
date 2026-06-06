/*
 * SisocVatTour
 *
 * Wrapper sobre driver.js para tours guiados del modulo VAT.
 * El partial vat/partials/tour.html inyecta window.SISOC_VAT_TOUR con
 * la seccion actual (si la pagina la conoce) y un flag autoStart.
 * Si no hay seccion, se autodetecta por pathname.
 *
 * Politica de auto-launch:
 *  - El tour GENERAL se autolanza una unica vez, solo en la pantalla de
 *    entrada al modulo (/vat/centros/). Es la "bienvenida" al modulo.
 *  - Cada SECCION se autolanza una unica vez la primera vez que el
 *    usuario abre esa pantalla. Cada seccion tiene su propio storage key.
 *  - Desde el boton "Tour de ayuda" se pueden relanzar manualmente, o
 *    reiniciar todos los tours vistos.
 */
(function () {
    "use strict";

    if (!window.driver || typeof window.driver.js === "undefined") {
        console.warn("[vat_tour] driver.js no esta cargado");
        return;
    }

    var driverFactory = window.driver.js.driver;
    var GENERAL_KEY = "sisoc_vat_tour_general_seen_v2";
    var SECTION_KEY_PREFIX = "sisoc_vat_tour_section_v2_";
    var GENERAL_ENTRY_PATH_RE = /\/vat\/centros\/?$/;

    function safeGet(k) {
        try { return localStorage.getItem(k); } catch (e) { return null; }
    }
    function safeSet(k, v) {
        try { localStorage.setItem(k, v); } catch (e) {}
    }
    function safeRemove(k) {
        try { localStorage.removeItem(k); } catch (e) {}
    }

    // Un elemento sirve para resaltar solo si esta presente Y visible: si esta
    // oculto o tiene tamaño 0, driver.js termina mostrando el popover en una
    // esquina. Se considera no visible si display:none/visibility:hidden o si
    // su bounding box es 0x0.
    function isElementVisible(el) {
        if (!el) return false;
        var style = window.getComputedStyle(el);
        if (style.display === "none" || style.visibility === "hidden") {
            return false;
        }
        var rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    }

    // Conserva solo los steps utilizables. Steps sin element (popovers
    // centrados) siempre se conservan. Steps con onHighlightStarted se
    // conservan aunque el elemento este oculto, porque ese callback revela su
    // panel (ej. pestañas del detalle de centro). El resto debe estar visible.
    function keepExistingSteps(steps) {
        return steps.filter(function (step) {
            if (!step.element) return true;
            try {
                var el = document.querySelector(step.element);
                if (el === null) return false;
                if (step.onHighlightStarted) return true;
                return isElementVisible(el);
            } catch (e) {
                return false;
            }
        });
    }

    // Activa una pestaña lateral del detalle de centro clickeando su tab.
    // Se usa antes de marcar elementos que viven en paneles ocultos
    // (ubicaciones, contactos), porque driver.js no puede resaltar
    // elementos con display:none/visibility:hidden.
    function activateCentroPanel(panelName) {
        // Los tabs viven en dos contenedores (izquierdo y derecho); el que
        // no corresponde al panel activo queda con [hidden]. Usamos el
        // primero visible para disparar el cambio.
        var tabs = document.querySelectorAll(
            "[data-sisoc-tab-target='" + panelName + "']"
        );
        for (var i = 0; i < tabs.length; i++) {
            var t = tabs[i];
            if (!t.hasAttribute("hidden") && typeof t.click === "function") {
                t.click();
                return;
            }
        }
        // Fallback: si todos estan hidden, clickeamos el primero igual.
        if (tabs.length && typeof tabs[0].click === "function") {
            tabs[0].click();
        }
    }
    function panelActivator(panelName) {
        return function () { activateCentroPanel(panelName); };
    }

    // Espera hasta que aparezca un elemento (selectores soportados por
    // querySelector). Resuelve igual al timeout. Lo usamos para tours
    // que dependen de bloques cargados por AJAX (ej. panel de cursos).
    function waitForElement(selector, timeoutMs) {
        return new Promise(function (resolve) {
            if (!selector) return resolve(null);
            var found = document.querySelector(selector);
            if (found) return resolve(found);
            var start = Date.now();
            var iv = setInterval(function () {
                var el = document.querySelector(selector);
                if (el || Date.now() - start > timeoutMs) {
                    clearInterval(iv);
                    resolve(el);
                }
            }, 150);
        });
    }

    function runDriver(steps, opts) {
        var filtered = keepExistingSteps(steps);
        if (filtered.length === 0) {
            console.info("[vat_tour] no hay elementos visibles para este tour");
            return;
        }
        var config = Object.assign(
            {
                showProgress: true,
                allowClose: true,
                showButtons: ["next", "previous", "close"],
                nextBtnText: "Siguiente",
                prevBtnText: "Anterior",
                doneBtnText: "Finalizar",
                progressText: "{{current}} de {{total}}",
                steps: filtered,
            },
            opts || {}
        );
        driverFactory(config).drive();
    }

    // ----------------------------- TOUR GENERAL -----------------------------
    // Recorre el modulo de punta a punta explicando el flujo: que se hace
    // primero, que despues y donde encontrar cada cosa.
    var generalSteps = [
        {
            popover: {
                title: "Bienvenido al modulo VAT",
                description:
                    "VAT gestiona la oferta academica: centros, planes, comisiones, inscripciones y asistencia. Te muestro el recorrido completo en pocos pasos.",
            },
        },
        {
            popover: {
                title: "El flujo de trabajo",
                description:
                    "<b>1.</b> Das de alta un <b>Centro</b>.<br><b>2.</b> Cargas una <b>Oferta institucional</b> en ese centro.<br><b>3.</b> Creas <b>Comisiones</b> con sus horarios.<br><b>4.</b> <b>Inscribis</b> personas.<br><b>5.</b> Tomas <b>Asistencia</b> por sesion.",
            },
        },
        {
            element: 'a[href*="/vat/centros"]',
            popover: {
                title: "1. Centros",
                description:
                    "Sedes donde se dicta la oferta. Cada centro tiene contacto, ubicacion, organizacion y los cursos/comisiones que ofrece.",
                side: "right",
            },
        },
        {
            element: 'a[href*="/vat/ofertas-institucionales"]',
            popover: {
                title: "2. Oferta institucional",
                description:
                    "Asocias un centro con un plan curricular y un ciclo lectivo. Aca podes activar voucher si la oferta lo usa.",
                side: "right",
            },
        },
        {
            element: 'a[href*="/vat/comisiones"]',
            popover: {
                title: "3. Comisiones y horarios",
                description:
                    "Instancia concreta de la oferta: codigo, fechas, cupo y horarios. De cada comision salen las sesiones donde se toma asistencia.",
                side: "right",
            },
        },
        {
            element: 'a[href*="/vat/inscripciones-oferta"], a[href*="/vat/inscripciones/"]',
            popover: {
                title: "4. Inscripciones",
                description:
                    "Inscribis personas a la oferta o directo a una comision. El sistema controla cupo y maneja lista de espera.",
                side: "right",
            },
        },
        {
            element: 'a[href*="/asistencia/"], a[href*="/vat/comisiones/sesiones"]',
            popover: {
                title: "5. Asistencia por sesion",
                description:
                    "En cada sesion programada marcas presentes/ausentes para los inscriptos de esa comision.",
                side: "right",
            },
        },
        {
            element: 'a[href*="/vat/catalogos"], a[href*="/vat/modalidades"]',
            popover: {
                title: "Catalogos academicos",
                description:
                    "Sectores, subsectores, modalidades de cursada, titulos de referencia y planes curriculares. Son los datos maestros que usan las ofertas.",
                side: "right",
            },
        },
        {
            element: 'a[href*="/vat/vouchers"]',
            popover: {
                title: "Vouchers",
                description:
                    "Si la oferta usa voucher: definis parametrias, asignas (individual o masivamente), recargas y cancelas.",
                side: "right",
            },
        },
        {
            element: 'a[href*="/vat/evaluaciones"], a[href*="/vat/resultados"]',
            popover: {
                title: "Evaluaciones",
                description:
                    "Cargas evaluaciones y los resultados por participante.",
                side: "right",
            },
        },
        {
            element: '[data-vat-tour="help-button"]',
            popover: {
                title: "Boton de ayuda",
                description:
                    "Desde aca podes relanzar este tour, ver el tour de la pantalla actual o reiniciar los tours ya vistos.",
                side: "left",
            },
        },
    ];

    // -------------------------- TOURS POR SECCION ---------------------------
    // Cada seccion explica funcionalidades reales: que se busca, que se
    // crea, que columnas hay, que acciones existen por fila, etc.

    var sectionSteps = {
        // -------------------- CENTROS --------------------
        centros_list: [
            {
                popover: {
                    title: "Listado de Centros",
                    description:
                        "Aca administras todas las sedes donde se dicta la oferta. Desde esta pantalla creas, buscas y entras al detalle de cada centro.",
                },
            },
            {
                element: "#simple-search-form, #ajax-search-input",
                popover: {
                    title: "Buscador",
                    description:
                        "Filtra por nombre o direccion. La busqueda se aplica al apretar Enter o el icono de lupa.",
                },
            },
            {
                element: ".search-actions a.btn-primary, .search-actions [href*='/nuevo/']",
                popover: {
                    title: "Agregar centro",
                    description:
                        "Abre el formulario para dar de alta un centro nuevo con sus datos basicos y de contacto.",
                },
            },
            {
                element: "#centros-table-body",
                popover: {
                    title: "Tabla de centros",
                    description:
                        "Cada fila es un centro. El nombre es un link que lleva al detalle, donde ves sus cursos y comisiones.",
                },
            },
            {
                element: "th.sortable",
                popover: {
                    title: "Ordenar columnas",
                    description:
                        "Las columnas con flecha se pueden ordenar haciendo click en el encabezado.",
                },
            },
            {
                element: ".badge-success, .badge-danger",
                popover: {
                    title: "Estado del centro",
                    description:
                        "Activo / Inactivo. Los inactivos se conservan (soft delete) y se siguen viendo en el listado.",
                },
            },
            {
                element: ".action-buttons",
                popover: {
                    title: "Acciones por fila",
                    description:
                        "Ver (detalle), Editar y Eliminar. La eliminacion pide confirmacion y es un borrado logico.",
                },
            },
            {
                element: "#pagination-container",
                popover: {
                    title: "Paginacion",
                    description:
                        "Navegas entre paginas sin perder el filtro de busqueda actual.",
                },
            },
        ],

        centros_form: [
            {
                popover: {
                    title: "Alta / edicion de centro",
                    description:
                        "Completas los datos basicos del centro. Los campos marcados con * son obligatorios.",
                },
            },
            {
                element: "input[name='nombre'], #id_nombre",
                popover: {
                    title: "Nombre",
                    description:
                        "Como identificas el centro en todo el modulo. Tratá que sea unico y reconocible.",
                },
            },
            {
                element: "select[name='organizacion'], #id_organizacion",
                popover: {
                    title: "Organizacion",
                    description:
                        "Entidad responsable del centro. Se usa para reportes y permisos.",
                },
            },
            {
                element: "select[name='provincia'], #id_provincia, select[name='localidad'], #id_localidad",
                popover: {
                    title: "Ubicacion",
                    description:
                        "Provincia y localidad. La localidad se carga dinamicamente segun la provincia elegida.",
                },
            },
            {
                element: "input[name='calle'], #id_calle, input[name='telefono'], #id_telefono",
                popover: {
                    title: "Contacto",
                    description:
                        "Direccion y telefonos para contactar al centro.",
                },
            },
            {
                element: "form button[type='submit'], form input[type='submit']",
                popover: {
                    title: "Guardar",
                    description:
                        "Crea o actualiza el centro. Si hay errores de validacion, los vas a ver junto al campo correspondiente.",
                },
            },
        ],

        centros_detail: [
            {
                popover: {
                    title: "Detalle del centro",
                    description:
                        "Vista 360 del centro: datos generales, ubicaciones, contactos y toda la oferta educativa con sus comisiones. Te recorro cada sección.",
                },
            },
            {
                element: ".sisoc-title-row",
                popover: {
                    title: "Encabezado",
                    description:
                        "Nombre del centro, su <b>CUE</b> y un pill que indica si está <b>Activo</b> o <b>Inactivo</b>.",
                },
            },
            {
                element: ".sisoc-side-tabs--left",
                popover: {
                    title: "Pestañas laterales",
                    description:
                        "Cambias entre <b>Información general</b>, <b>Ubicaciones adicionales</b> y <b>Contactos adicionales</b>. La pestaña activa se resalta.",
                    side: "right",
                },
            },
            {
                element: ".sisoc-general-grid",
                onHighlightStarted: panelActivator("general"),
                popover: {
                    title: "Información general",
                    description:
                        "CUE, sector de gestión, domicilio principal, teléfono, celular y correo electrónico del centro.",
                },
            },
            {
                element: ".sisoc-map-preview",
                onHighlightStarted: panelActivator("general"),
                popover: {
                    title: "Mapa",
                    description:
                        "Si el centro tiene calle, localidad, municipio y provincia, se muestra su ubicación geográfica embebida.",
                    side: "left",
                },
            },
            {
                element: ".sisoc-referente-list",
                onHighlightStarted: panelActivator("general"),
                popover: {
                    title: "Referente del centro",
                    description:
                        "Datos del referente principal: nombre, teléfono, usuario del sistema asignado, DNI y correo. Es a quien contactás por el centro.",
                },
            },
            {
                element: "[data-sisoc-tab-target='ubicaciones']:not([hidden])",
                onHighlightStarted: panelActivator("general"),
                popover: {
                    title: "Ubicaciones adicionales",
                    description:
                        "Click acá para ver las sedes secundarias del centro (cuando dicta en más de una dirección).",
                    side: "right",
                },
            },
            {
                element: "[data-sisoc-panel='ubicaciones'] .sisoc-table, [data-sisoc-panel='ubicaciones'] .sisoc-empty-state",
                onHighlightStarted: panelActivator("ubicaciones"),
                popover: {
                    title: "Tabla de ubicaciones",
                    description:
                        "Columnas: <b>Nombre</b>, <b>Característica</b> (rol de la ubicación), <b>Localidad</b>, <b>Domicilio</b> y <b>Acciones</b>.",
                },
            },
            {
                element: "[data-sisoc-panel='ubicaciones'] .sisoc-btn--add",
                onHighlightStarted: panelActivator("ubicaciones"),
                popover: {
                    title: "Agregar sede",
                    description:
                        "Abre el modal para cargar una ubicación nueva con rol, localidad y domicilio.",
                    side: "left",
                },
            },
            {
                element: "[data-sisoc-panel='ubicaciones'] .sisoc-table-actions",
                onHighlightStarted: panelActivator("ubicaciones"),
                popover: {
                    title: "Acciones por ubicación",
                    description:
                        "<b>Editar</b> abre el modal con los datos de esa sede. <b>Borrar</b> la elimina del centro.",
                },
            },
            {
                element: "[data-sisoc-tab-target='contactos']:not([hidden])",
                onHighlightStarted: panelActivator("ubicaciones"),
                popover: {
                    title: "Contactos adicionales",
                    description:
                        "Listado de personas de contacto del centro además del referente principal.",
                    side: "right",
                },
            },
            {
                element: "[data-sisoc-panel='contactos'] .sisoc-table, [data-sisoc-panel='contactos'] .sisoc-empty-state",
                onHighlightStarted: panelActivator("contactos"),
                popover: {
                    title: "Tabla de contactos",
                    description:
                        "Columnas: <b>Nombre y apellido</b>, <b>Documento</b>, <b>Rol</b> (área/función), <b>Principal</b> (Sí/No), <b>Teléfono</b> y <b>Acciones</b>.",
                },
            },
            {
                element: "[data-sisoc-panel='contactos'] .sisoc-btn--add",
                onHighlightStarted: panelActivator("contactos"),
                popover: {
                    title: "Agregar contacto",
                    description:
                        "Abre el modal para cargar un contacto nuevo con sus datos y rol.",
                    side: "left",
                },
            },
            // -------- Oferta educativa (panel cargado por AJAX) --------
            {
                element: ".sisoc-section-header-bar",
                popover: {
                    title: "Oferta educativa",
                    description:
                        "Sección con los <b>cursos</b> del centro y, debajo, sus <b>comisiones</b>. Cada sección tiene su propio buscador y filtros.",
                },
            },
            {
                element: "#cursosFilterSearch",
                popover: {
                    title: "Buscar curso",
                    description:
                        "Filtrás en vivo por nombre del curso o plan curricular.",
                },
            },
            {
                element: "#cursosFilterEstado",
                popover: {
                    title: "Filtro por estado",
                    description:
                        "Mostrás solo cursos <b>Creados con comisión</b> o <b>Creados sin comisión</b> (los que todavía no tienen ninguna comisión cargada).",
                },
            },
            {
                element: ".sisoc-toolbar [data-bs-target='#modalCurso'][data-curso-mode='create']",
                popover: {
                    title: "Agregar curso",
                    description:
                        "Abre un modal para crear un curso nuevo eligiendo plan curricular, nombre, estado, si usa voucher y si tiene inscripción libre.",
                    side: "left",
                },
            },
            {
                element: "#tablaCursosCentro thead",
                popover: {
                    title: "Columnas de la tabla de cursos",
                    description:
                        "<b>Plan Curricular</b>, <b>Curso FP</b>, <b>Cant. de Comisiones</b>, <b>Estado</b> y <b>Acciones</b>. Cada fila representa un curso del centro.",
                },
            },
            {
                element: "#tablaCursosCentro .sisoc-data-badge",
                popover: {
                    title: "Badge de estado",
                    description:
                        "Dorado = <b>Creado con comisión</b>. Rojo = <b>Creado sin comisión</b> (falta darle al menos una comisión para poder inscribir).",
                },
            },
            {
                element: "#tablaCursosCentro .sisoc-table-actions",
                popover: {
                    title: "Acciones por curso",
                    description:
                        "<b>+ Comisión</b> lanza el wizard de 3 pasos para crear una comisión nueva de ese curso. <b>Editar</b> modifica los datos del curso. <b>Borrar</b> lo elimina.",
                },
            },
            // -------- Comisiones del centro --------
            {
                element: "#comisionesFilterSearch",
                popover: {
                    title: "Buscar comisión",
                    description:
                        "Filtrás por código o nombre de la comisión.",
                },
            },
            {
                element: "#comisionesFilterCurso",
                popover: {
                    title: "Filtrar por curso",
                    description:
                        "Mostrás solo las comisiones de un curso puntual. También podés hacer click en una fila de la tabla de cursos de arriba para autofiltrar.",
                },
            },
            {
                element: "#tablaComisionesCursoCentro thead",
                popover: {
                    title: "Columnas de comisiones",
                    description:
                        "<b>Curso</b>, <b>Comisión</b> (código), <b>Ubicación</b>, <b>Fecha Inicio</b>, <b>Fecha Fin</b>, <b>Cupo</b> y <b>Acciones</b>.",
                },
            },
            {
                element: "#tablaComisionesCursoCentro .sisoc-table-actions",
                popover: {
                    title: "Acciones por comisión",
                    description:
                        "<b>Ver</b> abre el detalle completo (horarios, nómina de inscriptos y sesiones para tomar asistencia). <b>Editar</b> abre el modal con cupo/fechas/ubicación. <b>Borrar</b> la elimina.",
                },
            },
            {
                element: "#comisionesFilterSummary",
                popover: {
                    title: "Resumen del listado",
                    description:
                        "Indica cuántas comisiones se están mostrando respecto al total, considerando los filtros aplicados.",
                },
            },
        ],

        // -------------------- OFERTA INSTITUCIONAL --------------------
        oferta_list: [
            {
                popover: {
                    title: "Ofertas institucionales",
                    description:
                        "Cada oferta vincula un centro con un plan curricular y un ciclo lectivo. Es el paso previo a crear comisiones.",
                },
            },
            {
                element: "#simple-search-form, #ajax-search-input",
                popover: {
                    title: "Buscar oferta",
                    description:
                        "Filtra por centro, plan de estudio o nombre.",
                },
            },
            {
                element: ".search-actions a.btn-primary",
                popover: {
                    title: "Nueva oferta",
                    description:
                        "Crea una oferta nueva eligiendo centro, plan curricular, ciclo y si usa voucher.",
                },
            },
            {
                element: "table.table thead",
                popover: {
                    title: "Columnas",
                    description:
                        "Centro, plan de estudio, ciclo, estado y si usa voucher. Centro y plan son ordenables.",
                },
            },
            {
                element: ".badge-validacion",
                popover: {
                    title: "Estado de la oferta",
                    description:
                        "Activa, cancelada, finalizada o pendiente. El estado define que se puede hacer con sus comisiones.",
                },
            },
            {
                element: ".action-buttons",
                popover: {
                    title: "Acciones por fila",
                    description:
                        "Ver detalle, editar o eliminar. Desde el detalle accedes a las comisiones de esa oferta.",
                },
            },
        ],

        oferta_form: [
            {
                popover: {
                    title: "Alta / edicion de oferta",
                    description:
                        "Definis la oferta academica: que centro la dicta, con que plan y en que ciclo lectivo.",
                },
            },
            {
                element: "select[name='centro'], #id_centro",
                popover: {
                    title: "Centro",
                    description:
                        "Sede donde se va a dictar. Solo aparecen centros activos.",
                },
            },
            {
                element: "select[name='plan_curricular'], #id_plan_curricular",
                popover: {
                    title: "Plan curricular",
                    description:
                        "Plan/version cargado en Catalogos. Define materias y carga horaria.",
                },
            },
            {
                element: "input[name='ciclo_lectivo'], #id_ciclo_lectivo, select[name='ciclo_lectivo']",
                popover: {
                    title: "Ciclo lectivo",
                    description:
                        "Año o periodo academico de la oferta.",
                },
            },
            {
                element: "select[name='estado'], #id_estado",
                popover: {
                    title: "Estado",
                    description:
                        "Activa, pendiente, cancelada o finalizada. Solo las activas admiten nuevas inscripciones.",
                },
            },
            {
                element: "input[name='usa_voucher'], #id_usa_voucher",
                popover: {
                    title: "Voucher",
                    description:
                        "Si la oferta usa voucher, podes configurar la parametria y asignar vouchers desde el modulo Vouchers.",
                },
            },
            {
                element: "form button[type='submit'], form input[type='submit']",
                popover: {
                    title: "Guardar",
                    description: "Confirma los datos para crear o actualizar la oferta.",
                },
            },
        ],

        // -------------------- COMISIONES --------------------
        comision_list: [
            {
                popover: {
                    title: "Comisiones",
                    description:
                        "Una comision es la instancia concreta de una oferta: tiene fechas, cupo, horarios y genera las sesiones donde se toma asistencia.",
                },
            },
            {
                element: "#simple-search-form, #ajax-search-input",
                popover: {
                    title: "Buscar comision",
                    description: "Filtra por codigo, nombre u oferta asociada.",
                },
            },
            {
                element: ".search-actions a.btn-primary",
                popover: {
                    title: "Nueva comision",
                    description:
                        "Crea una comision suelta. Para alta guiada (con horarios y nomina) usa el wizard desde el panel del centro.",
                },
            },
            {
                element: "th[data-column='codigo'], th[data-column='nombre']",
                popover: {
                    title: "Codigo y nombre",
                    description:
                        "Codigo unico de la comision y un nombre descriptivo opcional. Ambos son ordenables.",
                },
            },
            {
                element: "table.table thead tr th:nth-child(4), table.table thead tr th:nth-child(5)",
                popover: {
                    title: "Fechas y cupo",
                    description:
                        "Fecha de inicio, fecha de fin y cupo maximo. Si se llena el cupo, las nuevas inscripciones van a lista de espera.",
                },
            },
            {
                element: ".badge-validacion",
                popover: {
                    title: "Estado",
                    description:
                        "Activa, cancelada, finalizada o pendiente. Una comision finalizada ya no acepta cambios de asistencia.",
                },
            },
            {
                element: ".action-buttons",
                popover: {
                    title: "Acciones",
                    description:
                        "Desde el detalle de la comision ves horarios, nomina de inscriptos y accedes a las sesiones para tomar asistencia.",
                },
            },
        ],

        // -------------------- INSCRIPCIONES A OFERTA --------------------
        inscripcion_oferta_list: [
            {
                popover: {
                    title: "Inscripciones a oferta",
                    description:
                        "Listado de personas inscriptas a las distintas ofertas institucionales. Desde aca cargas nuevas inscripciones.",
                },
            },
            {
                element: "#simple-search-form, #ajax-search-input",
                popover: {
                    title: "Buscar",
                    description: "Filtra por persona, documento u oferta.",
                },
            },
            {
                element: ".search-actions a.btn-primary",
                popover: {
                    title: "Nueva inscripcion",
                    description:
                        "Inscribi a una persona a una oferta. Si la oferta tiene comisiones, podes asignarla en el mismo paso.",
                },
            },
            {
                element: "table.table",
                popover: {
                    title: "Listado",
                    description:
                        "Cada fila muestra persona, oferta y estado. Desde las acciones podes ver el detalle o cambiar el estado.",
                },
            },
            {
                element: ".action-buttons",
                popover: {
                    title: "Acciones",
                    description:
                        "Ver, editar o eliminar. Para mover entre 'inscripto', 'lista de espera' o 'dado de baja' usa el detalle.",
                },
            },
        ],

        inscripcion_oferta_form: [
            {
                popover: {
                    title: "Nueva inscripcion",
                    description:
                        "Vinculas a una persona con una oferta institucional. El sistema valida cupo, sexo permitido y si ya estaba inscripta.",
                },
            },
            {
                element: "select[name='persona'], #id_persona, input[name='persona']",
                popover: {
                    title: "Persona",
                    description:
                        "Buscas la persona por nombre o documento. Si no existe, primero hay que darla de alta.",
                },
            },
            {
                element: "select[name='oferta'], #id_oferta, select[name='oferta_institucional'], #id_oferta_institucional",
                popover: {
                    title: "Oferta",
                    description:
                        "Solo aparecen ofertas activas. Si la oferta esta cerrada, no admite nuevas inscripciones.",
                },
            },
            {
                element: "select[name='comision'], #id_comision",
                popover: {
                    title: "Comision (opcional)",
                    description:
                        "Si seleccionas una comision puntual, la persona queda inscripta directamente a esa comision.",
                },
            },
            {
                element: "form button[type='submit'], form input[type='submit']",
                popover: {
                    title: "Guardar",
                    description:
                        "Si todo esta correcto, queda inscripta. Si el cupo esta lleno, va a lista de espera automaticamente.",
                },
            },
        ],

        // -------------------- ASISTENCIA --------------------
        asistencia: [
            {
                popover: {
                    title: "Asistencia de la sesión",
                    description:
                        "Pantalla para registrar quién estuvo presente y quién ausente en esta sesión de la comisión.",
                },
            },
            {
                element: ".asis-title-row",
                popover: {
                    title: "Datos de la sesión",
                    description:
                        "Comisión, día y fecha de la clase que estás registrando, y el estado de la comisión. Verificá antes de guardar.",
                },
            },
            {
                element: ".asis-metric-grid",
                popover: {
                    title: "Resumen en vivo",
                    description:
                        "Contadores de <b>presentes</b>, <b>ausentes</b> y <b>sin marcar</b>. Se actualizan a medida que marcás cada fila.",
                },
            },
            {
                element: ".asis-tbl",
                popover: {
                    title: "Nómina",
                    description:
                        "Cada fila es un inscripto aceptado de la comisión, con su apellido y nombre.",
                },
            },
            {
                element: ".asis-row .asis-mark",
                popover: {
                    title: "Marcar Presente / Ausente",
                    description:
                        "Por cada persona marcás <b>Presente</b> o <b>Ausente</b>. Son opciones excluyentes: al elegir una se desmarca la otra.",
                },
            },
            {
                element: ".asis-mark-all",
                popover: {
                    title: "Marcar todos",
                    description:
                        "Los recuadros del encabezado marcan a <b>todos</b> los inscriptos como presentes o como ausentes de una sola vez.",
                    side: "left",
                },
            },
            {
                element: ".asis-save",
                popover: {
                    title: "Guardar asistencia",
                    description:
                        "Guarda la asistencia de toda la sesión. Podés volver a editarla mientras la comisión no esté finalizada.",
                    side: "left",
                },
            },
        ],

        // -------------------- WIZARD DE COMISION DE CURSO --------------------
        curso_wizard: [
            {
                popover: {
                    title: "Wizard de comision",
                    description:
                        "Alta guiada en 3 pasos: datos basicos, horarios y confirmacion. Es la forma recomendada de crear una comision con su esquema completo.",
                },
            },
            {
                element: ".bs-stepper-header, .stepper, [data-step]",
                popover: {
                    title: "Pasos",
                    description:
                        "Los pasos se completan en orden. Podes volver atras sin perder lo cargado.",
                },
            },
            {
                element: "input[name*='nombre'], input[name*='codigo'], select[name*='oferta']",
                popover: {
                    title: "Paso 1: datos basicos",
                    description:
                        "Oferta, codigo, nombre, fechas y cupo. Estos datos identifican la comision.",
                },
            },
            {
                element: "[data-horario], .horario-row, fieldset:has(select[name*='dia'])",
                popover: {
                    title: "Paso 2: horarios",
                    description:
                        "Sumas dia, horario y aula. Cada bloque horario genera sesiones automaticamente entre las fechas de la comision.",
                },
            },
            {
                element: ".step-3, [data-step='3'], .resumen",
                popover: {
                    title: "Paso 3: confirmacion",
                    description:
                        "Revisas todo lo cargado y confirmas. A partir de ahi la comision queda lista para inscripciones y asistencia.",
                },
            },
        ],

        // -------------------- PANEL DE CURSOS DEL CENTRO --------------------
        centros_cursos_panel: [
            {
                popover: {
                    title: "Cursos del centro",
                    description:
                        "Panel con todos los cursos y comisiones asociados a este centro. Punto de entrada operativo.",
                },
            },
            {
                element: "a[href*='/comision/nueva/'], a[href*='wizard']",
                popover: {
                    title: "Nueva comision (wizard)",
                    description:
                        "Lanza el alta guiada en 3 pasos: datos, horarios y confirmacion.",
                },
            },
            {
                element: "table.table, .list-group",
                popover: {
                    title: "Comisiones existentes",
                    description:
                        "Lista las comisiones del centro con su estado. Desde cada fila accedes a detalle, inscriptos y sesiones.",
                },
            },
        ],

        // ---------- REPORTE DE INSCRIPCIONES Y ASISTENCIA ----------
        reporte_inscripciones: [
            {
                popover: {
                    title: "Reporte de inscripciones y asistencia",
                    description:
                        "Vista consolidada de inscripciones y asistencia. Elegís el alcance y cómo ver los totales, filtrás lo que necesites y podés exportar. Te muestro todo.",
                },
            },
            {
                element: ".rep-title-row",
                popover: {
                    title: "Nivel del reporte",
                    description:
                        "El pill <b>Nivel</b> indica el alcance del corte: <b>Centro</b>, <b>Provincia</b> o <b>INET (global)</b>. Se controla desde el filtro \"Nivel\".",
                    side: "bottom",
                },
            },
            {
                element: ".rep-filter-toolbar",
                popover: {
                    title: "Filtros dinámicos",
                    description:
                        "Arrancás solo con <b>Nivel</b> y <b>Agrupar por</b>. Los demás filtros no aparecen hasta que los agregás, así la pantalla no se llena de campos.",
                },
            },
            {
                element: "#repAddFilter",
                popover: {
                    title: "Agregar un filtro",
                    description:
                        "Elegí un filtro de la lista (provincia, centro, curso, comisión, fechas, estado, voucher, etc.) y aparece abajo listo para usar. Cada filtro agregado se quita con la <b>×</b>.",
                    side: "right",
                },
            },
            {
                element: "#id_nivel",
                popover: {
                    title: "Nivel",
                    description:
                        "Define el alcance del reporte: <b>Centro</b>, <b>Provincia</b> o <b>INET (global)</b>. Acota qué universo de datos entra.",
                },
            },
            {
                element: "#id_group_by",
                popover: {
                    title: "Agrupar por",
                    description:
                        "Define <b>cómo se consolidan las filas</b> del resumen: una fila por <b>centro</b>, <b>provincia</b>, <b>curso/oferta</b>, <b>comisión</b> o <b>mes</b>. No filtra: solo cambia el desglose.",
                },
            },
            {
                element: ".rep-filter-actions",
                popover: {
                    title: "Aplicar, limpiar y exportar resumen",
                    description:
                        "<b>Aplicar filtros</b> recalcula el reporte. <b>Limpiar</b> vuelve al estado inicial. <b>Resumen CSV/Excel</b> exportan la tabla agrupada (una fila por grupo).",
                },
            },
            {
                element: ".rep-metric-grid",
                popover: {
                    title: "Métricas del corte",
                    description:
                        "Totales de lo filtrado: <b>inscriptos</b>, <b>presentes</b>, <b>ausentes</b> y <b>% de asistencia</b> (sobre presentes + ausentes).",
                },
            },
            {
                element: "#reporteResumenTabla",
                popover: {
                    title: "Resumen por grupo",
                    description:
                        "Una fila por grupo (según \"Agrupar por\") con todas las columnas de inscripción y asistencia. El título y la primera columna se renombran según el agrupador elegido.",
                },
            },
            {
                element: "#reporteQuickSearch",
                popover: {
                    title: "Buscar en esta página",
                    description:
                        "Filtra <b>en vivo</b> las filas visibles del resumen, sin recargar. Actúa solo sobre lo que ya está en pantalla, no sobre toda la base.",
                },
            },
            {
                element: "#repDetalleTabla",
                popover: {
                    title: "Personas inscriptas (detalle)",
                    description:
                        "La nómina real, persona por persona. En pantalla se muestran hasta 250 filas como muestra.",
                },
            },
            {
                element: ".rep-detalle-export",
                popover: {
                    title: "Exportar el detalle completo",
                    description:
                        "<b>Detalle CSV/Excel</b> bajan <b>todas</b> las personas (sin el tope de 250 de la pantalla), respetando los filtros aplicados.",
                    side: "left",
                },
            },
            {
                element: '[data-vat-tour="help-button"]',
                popover: {
                    title: "Volver a ver el tour",
                    description:
                        "Desde el botón <b>Tour de ayuda</b> podés relanzar este recorrido cuando quieras.",
                    side: "left",
                },
            },
        ],
    };

    // ------------------------- Deteccion de seccion -------------------------

    function detectSection() {
        var injected = window.SISOC_VAT_TOUR && window.SISOC_VAT_TOUR.section;
        if (injected && sectionSteps[injected]) return injected;

        var p = window.location.pathname;
        if (/\/vat\/centros\/\d+\/panel\/cursos\/?$/.test(p)) return "centros_cursos_panel";
        if (/\/vat\/centros\/(nuevo|\d+\/editar)\/?$/.test(p)) return "centros_form";
        if (/\/vat\/centros\/\d+\/?$/.test(p)) return "centros_detail";
        if (/\/vat\/centros\/?$/.test(p)) return "centros_list";
        if (/\/vat\/ofertas-institucionales\/(nueva|\d+\/editar)\/?$/.test(p)) return "oferta_form";
        if (/\/vat\/ofertas-institucionales\/?$/.test(p)) return "oferta_list";
        if (/\/vat\/comisiones\/?$/.test(p)) return "comision_list";
        if (/\/vat\/inscripciones-oferta\/(nueva|\d+\/editar)\/?$/.test(p)) return "inscripcion_oferta_form";
        if (/\/vat\/inscripciones-oferta\/?$/.test(p)) return "inscripcion_oferta_list";
        if (/\/asistencia\/?$/.test(p)) return "asistencia";
        if (/\/vat\/cursos\/.+\/comision\//.test(p)) return "curso_wizard";
        if (/\/vat\/reportes\/inscripciones-asistencias\/?$/.test(p)) return "reporte_inscripciones";
        return null;
    }

    // ------------------------------ API publica ------------------------------

    // Para secciones cuyos contenidos se cargan por AJAX, esperamos a que
    // aparezca un elemento de referencia antes de lanzar el tour.
    var SECTION_WAIT_FOR = {
        centros_detail: { selector: "[data-panel-rendered]", timeoutMs: 4000 },
    };

    var SisocVatTour = {
        runGeneral: function () {
            runDriver(generalSteps);
            safeSet(GENERAL_KEY, "1");
        },
        runSection: function (name) {
            var key = name || detectSection();
            if (!key || !sectionSteps[key]) {
                this.runGeneral();
                return;
            }
            var wait = SECTION_WAIT_FOR[key];
            var launch = function () {
                runDriver(sectionSteps[key]);
                safeSet(SECTION_KEY_PREFIX + key, "1");
            };
            if (wait) {
                waitForElement(wait.selector, wait.timeoutMs).then(launch);
            } else {
                launch();
            }
        },
        currentSection: detectSection,
        resetSeen: function () {
            safeRemove(GENERAL_KEY);
            Object.keys(sectionSteps).forEach(function (k) {
                safeRemove(SECTION_KEY_PREFIX + k);
            });
        },
    };

    window.SisocVatTour = SisocVatTour;

    // --------------------------- Auto-launch ---------------------------
    // Deshabilitado a proposito: el tour NO se inicia solo. Se lanza unica y
    // exclusivamente cuando el usuario abre el boton "Tour de ayuda" y elige
    // "Tour de esta pantalla" o "Tour general". Antes se auto-lanzaba en la
    // primera visita de cada seccion (y el general al entrar a /vat/centros/),
    // lo cual resultaba molesto. La API publica (SisocVatTour) y el control de
    // "tours vistos" se conservan intactos para los disparadores manuales.
})();
