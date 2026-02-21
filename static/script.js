class RaffleGame {
    constructor() {
        // Элементы формы регистрации
        this.nicknameInput = document.getElementById('nickname');
        this.telegramInput = document.getElementById('telegram');
        this.siteUrlInput = document.getElementById('siteUrl');
        this.registerBtn = document.getElementById('registerBtn');
        
        // Элементы информации о пользователе
        this.userInfo = document.getElementById('userInfo');
        this.displayNickname = document.getElementById('displayNickname');
        this.displayTelegram = document.getElementById('displayTelegram');
        this.displaySiteUrl = document.getElementById('displaySiteUrl');
        this.coinBalance = document.getElementById('coinBalance');
        
        // Элементы розыгрыша
        this.raffleSection = document.getElementById('raffleSection');
        this.prizesGrid = document.getElementById('prizesGrid');
        this.drawButton = document.getElementById('drawButton');
        
        // Общие элементы
        this.messageDiv = document.getElementById('message');
        this.winnersTable = document.getElementById('winnersTable');
        
        // Данные пользователя
        this.currentUser = null;
        
        // Загружаем сохраненные данные из localStorage
        this.loadSavedUser();
        
        // Инициализация
        this.init();
    }
    
    loadSavedUser() {
        const savedUser = localStorage.getItem('raffleUser');
        if (savedUser) {
            try {
                this.currentUser = JSON.parse(savedUser);
                console.log('👤 Загружен сохраненный пользователь:', this.currentUser);
            } catch (e) {
                console.error('Ошибка загрузки сохраненного пользователя');
            }
        }
    }
    
    saveUser(userData) {
        this.currentUser = userData;
        localStorage.setItem('raffleUser', JSON.stringify(userData));
        this.updateUserDisplay();
    }
    
    updateUserDisplay() {
        if (this.currentUser) {
            this.userInfo.style.display = 'block';
            this.raffleSection.style.display = 'block';
            this.displayNickname.textContent = this.currentUser.nickname;
            this.displayTelegram.textContent = this.currentUser.telegram ? `📱 ${this.currentUser.telegram}` : '';
            this.displaySiteUrl.textContent = this.currentUser.site_url ? `🔗 ${this.currentUser.site_url}` : '';
            this.coinBalance.textContent = this.currentUser.coins;
        } else {
            this.userInfo.style.display = 'none';
            this.raffleSection.style.display = 'none';
        }
    }
    
    async init() {
        await this.loadPrizes();
        await this.loadWinners();
        
        this.registerBtn.addEventListener('click', () => this.handleRegister());
        this.drawButton.addEventListener('click', () => this.handleDraw());
        
        // Если есть сохраненный пользователь, показываем его данные
        if (this.currentUser) {
            this.updateUserDisplay();
        }
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
                this.saveUser(data.user);
                this.showMessage(data.new_user ? 'Регистрация успешна!' : 'Добро пожаловать обратно!', 'success');
                this.clearRegisterForm();
                await this.loadPrizes();
            } else {
                this.showMessage(data.message, 'error');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            this.showMessage('Ошибка соединения с сервером', 'error');
        } finally {
            this.registerBtn.disabled = false;
            this.registerBtn.textContent = 'Войти / Зарегистрироваться';
        }
    }
    
    clearRegisterForm() {
        this.nicknameInput.value = '';
        this.telegramInput.value = '';
        this.siteUrlInput.value = '';
    }
    
    async handleDraw() {
        if (!this.currentUser) {
            this.showMessage('Сначала войдите в систему', 'error');
            return;
        }
        
        this.drawButton.disabled = true;
        this.drawButton.textContent = 'Крутим...';
        
        try {
            const response = await fetch('/api/draw', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ user_id: this.currentUser.id })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Обновляем баланс пользователя
                this.currentUser.coins = data.new_balance;
                this.saveUser(this.currentUser);
                
                this.showMessage(data.message, 'success');
                await this.loadPrizes();
                await this.loadWinners();
            } else {
                this.showMessage(data.message, 'error');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            this.showMessage('Ошибка соединения с сервером', 'error');
        } finally {
            this.drawButton.disabled = false;
            this.drawButton.textContent = '🎲 Крутить рулетку 🎲';
        }
    }
    
    async loadPrizes() {
        try {
            const response = await fetch('/api/prizes');
            const data = await response.json();
            
            if (data.success) {
                this.renderPrizes(data.prizes);
            }
        } catch (error) {
            this.showMessage('Ошибка загрузки карт', 'error');
        }
    }
    
    renderPrizes(prizes) {
        this.prizesGrid.innerHTML = '';
        
        if (prizes.length === 0) {
            this.prizesGrid.innerHTML = '<p class="no-prizes">Все карты разыграны!</p>';
            return;
        }
        
        prizes.forEach(prize => {
            const card = document.createElement('div');
            card.className = 'prize-card';
            card.innerHTML = `
                <img src="/static/images/${prize.image}" alt="${prize.name}">
                <h3>${prize.name}</h3>
                <p>${prize.description || ''}</p>
                <div class="prize-price">💰 ${prize.price} монет</div>
            `;
            this.prizesGrid.appendChild(card);
        });
    }
    
    async loadWinners() {
        try {
            const response = await fetch('/api/winners');
            const data = await response.json();
            
            if (data.success) {
                this.renderWinners(data.winners);
            }
        } catch (error) {
            console.error('Ошибка загрузки победителей:', error);
        }
    }
    
    renderWinners(winners) {
        this.winnersTable.innerHTML = '';
        
        if (winners.length === 0) {
            this.winnersTable.innerHTML = '<p>Пока нет победителей</p>';
            return;
        }
        
        const table = document.createElement('table');
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Никнейм</th>
                    <th>Telegram</th>
                    <th>Ссылка</th>
                    <th>Приз</th>
                    <th>Дата</th>
                </tr>
            </thead>
            <tbody>
                ${winners.map(w => `
                    <tr>
                        <td>${w.nickname}</td>
                        <td>${w.telegram || '-'}</td>
                        <td>${w.site_url ? `<a href="${w.site_url}" target="_blank">Профиль</a>` : '-'}</td>
                        <td>${w.prize_name}</td>
                        <td>${new Date(w.won_at).toLocaleString()}</td>
                    </tr>
                `).join('')}
            </tbody>
        `;
        
        this.winnersTable.appendChild(table);
    }
    
    showMessage(text, type) {
        console.log(`📢 Сообщение: ${text}, тип: ${type}`);
        this.messageDiv.textContent = text;
        this.messageDiv.className = `message message-${type}`;
        this.messageDiv.style.display = 'block';
        
        // Автоматически скрываем через 5 секунд
        setTimeout(() => {
            this.messageDiv.style.display = 'none';
        }, 5000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new RaffleGame();
});