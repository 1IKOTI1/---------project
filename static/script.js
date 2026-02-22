// static/script.js - Только для главной страницы

class RaffleGame {
    constructor() {
        // Элементы формы входа
        this.loginNickname = document.getElementById('loginNickname');
        this.loginPassword = document.getElementById('loginPassword');
        this.loginBtn = document.getElementById('loginBtn');
        
        // Элементы формы регистрации
        this.regNickname = document.getElementById('regNickname');
        this.regPassword = document.getElementById('regPassword');
        this.regConfirmPassword = document.getElementById('regConfirmPassword');
        this.regTelegram = document.getElementById('regTelegram');
        this.regSiteUrl = document.getElementById('regSiteUrl');
        this.registerBtn = document.getElementById('registerBtn');
        
        // Элемент для сообщений
        this.messageDiv = document.getElementById('message');
        
        // Элемент для публичных победителей
        this.publicWinnersDiv = document.getElementById('publicWinners');
        
        // Счетчик для ника
        this.nicknameCounter = document.getElementById('nicknameCounter');
        
        // Инициализация
        this.init();
    }
    
    async init() {
        await this.loadPublicWinners();
        
        this.loginBtn.addEventListener('click', () => this.handleLogin());
        this.registerBtn.addEventListener('click', () => this.handleRegister());
        
        // Добавляем возможность входа по Enter
        this.loginPassword.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleLogin();
        });
        
        // Инициализация счетчика ника
        this.initNicknameCounter();
    }
    
    initNicknameCounter() {
        if (this.regNickname && this.nicknameCounter) {
            this.regNickname.addEventListener('input', () => {
                const length = this.regNickname.value.length;
                this.nicknameCounter.textContent = `${length}/20`;
                
                if (length > 20) {
                    this.nicknameCounter.style.color = '#ff4444';
                    this.nicknameCounter.classList.add('danger');
                } else if (length > 15) {
                    this.nicknameCounter.style.color = '#ffaa00';
                    this.nicknameCounter.classList.add('warning');
                } else {
                    this.nicknameCounter.style.color = '#8080a0';
                    this.nicknameCounter.classList.remove('warning', 'danger');
                }
            });
            
            // Первоначальное обновление
            this.nicknameCounter.textContent = `0/20`;
        }
    }
    
    async handleLogin() {
        const nickname = this.loginNickname.value.trim();
        const password = this.loginPassword.value;
        
        if (!nickname || !password) {
            this.showMessage('Введите никнейм и пароль', 'error');
            return;
        }
        
        // Проверка длины ника
        if (nickname.length < 3) {
            this.showMessage('Никнейм должен быть не менее 3 символов', 'error');
            return;
        }
        
        if (nickname.length > 20) {
            this.showMessage('Никнейм должен быть не более 20 символов', 'error');
            return;
        }
        
        this.loginBtn.disabled = true;
        this.loginBtn.textContent = 'Вход...';
        
        try {
            const response = await fetch('/api/login_with_password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    nickname: nickname,
                    password: password 
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                localStorage.setItem('shadowUser', JSON.stringify(data.user));
                this.showMessage('Успешный вход!', 'success');
                
                setTimeout(() => {
                    window.location.href = '/game';
                }, 1000);
            } else {
                this.showMessage(data.message, 'error');
                this.loginPassword.value = '';
            }
        } catch (error) {
            this.showMessage('Ошибка соединения с сервером', 'error');
        } finally {
            this.loginBtn.disabled = false;
            this.loginBtn.textContent = '🔐 Войти';
        }
    }
    
    async handleRegister() {
        const nickname = this.regNickname.value.trim();
        const password = this.regPassword.value;
        const confirmPassword = this.regConfirmPassword.value;
        const telegram = this.regTelegram.value.trim();
        const siteUrl = this.regSiteUrl.value.trim();
        
        // Проверки
        if (!nickname) {
            this.showMessage('Введите никнейм', 'error');
            return;
        }
        
        // Проверка длины ника
        if (nickname.length < 3) {
            this.showMessage('Никнейм должен быть не менее 3 символов', 'error');
            return;
        }
        
        if (nickname.length > 20) {
            this.showMessage('Никнейм должен быть не более 20 символов', 'error');
            return;
        }
        
        if (!password || password.length < 4) {
            this.showMessage('Пароль должен быть не менее 4 символов', 'error');
            return;
        }
        
        if (password !== confirmPassword) {
            this.showMessage('Пароли не совпадают', 'error');
            return;
        }
        
        if (!telegram && !siteUrl) {
            this.showMessage('Заполните Telegram или ссылку на профиль', 'error');
            return;
        }
        
        // Форматируем Telegram
        let formattedTelegram = telegram;
        if (telegram && !telegram.startsWith('@')) {
            formattedTelegram = '@' + telegram;
        }
        
        this.registerBtn.disabled = true;
        this.registerBtn.textContent = 'Регистрация...';
        
        try {
            const response = await fetch('/api/register_with_password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    nickname: nickname,
                    password: password,
                    telegram: formattedTelegram || null,
                    site_url: siteUrl || null
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                localStorage.setItem('shadowUser', JSON.stringify(data.user));
                this.showMessage('Регистрация успешна!', 'success');
                
                setTimeout(() => {
                    window.location.href = '/game';
                }, 1000);
            } else {
                this.showMessage(data.message, 'error');
                
                // Подсвечиваем проблемное поле
                if (data.message.includes('Никнейм')) {
                    this.regNickname.classList.add('input-error');
                } else if (data.message.includes('Telegram')) {
                    this.regTelegram.classList.add('input-error');
                } else if (data.message.includes('ссылк')) {
                    this.regSiteUrl.classList.add('input-error');
                }
            }
        } catch (error) {
            this.showMessage('Ошибка соединения с сервером', 'error');
        } finally {
            this.registerBtn.disabled = false;
            this.registerBtn.textContent = '📝 Зарегистрироваться';
        }
    }
    
    async loadPublicWinners() {
        try {
            const response = await fetch('/api/public-winners');
            const data = await response.json();
            
            if (this.publicWinnersDiv && data.success) {
                if (data.winners.length > 0) {
                    this.publicWinnersDiv.innerHTML = data.winners.map(w => `
                        <div class="winner-item">
                            <span class="nickname">${w.nickname}</span>
                            <span class="prize">${w.prize_name}</span>
                            <span class="date">${new Date(w.won_at).toLocaleDateString()}</span>
                        </div>
                    `).join('');
                } else {
                    this.publicWinnersDiv.innerHTML = '<p>Пока нет победителей</p>';
                }
            }
        } catch (error) {
            console.error('Ошибка загрузки победителей:', error);
        }
    }
    
    showMessage(text, type) {
        this.messageDiv.textContent = text;
        this.messageDiv.className = `message message-${type}`;
        this.messageDiv.style.display = 'block';
        
        setTimeout(() => {
            this.messageDiv.style.display = 'none';
        }, 3000);
    }
}

// Запускаем только на главной странице - ОДИН РАЗ
if (window.location.pathname === '/') {
    document.addEventListener('DOMContentLoaded', () => {
        new RaffleGame();
    });
}