const csrf = document.getElementsByName('csrfmiddlewaretoken')[0].value;

if (!csrf) {
    console.error("CSRF token not found");   
}

const searchInput = $("#legajoListSearchInput");

$('#legajoListBuscar').on('click', function(event) {
    event.preventDefault();
    // Aquí puedes agregar el código que deseas ejecutar cuando se presiona el elemento
    sendSearchData(searchInput.val());
});

const sendSearchData = (busqueda, pageNumber = 1) => {
    //$('#loadingIndicator').show();
    $.ajax({
        type: 'GET',
        url: `${legajosListar}?busqueda=${busqueda}&page=${pageNumber}`,  // Pasar parámetros en la URL
        /*data: {
            'csrfmiddlewaretoken': csrf,
            'busqueda': busqueda,
            'page': pageNumber,
        },*/
        success: (res) => {
            console.log("Search success", res);
            const data = res.data;
            if (Array.isArray(data)) {
                console.log(data);
                /*
                resultsBox.empty(); // Vaciar contenido anterior
                data.forEach(r => {
                    resultsBox.append(`
                        <tr id="id_tr${r.pk}">
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
                    
                });*/
                formNuevo.addClass('d-none');
            } else {/*
                if (searchInput.value.length > 0) {
                    resultsBox.empty(); // Vaciar contenido anterior
                    formNuevo.removeClass('d-none');
                } else {
                    formNuevo.addClass('d-none')
                }*/
            }
            //updatePaginationControls(res.data);
            //$('#loadingIndicator').hide();
        },
        error: (err) => {
            console.log("Error: ", err);
        }
    });
};