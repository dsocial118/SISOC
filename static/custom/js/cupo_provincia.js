// static/custom/js/cupo_provincia.js
// Added escapeHtml utility to sanitize alert messages and avoid XSS.
(function () {
  // --- Config tomada del HTML (data-*) ---
  const root = document.getElementById("cupo-root");
  if (!root) return; // página no coincide

  const urlConfig = root.dataset.urlConfig;
  const urlBajaTpl = (root.dataset.urlBajaTpl || "").replace("/0/", "/{id}/");
  const urlSuspTpl = (root.dataset.urlSuspTpl || "").replace("/0/", "/{id}/");
  const urlReactivarTpl = (root.dataset.urlReactivarTpl || "").replace("/0/", "/{id}/");

  // --- CSRF ---
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
  }
  const csrftoken = getCookie("csrftoken");

  // --- Utilidades ---
  const escapeHtml = (str) =>
    String(str).replace(
      /[&<>"']/g,
      (c) =>
        ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );

  // --- Alertas ---
  const alerta = (msg, kind = "success") => {
    const el = document.getElementById("alerts");
    if (!el) return;
    el.innerHTML = `<div class="alert alert-${kind} alert-dismissible fade show" role="alert">
      ${escapeHtml(msg)}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
    </div>`;
  };

  // --- Configurar cupo (modal) ---
  const formConfig = document.getElementById("form-config");
  if (formConfig) {
    formConfig.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = document.getElementById("btn-config-guardar");
      const spin = document.getElementById("spin-config");
      if (btn && spin) { btn.disabled = true; spin.classList.remove("d-none"); }

      const fd = new FormData(formConfig);
      fd.set("accion", "config");

      const total = fd.get("total_asignado");
      if (total === null || total === "" || Number(total) < 0) {
        alerta("Ingresá un valor de cupo válido (entero ≥ 0).", "warning");
        if (btn && spin) { btn.disabled = false; spin.classList.add("d-none"); }
        return;
      }

      try {
        const resp = await fetch(urlConfig, {
          method: "POST",
          headers: { "X-CSRFToken": csrftoken },
          body: fd,
        });
        const data = await resp.json();
        if (!resp.ok || data.success === false) {
          throw new Error(data.message || "No se pudo guardar el cupo.");
        }
        alerta("Cupo actualizado correctamente.");
        const modalEl = document.getElementById("modalConfigCupo");
        if (modalEl && window.bootstrap) {
          const modal = window.bootstrap.Modal.getInstance(modalEl) || new window.bootstrap.Modal(modalEl);
          modal.hide();
        }
        setTimeout(() => location.reload(), 600);
      } catch (err) {
        alerta(err.message || "Error al configurar el cupo.", "danger");
        if (btn && spin) { btn.disabled = false; spin.classList.add("d-none"); }
      }
    });
  }

  // --- Filtro tabla ocupados ---
  const filtro = document.getElementById("filtro");
  if (filtro) {
    filtro.addEventListener("input", (e) => {
      const q = (e.target.value || "").toLowerCase();
      document.querySelectorAll("#tabla-ocupados tbody tr[data-row]").forEach((tr) => {
        const hay = Array.from(tr.querySelectorAll("td[data-text]")).some((td) =>
          (td.getAttribute("data-text") || "").toLowerCase().includes(q)
        );
        tr.style.display = hay ? "" : "none";
      });
    });
  }

  // --- Filtro tabla suspendidos ---
  const filtroSusp = document.getElementById("filtro-suspendidos");
  if (filtroSusp) {
    filtroSusp.addEventListener("input", (e) => {
      const q = (e.target.value || "").toLowerCase();
      document
        .querySelectorAll("#tabla-suspendidos tbody tr[data-row]")
        .forEach((tr) => {
          const hay = Array.from(tr.querySelectorAll("td[data-text]")).some((td) =>
            (td.getAttribute("data-text") || "").toLowerCase().includes(q)
          );
          tr.style.display = hay ? "" : "none";
        });
    });
  }

  // --- Filtro tabla lista de espera ---
  const filtroLista = document.getElementById("filtro-lista-espera");
  if (filtroLista) {
    filtroLista.addEventListener("input", (e) => {
      const q = (e.target.value || "").toLowerCase();
      document
        .querySelectorAll("#tabla-lista-espera tbody tr[data-row]")
        .forEach((tr) => {
          const hay = Array.from(tr.querySelectorAll("td[data-text]")).some((td) =>
            (td.getAttribute("data-text") || "").toLowerCase().includes(q)
          );
          tr.style.display = hay ? "" : "none";
        });
    });
  }

  // --- Modales Suspender/Baja ---
  const modalSuspEl = document.getElementById("modalSuspender");
  const modalBajaEl = document.getElementById("modalBaja");
  const modalSusp = modalSuspEl && window.bootstrap ? new window.bootstrap.Modal(modalSuspEl) : null;
  const modalBaja = modalBajaEl && window.bootstrap ? new window.bootstrap.Modal(modalBajaEl) : null;

  document.querySelectorAll(".btn-suspender").forEach((b) => {
    b.addEventListener("click", () => {
      const inputId = document.getElementById("suspender-legajo-id");
      const form = document.getElementById("form-suspender");
      if (inputId) inputId.value = b.dataset.legajoId || "";
      if (form) form.reset();
      if (modalSusp) modalSusp.show();
    });
  });

  document.querySelectorAll(".btn-baja").forEach((b) => {
    b.addEventListener("click", () => {
      const inputId = document.getElementById("baja-legajo-id");
      const form = document.getElementById("form-baja");
      if (inputId) inputId.value = b.dataset.legajoId || "";
      if (form) form.reset();
      if (modalBaja) modalBaja.show();
    });
  });

  // --- Submit suspensión ---
  const formSusp = document.getElementById("form-suspender");
  if (formSusp) {
    formSusp.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = document.getElementById("btn-confirm-suspender");
      const spin = document.getElementById("spin-suspender");
      if (btn && spin) { btn.disabled = true; spin.classList.remove("d-none"); }

      const legajoId = document.getElementById("suspender-legajo-id")?.value;
      const data = new FormData(e.target);
      try {
        const resp = await fetch(urlSuspTpl.replace("{id}", legajoId), {
          method: "POST",
          headers: { "X-CSRFToken": csrftoken },
          body: data,
        });
        const json = await resp.json();
        if (!resp.ok || json.success === false) throw new Error(json.message || "Error");
        alerta("Suspensión registrada y cupo actualizado.");
        if (modalSusp) modalSusp.hide();
        setTimeout(() => location.reload(), 700);
      } catch (err) {
        alerta(err.message || "No se pudo suspender el legajo.", "danger");
        if (btn && spin) { btn.disabled = false; spin.classList.add("d-none"); }
      }
    });
  }

  // --- Submit baja ---
  const formBaja = document.getElementById("form-baja");
  if (formBaja) {
    formBaja.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = document.getElementById("btn-confirm-baja");
      const spin = document.getElementById("spin-baja");
      if (btn && spin) { btn.disabled = true; spin.classList.remove("d-none"); }

      const legajoId = document.getElementById("baja-legajo-id")?.value;
      const data = new FormData(e.target);
      try {
        const resp = await fetch(urlBajaTpl.replace("{id}", legajoId), {
          method: "POST",
          headers: { "X-CSRFToken": csrftoken },
          body: data,
        });
        const json = await resp.json();
        if (!resp.ok || json.success === false) throw new Error(json.message || "Error");
        alerta("Baja registrada y cupo actualizado.");
        if (modalBaja) modalBaja.hide();
        setTimeout(() => location.reload(), 700);
      } catch (err) {
        alerta(err.message || "No se pudo dar de baja el legajo.", "danger");
        if (btn && spin) { btn.disabled = false; spin.classList.add("d-none"); }
      }
    });
  }

  // --- Reactivar (solo en tabla de suspendidos) ---
  document.querySelectorAll(".btn-reactivar").forEach((b) => {
    b.addEventListener("click", async () => {
      if (!confirm("¿Reactivar al titular suspendido?")) return;

      const legajoId = b.dataset.legajoId;
      const fd = new FormData();
      try {
        const resp = await fetch(urlReactivarTpl.replace("{id}", legajoId), {
          method: "POST",
          headers: { "X-CSRFToken": csrftoken },
          body: fd,
        });
        const json = await resp.json();
        if (!resp.ok || json.success === false) throw new Error(json.message || "Error");
        alerta("Titular reactivado.");
        setTimeout(() => location.reload(), 700);
      } catch (err) {
        alerta(err.message || "No se pudo reactivar el legajo.", "danger");
      }
    });
  });

  // --- Filtro histórico por DNI ---
  const filtroHist = document.getElementById("filtro-historico");
  if (filtroHist) {
    filtroHist.addEventListener("input", (e) => {
      const q = (e.target.value || "").toLowerCase();
      document.querySelectorAll("#tabla-historico tbody tr[data-row]").forEach((tr) => {
        const dniCell = tr.querySelector("td:nth-child(2)");
        const val = (dniCell?.textContent || "").toLowerCase();
        tr.style.display = val.includes(q) ? "" : "none";
      });
    });
  }
})();
