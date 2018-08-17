function uploadAnswer(answer_id, user_id=null) {
    let success = true;
    let data = {'a': answer_id};
    if (user_id !== null) {
        data['u'] = user_id
    }
    $.post({
        url: '/api/answer',
        'data': data,
        error: function () {
            console.warn('Failed to upload answer ' + answer_id);
            success = false;
        }
    });
    return success;
}

$('textarea').on('input', function (){
    $(this).height(0).height(this.scrollHeight);
});

$(document).ready(function () {
    $('textarea').trigger('input');
});
