function onclick_f() {
    const is_admin = $('.is-admin');
    if ($('#show-admins').prop('checked')) {
        is_admin.removeClass('d-none');
        is_admin.addClass('d-flex');
    } else {
        is_admin.addClass('d-none');
        is_admin.removeClass('d-flex');
    }
}

$('#show-admins').click(onclick_f);

$(document).ready(function () {
    onclick_f();
});
