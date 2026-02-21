// static/script.js - Только для главной страницы

class RaffleGame {
    constructor() {
        // Элементы формы регистрации
        this.nicknameInput = document.getElementById('nickname');
        this.telegramInput = document.getElementById('telegram');
        this.siteUrlInput = document.getElementById('siteUrl');
        this.registerBtn = document.getElementById('registerBtn');
        
        // Элемент для сообщений
        this.messageDiv = document.getElementById('message');
        
        // Элемент для публичных победителей
        this.publicWinnersDiv = document.getElementById('publicWinners');
        
        // Инициализация
        this.init();
    }
    
    async init() {
        // Загружаем публичных победителей
        await this.loadPublicWinners();
        
        // Вешаем обработчик на кнопку регистрации
        this.registerBtn.addEventListener('click', () => this.handleRegister());
    }
    
    async handleRegister() {
        const nickname = this.nicknameInput.value.trim();
        const telegram = this.telegramInput.value.trim();
        const siteUrl = this.siteUrlInput.value.trim();
        
        // Проверка обязательного поля
        if (!nickname) {
            this.showMessage('Введите никнейм', 'error');
            return;
        }
        
        // Проверка, что заполнено хотя бы одно из двух полей
        if (!telegram && !siteUrl) {
            this.showMessage('Заполните Telegram или ссылку на профиль', 'error');
            return;
        }
        
        // Форматируем Telegram (добавляем @ если нет)
        let formattedTelegram = telegram;
        if (telegram && !telegram.startsWith('@')) {
            formattedTelegram = '@' + telegram;
        }
        
        this.registerBtn.disabled = true;
        this.registerBtn.textContent = 'Обработка...';
        
        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    nickname: nickname,
                    telegram: formattedTelegram || null,
                    site_url: siteUrl || null
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Сохраняем пользователя в localStorage
                localStorage.setItem('shadowUser', JSON.stringify(data.user));
                
                // Показываем сообщение об успехе
                this.showMessage(data.new_user ? 'Регистрация успешна!' : 'Добро пожаловать обратно!', 'success');
                
                // Перенаправляем на страницу игры через 1 секунду
                setTimeout(() => {
                    window.location.href = '/game';
                }, 1000);
            } else {
                this.showMessage(data.message, 'error');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            this.showMessage('Ошибка соединения с сервером', 'error');
        } finally {
            this.registerBtn.disabled = false;
            this.registerBtn.textContent = '🌑 Войти в тень 🌑';
        }
    }
    
    async loadPublicWinners() {
        try {
            const response = await fetch('/api/public-winners');
            const data = await response.json();
            
            if (this.publicWinnersDiv && data.success && data.winners.length > 0) {
                this.publicWinnersDiv.innerHTML = data.winners.map(w => `
                    <div class="winner-item">
                        <span class="nickname">${w.nickname}</span>
                        <span class="prize">${w.prize_name}</span>
                        <span class="date">${new Date(w.won_at).toLocaleDateString()}</span>
                    </div>
                `).join('');
            } else if (this.publicWinnersDiv) {
                this.publicWinnersDiv.innerHTML = '<p>Пока нет победителей</p>';
            }
        } catch (error) {
            console.error('Ошибка загрузки победителей:', error);
        }
    }
    
    showMessage(text, type) {
        console.log(`📢 Сообщение: ${text}, тип: ${type}`);
        this.messageDiv.textContent = text;
        this.messageDiv.className = `message message-${type}`;
        this.messageDiv.style.display = 'block';
        
        // Автоматически скрываем через 3 секунды
        setTimeout(() => {
            this.messageDiv.style.display = 'none';
        }, 3000);
    }
}

// Запускаем только на главной странице
if (window.location.pathname === '/') {
    document.addEventListener('DOMContentLoaded', () => {
        new RaffleGame();
    });
}