document.body.addEventListener('htmx:afterRequest', function (evt) {
    const errorTarget = document.getElementById("htmx-alert")
    if (evt.detail.successful) {
        // Successful request, clear out alert
        errorTarget.setAttribute("hidden", "true")
        errorTarget.innerText = "";
    } else if (evt.detail.xhr.status === 422) {
        const xhr = evt.detail.xhr;
        errorTarget.innerText = `Ошибка валидации: ${JSON.parse(xhr.responseText).detail}`;
        errorTarget.removeAttribute("hidden");
        errorTarget.focus();
    }
    else if (evt.detail.xhr.status === 400) {
        const xhr = evt.detail.xhr;
        errorTarget.innerText = `Невозможно совершить операцию: ${JSON.parse(xhr.responseText).error.message}`;
        errorTarget.removeAttribute("hidden");
        errorTarget.focus();
    }
    else if (evt.detail.failed && evt.detail.xhr) {
        // Server error with response contents, equivalent to htmx:responseError
        console.warn("Server error", evt.detail)
        const xhr = evt.detail.xhr;
        errorTarget.innerText = `Unexpected server error: ${xhr.status} - ${xhr.statusText};`;
        errorTarget.removeAttribute("hidden");
        errorTarget.focus();
    } else {
        // Unspecified failure, usually caused by network error
        console.error("Unexpected htmx error", evt.detail)
        errorTarget.innerText = "Unexpected error, check your connection and try to refresh the page.";
        errorTarget.removeAttribute("hidden");
    }
});