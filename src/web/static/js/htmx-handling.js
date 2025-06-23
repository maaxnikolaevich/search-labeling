// Constants
const ALERT_DISPLAY_TIME = 5000; // 2 seconds
const ERROR_MESSAGES = {
    422: (xhr) => `Ошибка валидации: ${JSON.parse(xhr.responseText).detail}`,
    400: (xhr) => `Невозможно совершить операцию: ${JSON.parse(xhr.responseText).error.message}`,
    default: (xhr) => `Unexpected server error: ${xhr.status} - ${xhr.statusText}`
};

// Alert management functions
function showAlert(message, type = 'danger') {
    const errorTarget = document.getElementById("htmx-alert");
    if (!errorTarget) return;

    errorTarget.innerText = message;
    errorTarget.classList.remove('alert-success', 'alert-danger');
    errorTarget.classList.add(`alert-${type}`);
    errorTarget.removeAttribute("hidden");
    errorTarget.focus();

    // Auto-hide after delay
    setTimeout(() => hideAlert(errorTarget), ALERT_DISPLAY_TIME);
}

function hideAlert(alertElement) {
    if (!alertElement) return;
    alertElement.setAttribute("hidden", "true");
    alertElement.innerText = "";
}

// Error handling function
function handleError(evt) {
    const xhr = evt.detail.xhr;

    if (!xhr) {
        showAlert("Unexpected error, check your connection and try to refresh the page.");
        return;
    }

    const errorHandler = ERROR_MESSAGES[xhr.status] || ERROR_MESSAGES.default;
    showAlert(errorHandler(xhr));

    if (evt.detail.failed) {
        console.warn("Server error", evt.detail);
    }
}

// Main event listener
document.body.addEventListener('htmx:afterRequest', function(evt) {
    const errorTarget = document.getElementById("htmx-alert");
    if (!errorTarget) return;

    if (evt.detail.xhr.status >= 200 && evt.detail.xhr.status < 300) {
        hideAlert(errorTarget);
    } else {
        handleError(evt);
    }
});

document.body.addEventListener('htmx:afterSwap', function(evt) {
var firstResult = document.querySelector('.list-group-item');
if (firstResult) {
  firstResult.focus();
}
});