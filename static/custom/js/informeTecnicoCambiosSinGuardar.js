/**
 * Aviso de cambios sin guardar en el formulario de Informe Técnico.
 *
 * Se aplica a `form[data-avisar-cambios-sin-guardar]`, tanto en la página
 * completa (informe_tecnico_form.html) como en la sección inline de
 * admisiones_tecnicos_form.html.
 *
 * Dos caminos, porque el navegador no permite el mismo trato en los dos:
 *
 *  - Click en un enlace que saca de la página: se intercepta y se muestra el
 *    modal `#modalCambiosSinGuardar`, que sí puede ofrecer "Guardar borrador".
 *  - Cerrar la pestaña, recargar o el botón atrás: solo se puede usar
 *    `beforeunload`, cuyo cartel lo dibuja el navegador y no admite un botón
 *    de guardado. Queda como red de seguridad.
 *
 * Para decidir si hay edición pendiente se piden dos condiciones: que el
 * usuario haya tocado el formulario (evento `isTrusted`) y que además algún
 * valor difiera del que tenía al cargar. La primera condición es la que evita
 * falsos positivos de los scripts que escriben campos por su cuenta —
 * `geografiaProvinciaLocalidad.js` repuebla el select de localidad al cargar y
 * la réplica del número de GDE escribe en el input del informe—, porque
 * asignar `value` por código no dispara eventos.
 */
(function (window, document) {
    const SELECTOR_FORM = "form[data-avisar-cambios-sin-guardar]";
    const IGNORAR = new Set(["csrfmiddlewaretoken"]);

    function valorDeCampo(campo) {
        if (campo.type === "checkbox" || campo.type === "radio") {
            return campo.checked ? "1" : "0";
        }
        if (campo.type === "file") {
            return Array.prototype.map
                .call(campo.files || [], (archivo) => archivo.name)
                .join("|");
        }
        if (campo.multiple && campo.options) {
            return Array.prototype.filter
                .call(campo.options, (opcion) => opcion.selected)
                .map((opcion) => opcion.value)
                .join("|");
        }
        return campo.value;
    }

    function camposDe(form) {
        return Array.prototype.filter.call(
            form.elements,
            (campo) => campo.name && !IGNORAR.has(campo.name)
        );
    }

    function tomarEstado(form) {
        const estado = new Map();
        camposDe(form).forEach((campo) => estado.set(campo, valorDeCampo(campo)));
        return estado;
    }

    function crearVigilante(form) {
        let referencia = tomarEstado(form);
        let interactuo = false;
        let enviando = false;

        function registrarInteraccion(evento) {
            if (evento.isTrusted) interactuo = true;
        }
        form.addEventListener("input", registrarInteraccion);
        form.addEventListener("change", registrarInteraccion);

        form.addEventListener("submit", function () {
            enviando = true;
        });

        // Si el envío no llegó a concretarse (validación del navegador, o el
        // usuario volvió con el botón atrás), el aviso vuelve a estar activo.
        window.addEventListener("pageshow", function () {
            enviando = false;
        });

        return {
            form,
            estaSucio: function () {
                if (enviando || !interactuo) return false;
                return camposDe(form).some(
                    (campo) => referencia.get(campo) !== valorDeCampo(campo)
                );
            },
            rebase: function () {
                referencia = tomarEstado(form);
                interactuo = false;
            },
        };
    }

    function esNavegacionExterna(enlace) {
        if (!enlace || !enlace.getAttribute) return false;
        const href = enlace.getAttribute("href");
        if (!href || href.startsWith("#")) return false;
        if (href.startsWith("javascript:")) return false;
        if (enlace.target && enlace.target !== "_self") return false;
        if (enlace.hasAttribute("download")) return false;
        if (enlace.dataset.bsToggle) return false;
        return true;
    }

    document.addEventListener("DOMContentLoaded", function () {
        const forms = Array.prototype.slice.call(
            document.querySelectorAll(SELECTOR_FORM)
        );
        if (!forms.length) {
            return;
        }

        const vigilantes = forms.map(crearVigilante);
        const hayCambios = () => vigilantes.some((v) => v.estaSucio());
        const rebasarTodo = () => vigilantes.forEach((v) => v.rebase());

        window.informeTecnicoCambios = { hayCambios, rebasar: rebasarTodo };

        // Red de seguridad: cerrar pestaña, recargar o botón atrás. El texto lo
        // decide el navegador; no se puede ofrecer un botón de guardado acá.
        window.addEventListener("beforeunload", function (evento) {
            if (!hayCambios()) return;
            evento.preventDefault();
            evento.returnValue = "";
            return "";
        });

        const modalElemento = document.getElementById("modalCambiosSinGuardar");
        if (!modalElemento || !window.bootstrap) {
            return;
        }
        const modal = new bootstrap.Modal(modalElemento);
        let destinoPendiente = null;

        document.addEventListener(
            "click",
            function (evento) {
                if (evento.defaultPrevented || evento.button !== 0) return;
                if (evento.metaKey || evento.ctrlKey || evento.shiftKey) return;
                const enlace = evento.target.closest("a[href]");
                if (!esNavegacionExterna(enlace) || !hayCambios()) return;

                evento.preventDefault();
                destinoPendiente = enlace.href;
                modal.show();
            },
            true
        );

        modalElemento.addEventListener("click", function (evento) {
            const boton = evento.target.closest("[data-accion]");
            if (!boton) return;

            if (boton.dataset.accion === "salir") {
                const destino = destinoPendiente;
                destinoPendiente = null;
                rebasarTodo();
                modal.hide();
                if (destino) window.location.href = destino;
                return;
            }

            if (boton.dataset.accion === "guardar") {
                destinoPendiente = null;
                modal.hide();
                const vigilante =
                    vigilantes.find((v) => v.estaSucio()) || vigilantes[0];
                const borrador = vigilante.form.querySelector(
                    '[type="submit"][name="action"][value="draft"]'
                );
                if (borrador) {
                    borrador.click();
                } else {
                    vigilante.form.submit();
                }
            }
        });
    });
})(window, document);
