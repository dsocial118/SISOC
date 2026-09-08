document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("pas-ddjj-form");
    if (!form) return;
    const steps = [...form.querySelectorAll(".pas-ddjj-step")];
    const back = document.getElementById("ddjj-back");
    const next = document.getElementById("ddjj-next");
    const submit = document.getElementById("ddjj-submit");
    const confirmModal = document.getElementById("ddjj-confirm-modal");
    let visible = [];
    let current = 0;
    const answer = (name) => form.querySelector(`[name="${name}"]:checked`)?.value || "";
    form.querySelectorAll(".pas-ddjj-options-inverted input").forEach((input) => {
        input.value = input.value === "si" ? "no" : "si";
    });
    const refresh = () => {
        steps.forEach((step) => {
            const condition = step.dataset.condition;
            step.hidden = Boolean(condition && answer(condition) !== "si");
            step.querySelectorAll("input").forEach((input) => { input.disabled = step.hidden; });
        });
        visible = steps.filter((step) => !step.hidden);
        current = Math.min(current, visible.length - 1);
    };
    const validate = () => {
        const controls = [...visible[current].querySelectorAll("input,select")].filter((el) => !el.disabled);
        const radioNames = [...new Set(controls.filter((el) => el.type === "radio").map((el) => el.name))];
        for (const name of radioNames) {
            const group = controls.filter((el) => el.name === name);
            if (!group.some((el) => el.checked)) {
                group[0].setCustomValidity("Elegí una respuesta para continuar.");
                group[0].reportValidity(); group[0].setCustomValidity(""); return false;
            }
        }
        return controls.every((el) => el.reportValidity());
    };
    const contact = () => document.querySelectorAll("[data-summary-field]").forEach((target) => {
        target.value = form.elements[target.dataset.summaryField]?.value || "Sin dato";
    });
    const summary = () => {
        const box = document.getElementById("ddjj-summary"); box.innerHTML = "";
        const appendRow = (label, value) => {
            const row = document.createElement("div"); row.innerHTML = `<strong>${label}</strong><span></span>`;
            row.querySelector("span").textContent = value; box.appendChild(row);
        };
        ["domicilio", "provincia", "municipio"].forEach((name) => {
            const field = form.elements[name]; if (!field) return;
            let value = field.value;
            if (field.tagName === "SELECT") value = field.selectedOptions[0]?.textContent || "";
            const labels = {domicilio:"Domicilio", provincia:"Provincia", municipio:"Municipio"};
            appendRow(labels[name], value);
        });
        [
            ["embarazada", "Embarazo"],
            ["controles_embarazo_cumplidos", "Controles de embarazo"],
            ["hijos_menores_a_cargo", "Menores a cargo"],
            ["vacunacion_cumplida", "Vacunación de menores"],
            ["regularidad_escolar_acreditada", "Regularidad escolar"],
            ["gastos_bajo_limite_smvm", "Gastos sobre 1 SMVM"],
            ["no_accedio_mercado_cambios", "Compra de dólares"],
        ].forEach(([name, label]) => {
            const selected = form.querySelector(`[name="${name}"]:checked`);
            if (!selected || selected.disabled) return;
            const visibleAnswer = selected.closest("label")?.textContent.trim();
            appendRow(label, visibleAnswer || (selected.value === "si" ? "Sí" : "No"));
        });
    };
    const show = (scroll = true) => {
        refresh(); steps.forEach((step) => { step.style.display = "none"; });
        const step = visible[current]; step.style.display = "block";
        const index = Number(step.dataset.stepIndex); const percent = Math.round(index / 7 * 100);
        document.getElementById("ddjj-progress-text").textContent = `Paso ${index} de 7`;
        document.getElementById("ddjj-progress-percent").textContent = `${percent}%`;
        document.getElementById("ddjj-progress-bar").style.width = `${percent}%`;
        back.hidden = current === 0; next.hidden = index === 7; submit.hidden = index !== 7;
        if (index >= 6) contact(); if (index === 7) summary();
        if (scroll) window.scrollTo({top: 0, behavior: "smooth"});
    };
    next.addEventListener("click", () => { if (validate()) { current += 1; show(); } });
    back.addEventListener("click", () => { current = Math.max(0, current - 1); show(); });
    form.addEventListener("change", () => refresh());
    const provincia = form.elements.provincia; const municipio = form.elements.municipio;
    provincia?.addEventListener("change", async () => {
        municipio.innerHTML = '<option value="">Cargando municipios...</option>';
        const url = new URL(form.dataset.municipiosUrl, location.origin); url.searchParams.set("provincia_id", provincia.value);
        try { const response = await fetch(url); const items = await response.json(); municipio.innerHTML = '<option value="">Seleccioná un municipio</option>'; items.forEach(({id,nombre}) => municipio.add(new Option(nombre,id))); }
        catch { municipio.innerHTML = '<option value="">No se pudieron cargar los municipios</option>'; }
    });
    const open = (modal) => { modal.hidden = false; modal.querySelector("button")?.focus(); };
    const close = (modal) => { modal.hidden = true; };
    document.getElementById("ddjj-legal-open").addEventListener("click", () => open(document.getElementById("ddjj-legal-modal")));
    document.querySelectorAll("[data-modal-close]").forEach((button) => button.addEventListener("click", () => close(button.closest(".pas-ddjj-modal"))));
    submit.addEventListener("click", () => { if (validate()) open(confirmModal); });
    document.getElementById("ddjj-confirm-send").addEventListener("click", () => { close(confirmModal); form.requestSubmit(); });
    const errorStep = steps.findIndex((step) => step.querySelector(".errorlist")); if (errorStep >= 0) current = errorStep;
    show(false);
});
