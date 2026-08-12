/**
 * Afordancia de scroll horizontal en las tablas de listados.
 *
 * Estos listados usan columnas configurables y llegan a 9-12 columnas; en
 * pantallas de 1280px la tabla scrollea, pero nada lo indica y se lee como si
 * estuviera cortada.
 *
 * Agrega dos clases al contenedor scrolleable:
 *   .poncho-scroll--der  hay contenido a la derecha
 *   .poncho-scroll--izq  hay contenido a la izquierda (ya se scrolleo)
 *
 * El CSS dibuja una sombra en el borde correspondiente. Hace falta JS porque
 * CSS no puede detectar si un contenedor desborda.
 */
(function () {
    'use strict';

    // Incluye .card-body porque hay listados sin envoltorio .table-responsive:
    // la tabla cuelga directo de la card. Se filtran los paneles sin tabla.
    var SELECTOR = '.table-responsive, .table-responsive-lg, .card-body';
    var MARGEN = 2; // tolerancia en px para redondeos del navegador

    function actualizar(contenedor) {
        var desborda = contenedor.scrollWidth - contenedor.clientWidth > MARGEN;
        var pos = contenedor.scrollLeft;

        contenedor.classList.toggle('poncho-scroll--izq', desborda && pos > MARGEN);
        contenedor.classList.toggle(
            'poncho-scroll--der',
            desborda && pos + contenedor.clientWidth < contenedor.scrollWidth - MARGEN
        );
    }

    function esContenedorTabla(contenedor) {
        return !contenedor.classList.contains('card-body') ||
            Boolean(contenedor.querySelector('table, .projects'));
    }

    function preparar() {
        // Solo en listados con el buscador nuevo, para no alterar otras vistas
        if (!document.querySelector('.poncho-search')) {
            return;
        }

        var contenedores = document.querySelectorAll(SELECTOR);
        Array.prototype.forEach.call(contenedores, function (contenedor) {
            if (!esContenedorTabla(contenedor)) {
                return;
            }
            if (contenedor.dataset.ponchoScroll === 'listo') {
                return;
            }
            contenedor.dataset.ponchoScroll = 'listo';
            contenedor.classList.add('poncho-scroll');

            actualizar(contenedor);
            contenedor.addEventListener('scroll', function () {
                actualizar(contenedor);
            }, { passive: true });

            // El ancho cambia al configurar columnas o al redimensionar
            if (typeof ResizeObserver === 'function') {
                new ResizeObserver(function () {
                    actualizar(contenedor);
                }).observe(contenedor);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', preparar);
    } else {
        preparar();
    }

    window.addEventListener('resize', function () {
        var contenedores = document.querySelectorAll(SELECTOR);
        Array.prototype.forEach.call(contenedores, function (contenedor) {
            if (esContenedorTabla(contenedor)) {
                actualizar(contenedor);
            }
        });
    });
})();
