document.addEventListener("DOMContentLoaded", function () {
    const feedback = document.getElementById("revision-feedback");
    const selectoresEstado = document.querySelectorAll(".js-documento-estado");
    const statusBadge = document.getElementById("rendicion-estado-badge");
    const downloadAction = document.getElementById("rendicion-download-action");
    const downloadUrl = "./descargar-pdf/";

    const renderRendicionBadge = function (estado, label) {
        if (!statusBadge) {
            return;
        }

        statusBadge.textContent = label;
        statusBadge.className = "badge-validacion";
        if (estado === "finalizada") {
            statusBadge.classList.add("validado");
            return;
        }
        if (estado === "subsanar") {
            statusBadge.classList.add("no-validado");
            return;
        }
        statusBadge.classList.add("pendiente");
    };

    const renderDownloadAction = function (enabled, customUrl) {
        if (!downloadAction) {
            return;
        }
        if (!enabled) {
            downloadAction.innerHTML = "";
            return;
        }

        const href = customUrl || downloadUrl;
        downloadAction.innerHTML =
            '<a href="' +
            href +
            '" class="btn btn-sm btn-success">' +
            '<i class="fas fa-file-pdf"></i> Generar descarga</a>';
    };

    const showFeedback = function (message, kind) {
        if (!feedback) {
            return;
        }
        feedback.textContent = message;
        feedback.className = "alert mb-3";
        feedback.classList.add(kind === "error" ? "alert-danger" : "alert-success");
    };

    const renderEstadoBadge = function (estadoVisual, estadoLabelVisual) {
        let badgeClass = "badge-validacion pendiente";
        if (estadoVisual === "validado") {
            badgeClass = "badge-validacion validado";
        } else if (estadoVisual === "subsanar") {
            badgeClass = "badge-validacion no-validado";
        }

        return (
            '<span class="' + badgeClass + '">' + estadoLabelVisual + "</span>"
        );
    };

    const bloquearRevisionCelda = function (documentoId) {
        const revisionCell = document.getElementById("revision-cell-" + documentoId);
        if (revisionCell) {
            revisionCell.innerHTML = '<span class="text-muted">-</span>';
        }
    };

    const actualizarObservaciones = function (documentoId, observaciones) {
        const observacionesRow = document.getElementById(
            "observaciones-row-" + documentoId
        );
        if (!observacionesRow) {
            return;
        }

        if (!observaciones) {
            observacionesRow.classList.add("d-none");
            return;
        }

        observacionesRow.classList.remove("d-none");
        const cell = observacionesRow.querySelector("td");
        if (!cell) {
            return;
        }

        let display = document.getElementById("observaciones-display-" + documentoId);
        if (!display) {
            cell.innerHTML =
                '<div class="ps-3" id="observaciones-display-' +
                documentoId +
                '"></div>';
            display = document.getElementById("observaciones-display-" + documentoId);
        }

        if (display) {
            display.innerHTML = "<strong>Observaciones:</strong> " + observaciones;
        }
    };

    const setSubmitterLoading = function (submitter, isLoading) {
        if (!submitter) {
            return;
        }

        submitter.disabled = isLoading;
        const idle = submitter.querySelector(".js-submit-idle");
        const spinner = submitter.querySelector(".js-submit-spinner");

        if (idle) {
            idle.classList.toggle("d-none", isLoading);
        }
        if (spinner) {
            spinner.classList.toggle("d-none", !isLoading);
        }
    };

    selectoresEstado.forEach(function (selector) {
        const documentoId = selector.dataset.documentoId;
        const form = document.getElementById("revision-documento-" + documentoId);
        const observacionesInput = document.getElementById(
            "observaciones-" + documentoId
        );
        const observacionesRow = document.getElementById(
            "observaciones-row-" + documentoId
        );
        const botonGuardar = document.getElementById(
            "guardar-revision-inline-" + documentoId
        );
        const botonGuardarObservaciones = document.getElementById(
            "guardar-revision-observaciones-" + documentoId
        );

        const actualizarFilaRevision = function () {
            const estadoSeleccionado = selector.value;
            const mostrarObservaciones = estadoSeleccionado === "subsanar";
            const mostrarGuardarInline = estadoSeleccionado === "validado";
            const mostrarGuardarObservaciones = estadoSeleccionado === "subsanar";

            if (observacionesInput) {
                observacionesInput.required = mostrarObservaciones;
                if (!mostrarObservaciones) {
                    observacionesInput.value = "";
                }
            }

            if (observacionesRow) {
                observacionesRow.classList.toggle("d-none", !mostrarObservaciones);
            }

            if (botonGuardar) {
                botonGuardar.classList.toggle("d-none", !mostrarGuardarInline);
            }

            if (botonGuardarObservaciones) {
                botonGuardarObservaciones.classList.toggle(
                    "d-none",
                    !mostrarGuardarObservaciones
                );
            }
        };

        selector.addEventListener("change", actualizarFilaRevision);
        actualizarFilaRevision();

        if (!form) {
            return;
        }

        form.addEventListener("submit", function (event) {
            event.preventDefault();

            const estadoSeleccionado = selector.value;
            const formData = new FormData(form);
            formData.set("estado", estadoSeleccionado);
            formData.set(
                "observaciones",
                observacionesInput ? observacionesInput.value.trim() : ""
            );

            const submitter =
                event.submitter && event.submitter.form === form
                    ? event.submitter
                    : null;

            setSubmitterLoading(submitter, true);

            fetch(window.location.href, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
                body: formData,
            })
                .then(function (response) {
                    return response.json().then(function (data) {
                        if (!response.ok) {
                            throw new Error(
                                data.message || "No se pudo actualizar el documento."
                            );
                        }
                        return data;
                    });
                })
                .then(function (data) {
                    showFeedback(data.message, "success");

                    const estadoCell = document.getElementById(
                        "estado-cell-" + documentoId
                    );
                    if (estadoCell) {
                        estadoCell.innerHTML = renderEstadoBadge(
                            data.documento.estado_visual,
                            data.documento.estado_visual_display
                        );
                    }

                    bloquearRevisionCelda(documentoId);
                    actualizarObservaciones(
                        documentoId,
                        data.documento.observaciones
                    );
                    renderRendicionBadge(
                        data.rendicion.estado,
                        data.rendicion.estado_display
                    );
                    renderDownloadAction(
                        data.rendicion.puede_descargar_pdf,
                        data.rendicion.download_url
                    );
                })
                .catch(function (error) {
                    showFeedback(error.message, "error");
                })
                .finally(function () {
                    setSubmitterLoading(submitter, false);
                });
        });
    });
});
