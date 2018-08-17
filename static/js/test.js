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

$(document).ready(function () {
    remaining = $('#remaining').text();
    counter();
    $('.answered').toggleClass('btn-outline-primary btn-primary answered')
});

$('.answer').click(function () {
    const user_id = new URL(window.location.href).searchParams.get('u');
    const match = this.id.match(/q(\d+)-a(\d+)/);
    let other = $('.answer').filter(function () {
        return this.id !== '' && this.id.startsWith('q' + match[1])
    });
    other.removeClass('btn-primary');
    other.addClass('btn-outline-primary');
    $(this).toggleClass('btn-outline-primary btn-primary');

    if (!uploadAnswer(match[2])) {
        localStorage.setItem(`u${user_id}-q${match[1]}`, match[2]);
    }
});

$('#finish-test').submit(function () {
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        const match = key.match(/u(\d+)-q\d+/);
        const value = localStorage.getItem(key);
        if (uploadAnswer(value, match[1])) {
            localStorage.removeItem(key);
        }
    }
});
