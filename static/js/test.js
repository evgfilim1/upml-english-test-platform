let remaining = 0;

function uploadAnswer(answer_id, question_id) {
    /**
     * Upload answer with id=answer_id and mark it as answered (UI).
     * If the uploading fails, save the answer to upload later.
     */
    $.post({
        url: '/api/answer',
        data: {'a': answer_id},
        success: function () {
            console.debug(`Uploaded answer (id=${answer_id})`);
            $(`#q${question_id}-a${answer_id}`).addClass('answered');
            localStorage.removeItem(`q${question_id}`);
        },
        error: function (jqxhr) {
            if (jqxhr.status === 400 && jqxhr.responseJSON !== undefined) {
                const r = jqxhr.responseJSON;
                if (r.ok === false && 1 <= r.error_code && r.error_code <= 3) {
                    console.warn(`Failed to upload answer (id=${answer_id}): ${r.error}`);
                    if (r.error_code === 1) {
                        location.reload(true);
                    } else if (r.error_code === 3) {
                        $('#finish-test').submit();
                    }
                    return;
                }
            }
            console.warn(
                `Failed to upload answer (id=${answer_id}): ${jqxhr.status} ${jqxhr.statusText}`
            );
            localStorage.setItem(`q${question_id}`, answer_id);
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
        const match = key.match(/q(\d+)/);
        const value = localStorage.getItem(key);
        uploadAnswer(value, match[1]);
    }
}

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

function autoUploader() {
    uploadAllAnswers();
    setTimeout(autoUploader, 5000);
}

$(document).ready(function () {
    remaining = $('#remaining').text();
    counter();
    autoUploader();
    worker();
});

$('.answer').click(function () {
    if ($(this).hasClass('answered')) {
        return // Don't resend the same answer
    }
    const match = this.id.match(/q(\d+)-a(\d+)/);
    let other = $('.answered').filter(function () {
        return this.id !== '' && this.id.startsWith('q' + match[1])
    });
    other.removeClass('btn-primary answered');
    other.addClass('btn-outline-primary');

    uploadAnswer(match[2], match[1]);
    $(this).addClass('answered') // Don't confuse user when there is no connection
});
