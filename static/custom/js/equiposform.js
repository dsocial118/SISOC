$(document).ready(function () {
    // Función para aplicar estilos de error a los select2 que ya tienen la clase "is-invalid"
    function aplicarEstilosError() {
      $("#form-equipos select.is-invalid").each(function () {
        var select2Container = $(this).next(".select2").find(".select2-selection");
        select2Container.addClass('border-danger');
      });
    }

    // Llamar a la función para aplicar estilos de error al cargar la página
    aplicarEstilosError();

  });