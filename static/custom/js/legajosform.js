$(document).ready(function() {
    $('#id_nacionalidad').select2();
});

id_foto.onchange = (evt) => {
    const [file] = id_foto.files;
    if (file) {
        blah.src = URL.createObjectURL(file);
    }
};