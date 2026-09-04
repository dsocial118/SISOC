(function (document) {
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            return parts.pop().split(";").shift();
        }
        return "";
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function renderErrors(errorsContainer, errors) {
        const messages = [];
        Object.entries(errors || {}).forEach(([field, fieldErrors]) => {
            fieldErrors.forEach((error) => messages.push(`${field}: ${error}`));
        });
        errorsContainer.innerHTML = messages.map(escapeHtml).join("<br>");
        errorsContainer.hidden = messages.length === 0;
    }

    function renderPreview(preview, data) {
        const meta = document.getElementById("pasInformePreviewMeta");
        const head = document.getElementById("pasInformePreviewHead");
        const body = document.getElementById("pasInformePreviewBody");
        const errors = document.getElementById("pasInformePreviewErrors");

        preview.hidden = false;
        errors.hidden = true;
        errors.innerHTML = "";
        meta.textContent = `${data.total} filas encontradas. Se muestran hasta ${data.limit}. Modo: ${data.modo}.`;

        head.innerHTML = `
            <tr>
                ${data.columns.map((column) => `<th>${escapeHtml(column.label)}</th>`).join("")}
            </tr>
        `;
        if (!data.rows.length) {
            body.innerHTML = `<tr><td colspan="${data.columns.length}" class="text-center text-muted py-3">Sin resultados para los filtros aplicados.</td></tr>`;
            return;
        }
        body.innerHTML = data.rows
            .map(
                (row) => `
                    <tr>
                        ${data.columns
                            .map((column) => `<td>${escapeHtml(row[column.key])}</td>`)
                            .join("")}
                    </tr>
                `
            )
            .join("");
    }

    document.addEventListener("DOMContentLoaded", function () {
        const form = document.getElementById("pasInformeForm");
        const button = document.getElementById("pasInformePreviewBtn");
        const preview = document.getElementById("pasInformePreview");
        if (!form || !button || !preview) {
            return;
        }

        const provincia = document.getElementById("id_provincia");
        const municipio = document.getElementById("id_municipio");
        if (provincia && municipio && window.ajaxLoadMunicipiosUrl) {
            provincia.addEventListener("change", async function () {
                municipio.innerHTML = '<option value="">---------</option>';
                if (!provincia.value) {
                    return;
                }
                const url = `${window.ajaxLoadMunicipiosUrl}?provincia_id=${encodeURIComponent(provincia.value)}`;
                const response = await fetch(url, {
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                    credentials: "same-origin",
                });
                if (!response.ok) {
                    return;
                }
                const municipios = await response.json();
                municipios.forEach((item) => {
                    const option = document.createElement("option");
                    option.value = item.id;
                    option.textContent = item.nombre;
                    municipio.appendChild(option);
                });
            });
        }

        button.addEventListener("click", async function () {
            const errors = document.getElementById("pasInformePreviewErrors");
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Previsualizando';
            try {
                const response = await fetch(form.dataset.previewUrl, {
                    method: "POST",
                    body: new FormData(form),
                    headers: {
                        "X-CSRFToken": getCookie("csrftoken"),
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    credentials: "same-origin",
                });
                const data = await response.json();
                if (!response.ok || !data.ok) {
                    preview.hidden = false;
                    renderErrors(errors, data.errors);
                    return;
                }
                renderPreview(preview, data);
            } catch (error) {
                preview.hidden = false;
                renderErrors(errors, { preview: ["No se pudo previsualizar el informe."] });
            } finally {
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-eye mr-1"></i> Previsualizar';
            }
        });
    });
})(document);
