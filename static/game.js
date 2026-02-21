class ShadowRaffleGame {
    constructor() {
        this.currentUser = null;
        this.currentSection = 'game';
        
        this.loadUserFromStorage();
        this.init();
    }
    
    loadUserFromStorage() {
        const savedUser = localStorage.getItem('shadowUser');
        if (savedUser) {
            try {
                this.currentUser = JSON.parse(savedUser);
                console.log('👤 Загружен пользователь:', this.currentUser);
                document.getElementById('userNickname').textContent = this.currentUser.nickname;
                document.getElementById('userCoins').textContent = this.currentUser.shadow_coins;
                
                // Показываем контакты пользователя
                const contacts = [];
                if (this.currentUser.telegram) contacts.push(`📱 ${this.currentUser.telegram}`);
                if (this.currentUser.site_url) contacts.push(`🔗 ${this.currentUser.site_url}`);
                document.getElementById('userContacts').textContent = contacts.join(' • ');
            } catch (e) {
                console.error('Ошибка загрузки пользователя');
                window.location.href = '/';
            }
        } else {
            window.location.href = '/';
        }
    }
    
    async init() {
        // Обработка навигации
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                if (e.target.getAttribute('href') === '/logout') {
                    this.logout();
                    e.preventDefault();
                } else {
                    e.preventDefault();
                    this.loadSection(e.target.getAttribute('data-section'));
                }
            });
        });
        
        // Загружаем начальную секцию
        this.loadSection('game');
    }
    
    async loadSection(section) {
        this.currentSection = section;
        
        // Обновляем активную кнопку
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-section') === section) {
                btn.classList.add('active');
            }
        });
        
        // Загружаем контент
        const content = document.getElementById('content');
        
        switch(section) {
            case 'game':
                content.innerHTML = await this.getGameHTML();
                this.initGame();
                break;
            case 'wins':
                content.innerHTML = await this.getWinsHTML();
                this.loadUserWins();
                break;
            case 'profile':
                content.innerHTML = await this.getProfileHTML();
                break;
        }
    }
    
    getGameHTML() {
        return `
            <h2>🎲 Доступные теневые карты</h2>
            <div id="prizesGrid" class="prizes-grid">
                <div class="loading">Загрузка...</div>
            </div>
            
            <button id="drawBtn" class="draw-btn">
                🌑 Крутить рулетку (1 теневая монета) 🌑
            </button>
            
            <div class="public-winners">
                <h3>🏆 Последние победители</h3>
                <div id="publicWinners"></div>
            </div>
        `;
    }
    
    getWinsHTML() {
        return `
            <h2>🏆 Мои выигрыши</h2>
            <table class="wins-table" id="userWinsTable">
                <thead>
                    <tr>
                        <th>Карта</th>
                        <th>Название</th>
                        <th>Описание</th>
                        <th>Дата</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        `;
    }
    
    getProfileHTML() {
        return `
            <h2>👤 Мой профиль</h2>
            <div class="profile-info">
                <p><strong>Никнейм:</strong> ${this.currentUser.nickname}</p>
                <p><strong>Telegram:</strong> ${this.currentUser.telegram || 'не указан'}</p>
                <p><strong>Ссылка на профиль:</strong> ${this.currentUser.site_url ? `<a href="${this.currentUser.site_url}" target="_blank">перейти</a>` : 'не указана'}</p>
                <p><strong>Теневые монеты:</strong> ${this.currentUser.shadow_coins}</p>
                <p><strong>Дата регистрации:</strong> ${new Date(this.currentUser.created_at || Date.now()).toLocaleDateString()}</p>
            </div>
        `;
    }
    
    async initGame() {
        await this.loadPrizes();
        await this.loadPublicWinners();
        
        document.getElementById('drawBtn').addEventListener('click', () => this.handleDraw());
    }
    
    async loadPrizes() {
        try {
            const response = await fetch('/api/prizes');
            const data = await response.json();
            
            const grid = document.getElementById('prizesGrid');
            
            if (data.success && data.prizes.length > 0) {
                grid.innerHTML = data.prizes.map(prize => `
                    <div class="prize-card">
                        <img src="/static/images/${prize.image}" alt="${prize.name}">
                        <h3>${prize.name}</h3>
                        <p>${prize.description || ''}</p>
                    </div>
                `).join('');
            } else {
                grid.innerHTML = '<p class="no-prizes">Все теневые карты разыграны!</p>';
            }
        } catch (error) {
            console.error('Ошибка загрузки призов:', error);
        }
    }
    
    async loadPublicWinners() {
        try {
            const response = await fetch('/api/public-winners');
            const data = await response.json();
            
            const container = document.getElementById('publicWinners');
            
            if (data.success && data.winners.length > 0) {
                container.innerHTML = `
                    <div class="winners-list">
                        ${data.winners.map(w => `
                            <div class="winner-item">
                                <span class="nickname">${w.nickname}</span>
                                <span class="prize">${w.prize_name}</span>
                                <span class="date">${new Date(w.won_at).toLocaleDateString()}</span>
                            </div>
                        `).join('')}
                    </div>
                `;
            } else {
                container.innerHTML = '<p>Пока нет победителей</p>';
            }
        } catch (error) {
            console.error('Ошибка загрузки победителей:', error);
        }
    }
    
    async loadUserWins() {
        try {
            const response = await fetch(`/api/user-wins?user_id=${this.currentUser.id}`);
            const data = await response.json();
            
            const tbody = document.querySelector('#userWinsTable tbody');
            
            if (data.success && data.wins.length > 0) {
                tbody.innerHTML = data.wins.map(win => `
                    <tr>
                        <td><img src="/static/images/${win.image}" alt="${win.name}"></td>
                        <td>${win.name}</td>
                        <td>${win.description || ''}</td>
                        <td>${new Date(win.won_at).toLocaleString()}</td>
                    </tr>
                `).join('');
            } else {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align: center;">У вас пока нет выигрышей</td></tr>';
            }
        } catch (error) {
            console.error('Ошибка загрузки выигрышей:', error);
        }
    }
    
    async handleDraw() {
        const drawBtn = document.getElementById('drawBtn');
        drawBtn.disabled = true;
        drawBtn.textContent = 'Крутим...';
        
        try {
            const response = await fetch('/api/draw', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ user_id: this.currentUser.id })
            });
            
            const data = await response.json();
            console.log('Ответ при розыгрыше:', data);  // ← отладка
            
            if (data.success) {
                // Обновляем баланс в текущем объекте
                this.currentUser.shadow_coins = data.new_balance;
                
                // Сохраняем в localStorage
                localStorage.setItem('shadowUser', JSON.stringify(this.currentUser));
                
                // Обновляем отображение на странице
                document.getElementById('userCoins').textContent = data.new_balance;
                
                this.showMessage(data.message, 'success');
                await this.loadPrizes();  // Обновляем список призов
                await this.loadPublicWinners();  // Обновляем список победителей
            } else {
                this.showMessage(data.message, 'error');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            this.showMessage('Ошибка соединения с сервером', 'error');
        } finally {
            drawBtn.disabled = false;
            drawBtn.textContent = '🌑 Крутить рулетку (1 теневая монета) 🌑';
        }
    }
    
    showMessage(text, type) {
        const msgDiv = document.getElementById('message');
        msgDiv.textContent = text;
        msgDiv.className = `message message-${type}`;
        msgDiv.style.display = 'block';
        
        setTimeout(() => {
            msgDiv.style.display = 'none';
        }, 3000);
    }
    
    logout() {
        localStorage.removeItem('shadowUser');
        window.location.href = '/';
    }

    
}

document.addEventListener('DOMContentLoaded', () => {
    new ShadowRaffleGame();
});
   