$(document).ready(function() {

    // Mostrar el modal al inicio
    $("#seleccionModal").modal("show");

    // Habilitar botón de confirmación si se selecciona un tipo de organización
    $("#tipoConvenio").change(function() {  // Asegúrate de que este ID es correcto
        $("#confirmarSeleccion").prop("disabled", !$(this).val());
    });

    // Al hacer clic en confirmar, ocultar el modal y actualizar la tabla
    $("#confirmarSeleccion").click(function() {
        var tipo = $("#tipoConvenio").val();  // Asegúrate de que coincide con el select
        if (!tipo) return;

        $("#seleccionModal").modal("hide");
        actualizarTabla(tipo);
    });

});