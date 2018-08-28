function destructive_confirm(ev) {
    if (!confirm('Это — деструктивная операция. Продолжить?')) {
        ev.preventDefault();
        ev.stopPropagation();
    }
}

$('textarea').on('input', function (){
    $(this)
        .height(0)
        .height(this.scrollHeight);
});

$(document).ready(function () {
    $('textarea').trigger('input');
});

$('a.destructive-confirm').click(destructive_confirm);
$('form.destructive-confirm').submit(destructive_confirm);

$('a.js-scroll').click(function (ev) {
    ev.preventDefault();
    ev.stopPropagation();
    const id = $(this).attr('href');
    const elem = $(id);
    // const elem = document.querySelector(id);
    // $('html, body').scrollTop(elem.offset().top - document.querySelector('#main-nav').scrollHeight);
    $('html, body').animate({
        scrollTop: elem.offset().top - document.querySelector('#main-nav').scrollHeight
    }, 500);
});

$('#noscript').hide();
