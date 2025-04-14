$(document).ready(function () {
    $('.tipo_llamado-select').change(function () {
        var estadoId = $(this).val();
        $.ajax({
            url: ajaxLoadSubLlamados,
            data: {
                'id': estadoId
            },
            success: function (data) {
                var $subIntervencion = $('.subtipo_llamado-select');
                $subIntervencion.empty();
                $.each(data, function (index, item) {
                    $subIntervencion.append($('<option>', {
                        value: item.id,
                        text: item.text
                    }));
                });
            }
        });
    });

    $('.programasllamado-select').change(function () {
        var estadoId = $(this).val();
        $.ajax({
            url: ajaxLoadLlamadosTipos,
            data: {
                'id': estadoId
            },
            success: function (data) {
                var $subIntervencion = $('.tipo_llamado-select');
                $subIntervencion.empty();
                $.each(data, function (index, item) {
                    $subIntervencion.append($('<option>', {
                        value: item.id,
                        text: item.text
                    }));
                });
            }
        });
    });
});