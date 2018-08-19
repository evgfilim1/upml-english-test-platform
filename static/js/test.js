let remaining = 0;

function counter() {
    let min = Math.floor(remaining / 60);
    let sec = remaining % 60;
    if (min < 10) {
        min = `0${min}`
    }
    if (sec < 10) {
        sec = `0${sec}`
    }
    const t = `${min}:${sec}`;
    $('#remaining').text(t);
    if (--remaining >= 0) {
        setTimeout(counter, 1000);
    } else {
        $('#finish-test').submit()
    }
}

function worker() {
    $('.answered')
        .removeClass('btn-outline-primary')
        .addClass('btn-primary');
    setTimeout(worker, 500);
}

$(document).ready(function () {
    remaining = $('#remaining').text();
    counter();
    uploadAllAnswers();
    worker();
});

$('.answer').click(function () {
    const user_id = new URL(window.location.href).searchParams.get('u');
    const match = this.id.match(/q(\d+)-a(\d+)/);
    let other = $('.answered').filter(function () {
        return this.id !== '' && this.id.startsWith('q' + match[1])
    });
    other.removeClass('btn-primary answered');
    other.addClass('btn-outline-primary');

    uploadAnswer(match[2], user_id, match[1]);
    $(this).addClass('answered') // Don't confuse user when there is no connection
});

$('#finish-test').submit(function () {
    uploadAllAnswers()
});
