// Инициализация Sortable и обработчиков
//function initSortableAndHandlers() {
//    const list = document.getElementsByClassName('list-group')[0];
//
//    if (list) {
//        // Инициализация Sortable
//        new Sortable(list, {
//            animation: 150,
//            ghostClass: 'sortable-ghost',
//            chosenClass: 'sortable-chosen',
//            dragClass: 'sortable-drag',
////            onEnd: function() {
////                saveResults();
////            }
//        });
//    }
//}

// Функция сохранения порядка (остаётся без изменений)
//function saveResults() {
//    let a = [...document.querySelectorAll('#result-list li')]
//    const items = a.map((el, index) => ({
//        id: el.id,
//        position: index + 1
//    }));
//    console.warn(items)
//    fetch('/results', {
//        method: 'POST',
//        headers: {'Content-Type': 'application/json'},
//        body: JSON.stringify({data: items})
//    })
//    .then(response => {
//        if (response.ok) {
//           showTempAlert('Порядок сохранён', 'success');
//        }
//        else {
//            throw new Error('Ошибка сохранения');
//        }
//        return response.json();
//    })
//    .catch(error => {
//        console.error('Error:', error);
//        showTempAlert('Ошибка сохранения', 'danger');
//    });
//}


function showTempAlert(message, type) {
    // Remove existing alerts first
    const existingAlerts = document.querySelectorAll('.temp-alert');
    existingAlerts.forEach(alert => alert.remove());

    const alert = document.createElement('div');
    alert.className = `alert alert-${type} position-fixed top-0 end-0 m-3 temp-alert`;
    alert.style.zIndex = '1050';
    alert.textContent = message;
    document.body.appendChild(alert);

    setTimeout(() => {
        alert.remove();
    }, 1000);
}

// Success handler for action buttons
document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.successful && evt.detail.requestConfig.path === "/results") {
        showTempAlert("Результат сохранен", "success");
    }
});

// Инициализация при загрузке и после HTMX-обновлений
//document.addEventListener('DOMContentLoaded', initSortableAndHandlers);
//document.addEventListener('htmx:afterSwap', initSortableAndHandlers);

