function uploadAnswer(answer_id, user_id, question_id) {
    /**
     * Upload answer with id=answer_id as user with id=user_id and mark it as answered (UI).
     * If the uploading fails, save the answer to upload later.
     */
    let data = {'a': answer_id, 'u': user_id};
    $.post({
        url: '/api/answer',
        'data': data,
        success: function () {
            console.debug(`Uploaded answer (id=${answer_id})`);
            $(`#q${question_id}-a${answer_id}`).addClass('answered');
            localStorage.removeItem(`u${user_id}-q${question_id}`);
        },
        error: function () {
            console.warn(`Failed to upload answer (id=${answer_id})`);
            localStorage.setItem(`u${user_id}-q${question_id}`, answer_id);
        }
    });
}


function uploadAllAnswers() {
    let keys = [];
    for (let i = 0; i < localStorage.length; i++) {
        keys.push(localStorage.key(i));
    }
    for (let i in keys) {
        const key = keys[i];
        const match = key.match(/u(\d+)-q(\d+)/);
        const value = localStorage.getItem(key);
        uploadAnswer(value, match[1], match[2]);
    }
}

function destructive_confirm(ev) {
    if (!confirm('Это — деструктивная операция. Продолжить?')) {
        ev.preventDefault();
        ev.stopPropagation();
    }
}

$('textarea').on('input', function (){
    $(this).height(0).height(this.scrollHeight);
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
