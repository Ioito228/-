let interval;

async function generateQR() {
    const user = JSON.parse(localStorage.getItem('user'));
    try {
        const res = await fetch(`/api/generate_qr/${user.id}`);
        const data = await res.json();
        const img = document.getElementById('qr-image');
        
        img.src = "data:image/png;base64," + data.qr;
        img.classList.remove('hidden');
        
        let sec = data.expires;
        clearInterval(interval);
        interval = setInterval(() => {
            sec--;
            document.getElementById('timer').innerText = `Обновится через: ${sec}с`;
            if (sec <= 0) { resetQR(); }
        }, 1000);
    } catch (e) { alert("Ошибка связи с сервером"); }
}

function resetQR() {
    clearInterval(interval);
    const img = document.getElementById('qr-image');
    img.src = "";
    img.classList.add('hidden');
    document.getElementById('timer').innerText = "Пропуск аннулирован";
}

// ЗАЩИТА ОТ СКРИНШОТОВ (Visibility API)
document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
        resetQR();
        alert("Безопасность: QR-код удален из памяти устройства.");
    }
});

// ЗАЩИТА: Блюр при потере фокуса окна
window.onblur = () => document.body.classList.add('blur-effect');
window.onfocus = () => document.body.classList.remove('blur-effect');

function logout() {
    localStorage.clear();
    window.location.href = 'login.html';
}