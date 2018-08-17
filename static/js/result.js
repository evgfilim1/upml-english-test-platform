$(document).ready(function () {
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        const match = key.match(/u(\d+)-q(\d+)/);
        const value = localStorage.getItem(key);
        if (uploadAnswer(value, match[1])) {
            $(`#q${ match[2] }-a${ value }`).addClass('answered');
            localStorage.removeItem(key);
        }
    }
    $('.answer').addClass('disabled');
    $('.answered').toggleClass('btn-outline-primary btn-danger answered');
    $('.correct').toggleClass('btn-outline-primary btn-success correct');
});