document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded and parsed");

    const contextData = document.getElementById('context-data');
    if (contextData) {
        // Extraer las variables desde los data-attributes
        const searchUrl = contextData.dataset.searchUrl;
        const createUrl = contextData.dataset.createUrl;
        const deleteUrl = contextData.dataset.deleteUrl;
        const pk = contextData.dataset.pk;
        const formVinculo = contextData.dataset.formVinculo;
        const formEstadoRelacion = contextData.dataset.formEstadoRelacion;
        const formConviven = contextData.dataset.formConviven;
        const formCuidadorPrincipal = contextData.dataset.formCuidadorPrincipal;
        const mediaUrl = contextData.dataset.mediaUrl;
        const staticUrl = contextData.dataset.staticUrl;

        // Verificación en consola
        console.log("searchUrl:", searchUrl);
        console.log("createUrl:", createUrl);
        console.log("deleteUrl:", deleteUrl);
        console.log("pk:", pk);
        console.log("formVinculo:", formVinculo);
        console.log("formEstadoRelacion:", formEstadoRelacion);
        console.log("formConviven:", formConviven);
        console.log("formCuidadorPrincipal:", formCuidadorPrincipal);
        console.log("mediaUrl:", mediaUrl);
        console.log("staticUrl:", staticUrl);
    } else {
        console.error("Element with ID 'context-data' not found.");
    }

    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const resultsBox = $('#results-box');
    const formNuevo = $('#nuevo_legajo_familiar');

    resultsBox.append('<td colspan="8" class="text-center text-muted h4">Realice una búsqueda.</td>');

    const csrf = document.getElementsByName('csrfmiddlewaretoken')[0]?.value;
    if (csrf) {
        console.log("CSRF token:", csrf);
    } else {
        console.error("CSRF token not found.");
    }
});


const sendSearchData = (busqueda, pageNumber=1) => {
    console.log("sendSearchData called with busqueda:", busqueda, "pageNumber:", pageNumber);
    $('#loadingIndicator').show();
    $.ajax({
        type: 'POST',
        url: searchUrl,
        data: {
            'csrfmiddlewaretoken': csrf,
            'busqueda': busqueda,
            'id': pk,
            'page': pageNumber,
        },
        success: (res) => {
            console.log("AJAX success response:", res);
            const data = res.data.familiares;
            if (Array.isArray(data)) {
                resultsBox.empty(); // Vaciar contenido anterior
                data.forEach(r => {
                    resultsBox.append(`
                        <tr id="id_tr${r.pk}" >
                            <td>${r.apellido}</td>
                            <td>${r.nombre}</td>
                            <td>${r.documento}</td>
                            <td>${formVinculo}</td>
                            <td>${formEstadoRelacion}</td>
                            <td class="text-center">${formConviven}</td>
                            <td class="text-center">${formCuidadorPrincipal}</td>
                            <td class="text-right">
                                <button class="btn btn-primary btn-sm" id="btn_1" onclick="submitForms('id_tr${r.pk}','${r.pk}');" type="button">Agregar</button>
                            </td>
                        </tr>
                    `);
                });
            } else {
                if (searchInput.value.length > 0) {
                    resultsBox.empty(); // Vaciar contenido anterior
                    formNuevo.removeClass('d-none');
                }
            }
            updatePaginationControls(res.data);
            $('#loadingIndicator').hide();
        },
        error: (err) => {
            console.log("AJAX error:", err);
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
    $('#prevPage').off('click').on('click', function(e) {
        e.preventDefault();
        sendSearchData(searchInput.value, parseInt(data.page) - 1);
    });
    $('#nextPage').off('click').on('click', function(e) {
        e.preventDefault();
        sendSearchData(searchInput.value, parseInt(data.page) + 1);
    });
}

searchInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
        sendSearchData(e.target.value);
        e.preventDefault();
    } else {
        resultsBox.html('<td colspan="8" class="text-center text-muted h4">Realice una búsqueda.</td>');
    }
});

// Crea Django Ajax Call
window.submitForms = function(trId, pk) {
    console.log("submitForms called with trId:", trId, "pk:", pk);
    var tr = document.getElementById(trId);
    var tdValues = tr.getElementsByTagName('td');
    var selectValues = tr.getElementsByTagName('select');
    var values = {};
    const addNombre = tdValues[0].innerHTML;
    const addApellido = tdValues[1].innerHTML;
    const addDocumento = tdValues[2].innerHTML;
    const addParentesco = selectValues[0].value;
    const addRelacion = selectValues[1].value;
    const addConviven = selectValues[2].value;
    const addCuidador = selectValues[3].value;

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
                'fk_legajo_1': pk,
                'fk_legajo_2': pk,
                'vinculo': addParentesco,
                'estado_relacion': addRelacion,
                'conviven': addConviven,
                'cuidador_principal': addCuidador,
            },
            dataType: 'json',
            success: function (data) {
                console.log("AJAX success response:", data);
                $("#tablaResultado").append(`
                <div id="familiar-${data.familiar.id} class="col-md-3">
                    <ul class="users-list">
                        <li style="width:auto">
                            ${data.familiar.foto ? `<img src="${mediaUrl}${data.familiar.foto}" alt="User Image" width="60px">` : `<img src="${staticUrl}custom/img/default.png" alt="User Image" width="60px">`}
                            <span class="users-list-name">${data.familiar.apellido}, ${data.familiar.nombre}</span>
                            <span class="users-list-date">${data.familiar.vinculo}</span>
                            <span class="users-list-date"><button
                                class="btn btn-danger btn-sm"
                                onclick='deleteFamiliar("${data.familiar.id}")'
                                type="submit">Eliminar</button></span>
                        </li>
                    </ul>
                </div>
                `);
                $(searchInput).val(""); // Vaciar el campo de búsqueda
                resultsBox.empty(); // Vaciar contenido anterior   
                $('#sin-familiares').remove();
                toastr.options = { "positionClass": "toast-bottom-right",};
                toastr[data.data.tipo_mensaje](data.data.mensaje);
            }
        });
    } else {
        // Mostrar un mensaje de error o realizar alguna acción en caso de campos incompletos
        console.log("Todos los campos deben estar completos");
    }
};

window.deleteFamiliar = function(id) {
    console.log("deleteFamiliar called with id:", id);
    $.ajax({
        url: deleteUrl,
        data: {
            'id': id,
        },
        dataType: 'json',
        success: function (data) {
            console.log("AJAX success response:", data);
            $("#familiar-" + id).remove();
            $('#tablaResultado').load(window.location.href + ' #tablaResultado');
            $(searchInput).val(""); // Vaciar el campo de búsqueda
            resultsBox.empty(); // Vaciar contenido anterior
            resultsBox.append('<td colspan="8" class="text-center text-muted h4">Realice una busqueda.</td>');
            $('#formulario-nuevo')[0].reset();
            formNuevo.addClass('d-none');
            toastr.options = { "positionClass": "toast-bottom-right",};
            toastr[data.tipo_mensaje](data.mensaje);
        }
    });
};

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
form.find('.is-invalid').each(function () {
    hasErrors = true;
    return false; // Salir del bucle si se encuentra un campo inválido
});

if (hasErrors) {
    document.getElementById('nuevo_legajo_familiar').classList.remove('d-none');
} else {
    document.getElementById('nuevo_legajo_familiar').classList.add('d-none');
}
