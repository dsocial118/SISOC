$(document).ready(function () {
    // when user clicks add more btn of variants
    $('.add-variants').click(function (ev) {
      ev.preventDefault();
      var count = $('#item-variants').children().length;
      var tmplMarkup = $('#variants-template').html();
      var compiledTmpl = tmplMarkup.replace(/__prefix__/g, count);
      $('#item-variants').append(compiledTmpl);
      // update form count
      $('#id_variants-TOTAL_FORMS').attr('value', count + 1);
    });

    $('body').on('click', '.borrar_tr', function () {
      $(this).parent().parent().remove();

    });


    // Disable form submissions if there are invalid fields
    (function () {
      'use strict';
      window.addEventListener('load', function () {
        // Get the forms we want to add validation styles to
        var forms = document.getElementsByClassName('needs-validation');
        // Loop over them and prevent submission
        var validation = Array.prototype.filter.call(forms, function (form) {
          form.addEventListener('submit', function (event) {
            if (form.checkValidity() === false) {
              event.preventDefault();
              event.stopPropagation();
            }
            form.classList.add('was-validated');
          }, false);
        });
      }, false);
    })();

    $(function () {
      //Initialize Select2 Elements
      $('.select2').select2()

      //Initialize Select2 Elements
      $('.select2bs4').select2({
        theme: 'bootstrap4'
      })
    });

  });