$(document).ready(function () {
    // Inicializar los campos de Select2
    $('.select2').select2();

    // Evento para actualizar las opciones de Alertas al seleccionar una Categoría
    $('#id_fk_categoria').on('change', function () {
        let categoria_id = $(this).val();
        let alerta_select = $('#id_fk_alerta');
        let categoria_select = $('#id_fk_categoria');
        // Encontrar el elemento span con clase 'select2-selection' que es el contenedor del select2 de cada elemento
        let alerta_select2Container = alerta_select.next(".select2").find(".select2-selection");
        let categoria_select2Container = categoria_select.next(".select2").find(".select2-selection");

        ocultarMensajesError(alerta_select, alerta_select2Container)
        ocultarMensajesError(categoria_select, categoria_select2Container)

        $.getJSON(alertasSelectUrl, { categoria_id: categoria_id }, function (data) {
            alerta_select.empty();
            // Agregar una opción vacía al inicio
            alerta_select.append('<option value="">---------</option>');
            $.each(data, function (index, option) {
                alerta_select.append(new Option(option.text, option.id, true, true));
            });
            alerta_select.val(""); // Restablecer el valor del campo de Alerta
        });
    });

    // Evento para actualizar las opciones de Categoría al cambiar el campo de Alerta
    $('#id_fk_alerta').on('change', function () {
        let alerta_id = $(this).val();
        let alerta_select = $('#id_fk_alerta');
        let categoria_select = $('#id_fk_categoria');
        // Encontrar el elemento span con clase 'select2-selection' que es el contenedor del select2 de cada elemento
        let alerta_select2Container = alerta_select.next(".select2").find(".select2-selection");
        let categoria_select2Container = categoria_select.next(".select2").find(".select2-selection");

        ocultarMensajesError(alerta_select, alerta_select2Container)
        ocultarMensajesError(categoria_select, categoria_select2Container)

        $.getJSON(categoriasSelectUrl, { alerta_id: alerta_id }, function (data) {
            categoria_select.empty();
            // Agregar una opción vacía al inicio
            categoria_select.append('<option value="">---------</option>');
            $.each(data, function (index, option) {
                categoria_select.append(new Option(option.text, option.id, true, true));
            });
            if (alerta_id === "") {
                categoria_select.val(""); // Restablecer el valor del campo de Categoría
            }
        });
    });

    // Función para ocultar los mensajes de error
    function ocultarMensajesError(select, selectContainer) {
        select.removeClass('is-invalid');
        select.parent().find('p').hide();
        selectContainer.removeClass('border-danger');
    }

    // Escuchar clics en los botones de eliminar
    $(".eliminar-alerta-btn").click(function () {
        let alertaId = $(this).data("alerta-id");
        $.ajax({
            // Función Ajax para eliminar la alerta
            url: alertaAjaxBorrarUrl,
            data: {
                'id': alertaId,
            },
            dataType: 'json',
            success: function (data) {
                if (data.deleted) {
                    $("#alerta-" + alertaId).remove();
                    toastr.options = { "positionClass": "toast-bottom-right",}
                    toastr[data.tipo_mensaje](data.mensaje);
                }
            }
        });
    });

    // Función para aplicar estilos de error a los select2 que ya tienen la clase "is-invalid"
    function aplicarEstilosError() {
        $("#agregarAlerta select.is-invalid").each(function() {
            var select2Container = $(this).next(".select2").find(".select2-selection");
            select2Container.addClass('border-danger');
        });
    }

    // Llamar a la función para aplicar estilos de error al cargar la página
    aplicarEstilosError();
});