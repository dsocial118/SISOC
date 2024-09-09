
    const url = window.location.href;
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const resultsBox = $('#results-box');
    const formNuevo = $('#nuevo_legajo_familiar');

    if (!searchForm || !searchInput || !resultsBox.length || !formNuevo.length) {
        console.error("One or more elements not found:", { searchForm, searchInput, resultsBox, formNuevo });
    
    }
    resultsBox.append('<td colspan="8" class="text-center text-muted h4">Realice una busqueda.</td>');
    const csrf = document.getElementsByName('csrfmiddlewaretoken')[0].value;

    if (!csrf) {
        console.error("CSRF token not found");
        
    }

    const sendSearchData = (busqueda, pageNumber = 1) => {
        $('#loadingIndicator').show();
        $.ajax({
            type: 'POST',
            url: searchUrl,
            data: {
                'csrfmiddlewaretoken': csrf,
                'busqueda': busqueda,
                'id': pk1,
                'page': pageNumber,
            },
            success: (res) => {
                const data = res.data.hogares;
                if (Array.isArray(data)) {
                    resultsBox.empty(); // Vaciar contenido anterior
                    data.forEach(r => {
                        resultsBox.append(`
                            <tr id="id_tr${r.pk}" >
                                <td>${r.apellido}</td>
                                <td>${r.nombre}</td>
                                <td>${r.documento}</td>
                                <td>${formEstadoRelacion}</td>
                                <td class="text-right">
                                    <button class="btn btn-primary btn-sm" id="btn_1" onclick="submitForms('id_tr${r.pk}','${r.pk}');" type="button">Agregar</button>
                                </td>
                            </tr>
                        `);
                    });
                    formNuevo.addClass('d-none');
                } else {
                    if (searchInput.value.length > 0) {
                        resultsBox.empty(); // Vaciar contenido anterior
                        formNuevo.removeClass('d-none');
                    }else{
                        formNuevo.addClass('d-none');
                    }
                }
                updatePaginationControls(res.data);
                $('#loadingIndicator').hide();
            },
            error: (err) => {
                console.log("Error: ", err);
            }
        });
    };

    function updatePaginationControls(data) {
        if (data.has_previous) {
            $('#prevPage').show();
        } else {
            $('#prevPage').hide();
        }
        if (data.has_next) {
            $('#nextPage').show();
        } else {
            $('#nextPage').hide();
        }

        $('#currentPage').text(`Página ${data.page} de ${data.num_pages}`);
        // Manejar clics en los botones de paginación
        $('#prevPage').off('click').on('click', function (e) {
            e.preventDefault();
            sendSearchData(searchInput.value, parseInt(data.page) - 1);
        });
        $('#nextPage').off('click').on('click', function (e) {
            e.preventDefault();
            sendSearchData(searchInput.value, parseInt(data.page) + 1);
        });
    }

    // Activa la búsqueda ajax cuando se ingresa texto
    searchInput.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
            sendSearchData(e.target.value);
            e.preventDefault();
        } else {
            resultsBox.innerHTML = '<td colspan="8" class="text-center text-muted h4">Realice una búsqueda.</td>';
        }
    });

    // Crea Django Ajax Call
    function submitForms(trId, pk) {
        var tr = document.getElementById(trId);
        var tdValues = tr.getElementsByTagName('td');
        var selectValues = tr.getElementsByTagName('select');
        var values = {};
        const addNombre = tdValues[0].innerHTML;
        const addApellido = tdValues[1].innerHTML;
        const addDocumento = tdValues[2].innerHTML;
        const addRelacion = selectValues[0].value;
        
        // Validar que todos los campos select estén seleccionados
        var allFieldsSelected = true;
        Array.from(selectValues).forEach(function (select) {
            if (select.value === "") {
                allFieldsSelected = false;
                select.classList.add("is-invalid"); // Agregar clase 'is-invalid' para resaltar el campo inválido
            } else {
                select.classList.remove("is-invalid"); // Quitar clase 'is-invalid' si el campo es válido
            }
        });

        if (allFieldsSelected) {
            // Create Ajax Call
            $.ajax({
                url: createUrl,
                data: {
                    'fk_legajo_1': pk1,
                    'fk_legajo_2': pk,
                    'estado_relacion': addRelacion,
                },
                dataType: 'json',
                success: function (data) {
                    let hogarFoto = data.hogar.foto != null && data.hogar.foto != "" ? mediaUrl + data.hogar.foto : staticUrl + 'custom/img/default.png';
                    $("#tablaResultado").append(`
                        <div id="familiar-${data.hogar.id} class="col-md-3">
                            <ul class="users-list">
                                <li style="width:auto">
                                    <img src="${hogarFoto}" alt="User Image" width="60px">
                                    <img src="${staticUrl + 'custom/img/default.png'}" alt="User Image" width="60px">
                                    <span class="users-list-name">${data.hogar.apellido}, ${data.hogar.nombre}</span>
                                    <span class="users-list-date"><button
                                        class="btn btn-danger btn-sm"
                                        onclick='deleteHogar("${data.hogar.id}")'
                                        type="submit">Eliminar</button></span>
                                </li>
                            </ul>
                        </div>
                    `);
                    $(searchInput).val(""); // Vaciar el campo de búsqueda
                    resultsBox.empty(); // Vaciar contenido anterior   
                    $('#sin-familiares').remove();
                    toastr.options = { "positionClass": "toast-bottom-right" };
                    toastr[data.data.tipo_mensaje](data.data.mensaje);
                }
            });
        } else {
            // Mostrar un mensaje de error o realizar alguna acción en caso de campos incompletos
            console.log("Todos los campos deben estar completos");
        }
    }

    function deleteHogar(id) {
        $.ajax({
            url: deleteUrl,
            data: {
                'id': id,
            },
            dataType: 'json',
            success: function (data) {
                $("#familiar-" + id).remove();
                $('#tablaResultado').load(window.location.href + ' #tablaResultado');
                $(searchInput).val(""); // Vaciar el campo de búsqueda
                resultsBox.empty(); // Vaciar contenido anterior
                resultsBox.append('<td colspan="8" class="text-center text-muted h4">Realice una busqueda.</td>');
                $('#formulario-nuevo')[0].reset();
                formNuevo.addClass('d-none');
                toastr.options = { "positionClass": "toast-bottom-right" };
                toastr[data.tipo_mensaje](data.mensaje);
            }
        });
    }

    function insertErrorMessage(element, message) {
        var small = document.createElement('small');
        small.classList.add('text-danger');
        small.textContent = message;

        var divWrapper = document.createElement('div');
        divWrapper.appendChild(small);

        var wrapper = document.createElement('div');
        wrapper.classList.add('error-wrapper');
        wrapper.appendChild(divWrapper);

        element.parentNode.insertBefore(wrapper, element.nextSibling);
    }

    $('#formulario-nuevo').submit(function (event) {
        event.preventDefault(); // Evitar el envío del formulario

        // Validar campos antes de enviar el formulario
        if (validarCampos()) {
            this.submit(); // Enviar el formulario si los campos son válidos
        }
    });

    function validarCampos() {
        let valido = true;

        // Validar cada campo individualmente
        $('#formulario-nuevo input, #formulario-nuevo select').each(function () {
            if ($(this).prop('required') && $(this).val() === '') {
                // Agregar clase de advertencia al campo vacío
                $(this).addClass('is-invalid');
                valido = false;
            } else {
                $(this).removeClass('is-invalid');
            }
        });

        return valido;
    }

    // Verificar si hay errores en el formulario
    const form = $('#formulario-nuevo');
    let hasErrors = false;
    form.querySelectorAll('.is-invalid').forEach(function (field) {
        hasErrors = true;
        return false; // Salir del bucle si se encuentra un campo inválido
    });

    if (hasErrors) {
        document.getElementById('nuevo_legajo_familiar').classList.remove('d-none');
    } else {
        document.getElementById('nuevo_legajo_familiar').classList.add('d-none');
    }
