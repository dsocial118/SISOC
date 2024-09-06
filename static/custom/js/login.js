setTimeout(function () {
    // desaparecer los Success messages
    $(".alert").alert('close');
}, 3000);

//popovers
$(function () {
    $('[data-toggle="popover"]').popover()
})
$('.popover-dismiss').popover({
    trigger: 'focus'
});