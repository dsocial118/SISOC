/**
 * Secciones colapsables del formulario de Informe Técnico.
 *
 * Se usa tanto en la página completa (informe_tecnico_form.html) como en la
 * sección inline de admisiones_tecnicos_form.html. Cada bloque es un
 * `.card-body.collapse[data-informe-seccion]` con su botón toggle en el
 * `.card-header`.
 *
 * Responsabilidades:
 *  - abrir automáticamente las secciones que traen errores del servidor;
 *  - rotar el chevron según el estado de cada sección;
 *  - desplegar todas las secciones antes de enviar el formulario, para que el
 *    navegador pueda enfocar un campo obligatorio vacío que esté oculto.
 */
document.addEventListener("DOMContentLoaded", function () {
    const SELECTOR_SECCION = ".collapse[data-informe-seccion]";
    const SELECTOR_ERROR = [
        ".is-invalid",
        ".invalid-feedback",
        ".alert-danger",
        ".border-danger",
        ".errorlist",
        "ul.errorlist",
    ].join(",");

    const secciones = Array.prototype.slice.call(
        document.querySelectorAll(SELECTOR_SECCION)
    );

    if (!secciones.length) {
        return;
    }

    function toggleDeSeccion(seccion) {
        return document.querySelector('[data-bs-target="#' + seccion.id + '"]');
    }

    function marcarToggle(seccion, expandida) {
        const toggle = toggleDeSeccion(seccion);
        if (!toggle) {
            return;
        }
        toggle.setAttribute("aria-expanded", expandida ? "true" : "false");
        toggle.classList.toggle("collapsed", !expandida);
    }

    function abrir(seccion) {
        seccion.classList.add("show");
        marcarToggle(seccion, true);
    }

    // Secciones con errores: quedan visibles al cargar la página.
    secciones.forEach(function (seccion) {
        if (seccion.querySelector(SELECTOR_ERROR)) {
            abrir(seccion);
        }
        seccion.addEventListener("shown.bs.collapse", function () {
            marcarToggle(seccion, true);
        });
        seccion.addEventListener("hidden.bs.collapse", function () {
            marcarToggle(seccion, false);
        });
    });

    // Al pulsar un botón de envío hay que desplegar todo ANTES de que corra la
    // validación del navegador: un campo obligatorio oculto no es enfocable y
    // el submit se cancelaría sin explicar por qué. El evento `submit` llega
    // demasiado tarde (solo se dispara si la validación pasó), así que se
    // engancha el `click` en fase de captura.
    const formularios = new Set();
    secciones.forEach(function (seccion) {
        const formulario = seccion.closest("form");
        if (formulario) {
            formularios.add(formulario);
        }
    });

    formularios.forEach(function (formulario) {
        function desplegarTodo() {
            secciones.forEach(function (seccion) {
                if (formulario.contains(seccion)) {
                    abrir(seccion);
                }
            });
        }

        formulario.addEventListener(
            "click",
            function (evento) {
                const boton = evento.target.closest(
                    'button[type="submit"], input[type="submit"]'
                );
                if (boton && formulario.contains(boton)) {
                    desplegarTodo();
                }
            },
            true
        );
        formulario.addEventListener("submit", desplegarTodo);
    });
});
