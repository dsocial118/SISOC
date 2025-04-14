$(document).ready(function () {
    $('.tipo_intervencion-select').change(function () {
        var estadoId = $(this).val();
        $.ajax({
            url: ajaxLoadSubIntervenciones,
            data: {
                'id': estadoId
            },
            success: function (data) {
                var $subIntervencion = $('.subintervencion-select');
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