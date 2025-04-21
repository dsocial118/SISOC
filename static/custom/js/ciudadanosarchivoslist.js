function deleteArchivo(id) {
    $.ajax({

        // Función Ajax para eliminar la archivos
        url: deleteUrl,
        data: {
            'id': id,
        },
        dataType: 'json',
        success: function (data) {
            if (data.deleted) {
                $("#tr-" + id).remove();
                toastr.options = { "positionClass": "toast-bottom-right", }
                toastr[data.tipo_mensaje](data.mensaje);
            }
        },
        error: (err) => {
            toastr.options = { "positionClass": "toast-bottom-right", }
            toastr["Error"](err);
        }
    });
};