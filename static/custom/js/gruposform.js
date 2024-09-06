$('#btn-submit').click(function(){
    let nombre =  ( $('#id_programa').find(":selected").text())+' '+($('#id_permiso').find(":selected").text())
    $('#id_name').val(nombre)
    $( "#target" ).trigger( "submit" );
});