/**
 * COMUNICADOS FORM - JAVASCRIPT
 * Tipo/Subtipo visibility, archivos adjuntos, selector de comedores
 */
(function() {
    // --- Tipo/Subtipo - mostrar/ocultar campos ---
    var tipoSelect = document.getElementById("id_tipo");
    var subtipoOptions = document.getElementById("subtipo-options");
    var subtipoSelect = document.getElementById("id_subtipo");
    var comedoresOptions = document.getElementById("comedores-options");
    var destacadoOption = document.getElementById("destacado-option");
    var paraTodosCheckbox = document.getElementById("id_para_todos_comedores");
    var comedoresSelector = document.getElementById("comedores-selector");

    function updateFieldsVisibility() {
        if (!tipoSelect) return;
        var isExterno = tipoSelect.value === "externo";

        if (subtipoOptions) subtipoOptions.classList.toggle("d-none", !isExterno);
        if (!isExterno && subtipoSelect) subtipoSelect.value = "";

        updateSubtipoVisibility();

        if (destacadoOption) destacadoOption.classList.toggle("d-none", isExterno);
    }

    function updateSubtipoVisibility() {
        if (!subtipoSelect) return;
        var isComedores = subtipoSelect.value === "comedores";
        if (comedoresOptions) comedoresOptions.classList.toggle("d-none", !isComedores);
    }

    function updateComedoresSelector() {
        if (!paraTodosCheckbox || !comedoresSelector) return;
        comedoresSelector.classList.toggle("d-none", paraTodosCheckbox.checked);
    }

    if (tipoSelect) {
        tipoSelect.addEventListener("change", updateFieldsVisibility);
        updateFieldsVisibility();
    }
    if (subtipoSelect) subtipoSelect.addEventListener("change", updateSubtipoVisibility);
    if (paraTodosCheckbox) {
        paraTodosCheckbox.addEventListener("change", updateComedoresSelector);
        updateComedoresSelector();
    }

    // --- Archivos adjuntos ---
    var selectedFiles = [];
    var addFilesBtn = document.getElementById("addFilesBtn");
    var archivosInput = document.getElementById("archivosInput");
    var selectedFilesInfo = document.getElementById("selectedFilesInfo");
    var fileCount = document.getElementById("fileCount");
    var filePreviewContainer = document.getElementById("filePreviewContainer");

    if (addFilesBtn && archivosInput) {
        addFilesBtn.addEventListener("click", function() { archivosInput.click(); });

        archivosInput.addEventListener("change", function() {
            selectedFiles = selectedFiles.concat(Array.from(this.files));
            updateFileDisplay();
        });

        function updateFileDisplay() {
            if (selectedFiles.length > 0) {
                if (selectedFilesInfo) selectedFilesInfo.classList.remove("d-none");
                if (fileCount) fileCount.textContent = selectedFiles.length;
            } else {
                if (selectedFilesInfo) selectedFilesInfo.classList.add("d-none");
            }

            if (filePreviewContainer) {
                filePreviewContainer.innerHTML = "";
                selectedFiles.forEach(function(file, index) {
                    var div = document.createElement("div");
                    div.className = "archivo-preview-item d-flex align-items-center justify-content-between p-2 mb-2 rounded";

                    var icon = "fas fa-file";
                    if (file.type.startsWith("image/")) icon = "fas fa-file-image";
                    else if (file.type.includes("pdf")) icon = "fas fa-file-pdf";
                    else if (file.type.includes("word") || file.name.endsWith(".doc") || file.name.endsWith(".docx")) icon = "fas fa-file-word";
                    else if (file.type.includes("excel") || file.name.endsWith(".xls") || file.name.endsWith(".xlsx")) icon = "fas fa-file-excel";

                    div.innerHTML =
                        '<div class="d-flex align-items-center">' +
                            '<i class="' + icon + ' me-2" style="color: #f39c12;"></i>' +
                            '<div>' +
                                '<div class="fw-bold small">' + file.name + '</div>' +
                                '<div class="small" style="color: #6b7280;">' + formatSize(file.size) + '</div>' +
                            '</div>' +
                        '</div>' +
                        '<button type="button" class="btn btn-sm btn-outline-danger btn-remove-file" data-index="' + index + '">' +
                            '<i class="fas fa-times"></i>' +
                        '</button>';

                    filePreviewContainer.appendChild(div);
                });

                filePreviewContainer.querySelectorAll(".btn-remove-file").forEach(function(btn) {
                    btn.addEventListener("click", function() {
                        selectedFiles.splice(parseInt(this.getAttribute("data-index")), 1);
                        updateFileDisplay();
                    });
                });
            }
        }

        function formatSize(bytes) {
            if (bytes === 0) return "0 B";
            var k = 1024, sizes = ["B", "KB", "MB", "GB"];
            var i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
        }

        var form = document.querySelector('form[enctype="multipart/form-data"]');
        if (form) {
            form.addEventListener("submit", function(e) {
                if (selectedFiles.length > 0) {
                    e.preventDefault();
                    e.stopPropagation();
                    var fd = new FormData(form);
                    fd.delete("archivos_adjuntos");
                    selectedFiles.forEach(function(f) { fd.append("archivos_adjuntos", f); });

                    fetch(form.action || window.location.href, { method: "POST", body: fd })
                    .then(function(r) {
                        if (r.redirected) window.location.href = r.url;
                        else if (r.ok) window.location.href = r.url || window.location.href;
                        else alert("Error al guardar el comunicado");
                    })
                    .catch(function() { alert("Error al enviar el formulario"); });
                    return false;
                }
            }, true);
        }
    }

    // --- Selector de comedores ---
    var comedorSearch = document.getElementById("comedorSearch");
    var comedoresLista = document.getElementById("comedoresLista");
    var seleccionadosContainer = document.getElementById("comedoresSeleccionados");
    var selectOriginal = document.getElementById("id_comedores");

    if (comedorSearch && selectOriginal && comedoresLista) {
        var allOptions = [];
        Array.from(selectOriginal.options).forEach(function(opt) {
            allOptions.push({ value: opt.value, text: opt.text });
        });

        renderAll();
        comedorSearch.addEventListener("input", function() {
            renderLista(this.value.trim().toLowerCase());
        });

        function isSelected(value) {
            var opt = selectOriginal.querySelector('option[value="' + value + '"]');
            return opt ? opt.selected : false;
        }

        function toggleComedor(value, add) {
            var opt = selectOriginal.querySelector('option[value="' + value + '"]');
            if (opt) opt.selected = add;
            renderAll();
        }

        function renderAll() {
            renderSeleccionados();
            renderLista(comedorSearch.value.trim().toLowerCase());
        }

        function renderSeleccionados() {
            seleccionadosContainer.innerHTML = "";
            var hay = false;
            allOptions.forEach(function(opt) {
                if (!isSelected(opt.value)) return;
                hay = true;
                var badge = document.createElement("span");
                badge.className = "badge me-1 mb-1 d-inline-flex align-items-center gap-1";
                badge.innerHTML = opt.text +
                    ' <button type="button" class="btn-close btn-close-white" style="font-size:0.55em;" data-value="' + opt.value + '"></button>';
                badge.querySelector(".btn-close").addEventListener("click", function() {
                    toggleComedor(this.getAttribute("data-value"), false);
                });
                seleccionadosContainer.appendChild(badge);
            });
            if (!hay) {
                seleccionadosContainer.innerHTML = '<p class="small mb-0" style="color:#6b7280;">No hay comedores seleccionados.</p>';
            }
        }

        function renderLista(query) {
            comedoresLista.innerHTML = "";
            var filtered = allOptions.filter(function(opt) {
                return !query || opt.text.toLowerCase().indexOf(query) !== -1;
            });

            if (filtered.length === 0) {
                comedoresLista.innerHTML = '<div style="padding:16px;text-align:center;color:#6b7280;">No se encontraron comedores.</div>';
                return;
            }

            filtered.forEach(function(opt) {
                var sel = isSelected(opt.value);
                var row = document.createElement("div");
                row.className = "comedor-row";

                var name = document.createElement("span");
                name.className = "comedor-nombre";
                name.textContent = opt.text;

                var btn = document.createElement("button");
                btn.type = "button";
                btn.setAttribute("data-value", opt.value);

                if (sel) {
                    btn.className = "btn btn-sm btn-outline-danger";
                    btn.innerHTML = '<i class="fas fa-times"></i> Quitar';
                    btn.addEventListener("click", function() {
                        toggleComedor(this.getAttribute("data-value"), false);
                    });
                } else {
                    btn.className = "btn btn-sm btn-outline-warning";
                    btn.innerHTML = '<i class="fas fa-plus"></i> Agregar';
                    btn.addEventListener("click", function() {
                        toggleComedor(this.getAttribute("data-value"), true);
                    });
                }

                row.appendChild(name);
                row.appendChild(btn);
                comedoresLista.appendChild(row);
            });
        }
    }
})();
