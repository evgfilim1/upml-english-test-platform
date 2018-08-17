$(document).ready(function () {
    $('.correct').toggleClass('btn-outline-primary btn-success');
});

$('.answer').click(function () {
    const match = this.id.match(/q(\d+)-a(\d+)/);
    let other = $('.correct').filter(function () {
        return this.id !== '' && this.id.startsWith('q' + match[1])
    });
    const that = this;

    $.post({
        url: '/api/admin/question',
        data: {'q': match[1], 'r': match[2]},
        success: function () {
            other.removeClass('btn-success correct');
            other.addClass('btn-outline-primary');
            $(that).toggleClass('btn-outline-primary btn-success correct');
        }
    })
});