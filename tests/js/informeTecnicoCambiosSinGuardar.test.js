/**
 * Detección de cambios sin guardar del Informe Técnico.
 *
 * Se ejercita la lógica que decide si hay edición pendiente, que es la que
 * puede dar falsos positivos: pide interacción real del usuario (`isTrusted`)
 * además de un valor distinto al de carga.
 *
 * Correr con:  node tests/js/informeTecnicoCambiosSinGuardar.test.js
 */

function crearCampo(nombre, valor, extra = {}) {
    return Object.assign({ name: nombre, value: valor, type: "text" }, extra);
}

function crearForm(campos) {
    const oyentes = {};
    return {
        elements: campos,
        dataset: {},
        addEventListener(tipo, fn) {
            (oyentes[tipo] = oyentes[tipo] || []).push(fn);
        },
        querySelector() {
            return null;
        },
        emitir(tipo, evento) {
            (oyentes[tipo] || []).forEach((fn) => fn(evento));
        },
    };
}

function montar(form) {
    const oyentesDocumento = {};
    const oyentesVentana = {};

    global.document = {
        addEventListener(tipo, fn) {
            (oyentesDocumento[tipo] = oyentesDocumento[tipo] || []).push(fn);
        },
        querySelectorAll(selector) {
            return selector.includes("avisar-cambios-sin-guardar") ? [form] : [];
        },
        getElementById() {
            return null; // sin modal: se ejercita solo la detección
        },
    };
    global.window = {
        addEventListener(tipo, fn) {
            (oyentesVentana[tipo] = oyentesVentana[tipo] || []).push(fn);
        },
        // bootstrap ausente a propósito
    };

    delete require.cache[
        require.resolve("../../static/custom/js/informeTecnicoCambiosSinGuardar.js")
    ];
    require("../../static/custom/js/informeTecnicoCambiosSinGuardar.js");

    (oyentesDocumento.DOMContentLoaded || []).forEach((fn) => fn());
    return {
        api: () => global.window.informeTecnicoCambios,
        beforeunload: (evento) =>
            (oyentesVentana.beforeunload || []).forEach((fn) => fn(evento)),
        pageshow: () => (oyentesVentana.pageshow || []).forEach((fn) => fn()),
    };
}

function afirmar(condicion, mensaje) {
    if (!condicion) throw new Error(mensaje);
}

// --- Al cargar no hay cambios ---------------------------------------------
{
    const campo = crearCampo("nota_gde_if", "IF-1");
    const form = crearForm([campo]);
    const ctx = montar(form);
    afirmar(ctx.api().hayCambios() === false, "recién cargado no debe estar sucio");
}

// --- Un cambio por código no cuenta como edición del usuario ---------------
{
    const campo = crearCampo("nota_gde_if", "IF-1");
    const form = crearForm([campo]);
    const ctx = montar(form);
    campo.value = "IF-SINCRONIZADO-POR-AJAX";
    afirmar(
        ctx.api().hayCambios() === false,
        "asignar value por código no debe marcar cambios pendientes"
    );
}

// --- Un evento no confiable tampoco --------------------------------------
{
    const campo = crearCampo("nota_gde_if", "IF-1");
    const form = crearForm([campo]);
    const ctx = montar(form);
    campo.value = "otro";
    form.emitir("input", { isTrusted: false });
    afirmar(
        ctx.api().hayCambios() === false,
        "un evento sintético no debe marcar cambios pendientes"
    );
}

// --- Edición real del usuario sí cuenta -----------------------------------
{
    const campo = crearCampo("nota_gde_if", "IF-1");
    const form = crearForm([campo]);
    const ctx = montar(form);
    campo.value = "editado a mano";
    form.emitir("input", { isTrusted: true });
    afirmar(ctx.api().hayCambios() === true, "una edición real debe marcar cambios");
}

// --- Volver al valor original deja de estar sucio -------------------------
{
    const campo = crearCampo("nota_gde_if", "IF-1");
    const form = crearForm([campo]);
    const ctx = montar(form);
    campo.value = "editado";
    form.emitir("input", { isTrusted: true });
    campo.value = "IF-1";
    afirmar(
        ctx.api().hayCambios() === false,
        "deshacer la edición no debe seguir marcando cambios"
    );
}

// --- Al enviar el formulario no se avisa ----------------------------------
{
    const campo = crearCampo("nota_gde_if", "IF-1");
    const form = crearForm([campo]);
    const ctx = montar(form);
    campo.value = "editado";
    form.emitir("input", { isTrusted: true });
    form.emitir("submit", {});
    afirmar(
        ctx.api().hayCambios() === false,
        "durante el envío no debe avisar de cambios"
    );
    ctx.pageshow();
    afirmar(
        ctx.api().hayCambios() === true,
        "si el envío no se concretó, el aviso debe volver"
    );
}

// --- El csrf no cuenta como cambio ---------------------------------------
{
    const csrf = crearCampo("csrfmiddlewaretoken", "abc");
    const form = crearForm([csrf]);
    const ctx = montar(form);
    csrf.value = "token-rotado";
    form.emitir("input", { isTrusted: true });
    afirmar(ctx.api().hayCambios() === false, "el csrf no debe contar como cambio");
}

// --- Checkbox y select multiple ------------------------------------------
{
    const check = crearCampo("no_corresponde", "", { type: "checkbox", checked: false });
    const form = crearForm([check]);
    const ctx = montar(form);
    check.checked = true;
    form.emitir("change", { isTrusted: true });
    afirmar(ctx.api().hayCambios() === true, "tildar un checkbox debe marcar cambios");
}

// --- beforeunload solo frena cuando hay cambios ---------------------------
{
    const campo = crearCampo("nota_gde_if", "IF-1");
    const form = crearForm([campo]);
    const ctx = montar(form);

    let frenado = false;
    const evento = {
        preventDefault() {
            frenado = true;
        },
    };
    ctx.beforeunload(evento);
    afirmar(frenado === false, "sin cambios no debe frenar la salida");

    campo.value = "editado";
    form.emitir("input", { isTrusted: true });
    ctx.beforeunload(evento);
    afirmar(frenado === true, "con cambios debe frenar la salida");
    afirmar(evento.returnValue === "", "debe setear returnValue para el navegador");
}

console.log("informeTecnicoCambiosSinGuardar: todas las comprobaciones pasaron");
