/**
 * "Volver" unificado del sistema (issue #2460).
 *
 * El requisito no es solo estetico: al volver tienen que seguir aplicados los
 * filtros de la pantalla anterior. Por eso no alcanza con un href fijo al
 * listado (perderia la querystring) ni con history.back() a secas (se rompe
 * despues de un POST-redirect-GET, que deja una entrada intermedia).
 *
 * Solucion: se mantiene una pila de URLs visitadas en sessionStorage, con
 * path + querystring. "Volver" navega a la anterior distinta de la actual, asi
 * que vuelve al listado tal como estaba filtrado. Si no hay historial (entrada
 * directa, pestaña nueva) cae al fallback que declara la pantalla y, si tampoco
 * hay, al referrer o a history.back().
 */
(function (window, document) {
    "use strict";

    var CLAVE_PILA = "sisocNavStack";
    var MAX_ENTRADAS = 25;

    function urlActual() {
        return window.location.pathname + window.location.search;
    }

    function leerPila() {
        try {
            var crudo = window.sessionStorage.getItem(CLAVE_PILA);
            var pila = crudo ? JSON.parse(crudo) : [];
            return Array.isArray(pila) ? pila : [];
        } catch (error) {
            return [];
        }
    }

    function guardarPila(pila) {
        try {
            window.sessionStorage.setItem(CLAVE_PILA, JSON.stringify(pila));
        } catch (error) {
            // Navegacion privada o storage lleno: el boton sigue andando por fallback.
        }
    }

    /**
     * Registra la pantalla actual.
     *
     * - Si repite la ultima entrada (F5, o POST que re-renderiza la misma URL)
     *   no se apila de nuevo.
     * - Si coincide con la anteultima, se interpreta como "el usuario volvio" y
     *   se desapila, para que la pila no crezca en zigzag.
     */
    function registrarVisita() {
        var actual = urlActual();
        var pila = leerPila();

        if (pila.length && pila[pila.length - 1] === actual) {
            return pila;
        }
        if (pila.length > 1 && pila[pila.length - 2] === actual) {
            pila.pop();
            guardarPila(pila);
            return pila;
        }

        pila.push(actual);
        if (pila.length > MAX_ENTRADAS) {
            pila = pila.slice(pila.length - MAX_ENTRADAS);
        }
        guardarPila(pila);
        return pila;
    }

    /** URL anterior distinta de la actual, o null. */
    function destinoPrevio() {
        var pila = leerPila();
        var actual = urlActual();
        for (var i = pila.length - 1; i >= 0; i--) {
            if (pila[i] !== actual) {
                return pila[i];
            }
        }
        return null;
    }

    /** El referrer solo sirve si es del mismo origen. */
    function referrerInterno() {
        if (!document.referrer) return null;
        try {
            var referrer = new URL(document.referrer);
            if (referrer.origin !== window.location.origin) return null;
            var destino = referrer.pathname + referrer.search;
            return destino === urlActual() ? null : destino;
        } catch (error) {
            return null;
        }
    }

    function resolverDestino(boton) {
        return (
            destinoPrevio() ||
            referrerInterno() ||
            boton.dataset.volverFallback ||
            null
        );
    }

    function conectar(boton) {
        var destino = resolverDestino(boton);
        if (destino) {
            boton.setAttribute("href", destino);
            return;
        }
        // Sin destino conocido: ultimo recurso, el historial del navegador.
        boton.setAttribute("href", "#");
        boton.addEventListener("click", function (evento) {
            evento.preventDefault();
            if (window.history.length > 1) {
                window.history.back();
            } else {
                window.location.href = "/";
            }
        });
    }

    registrarVisita();

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll("[data-sisoc-volver]").forEach(conectar);
    });

    // Expuesto para tests manuales y para pantallas que reconstruyen el boton.
    window.SisocVolver = {
        registrarVisita: registrarVisita,
        destinoPrevio: destinoPrevio,
        conectar: conectar,
    };
})(window, document);
