class ShadowRaffleGame {
    constructor() {
        this.currentUser = null;
        this.currentSection = 'game';
        this.isSpinning = false;
        this.rouletteCards = [];
        this.winningPrize = null;
        
        this.init();
    }
    
    async init() {
        await this.loadUserFromStorage();
        
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
        
        this.loadSection('game');
    }
    
    async loadUserFromStorage() {
        const savedUser = localStorage.getItem('shadowUser');
        console.log('📦 Данные из localStorage:', savedUser);
        
        if (!savedUser) {
            console.log('❌ Нет сохраненного пользователя');
            window.location.href = '/';
            return;
        }
        
        try {
            const parsedUser = JSON.parse(savedUser);
            
            // Запрашиваем актуальные данные с сервера
            const response = await fetch(`/api/user-data?user_id=${parsedUser.id}`);
            const data = await response.json();
            
            if (data.success) {
                this.currentUser = data.user;
                localStorage.setItem('shadowUser', JSON.stringify(this.currentUser));
            } else {
                this.currentUser = parsedUser;
            }
            
            this.updateUserDisplay();
            
        } catch (error) {
            console.error('❌ Ошибка загрузки пользователя:', error);
            this.currentUser = JSON.parse(savedUser);
            this.updateUserDisplay();
        }
    }
    
    updateUserDisplay() {
        console.log('🖥️ Обновляем интерфейс с балансом:', this.currentUser.shadow_coins);
        
        const nicknameEl = document.getElementById('userNickname');
        const coinsEl = document.getElementById('userCoins');
        const contactsEl = document.getElementById('userContacts');
        
        if (nicknameEl) nicknameEl.textContent = this.currentUser.nickname;
        if (coinsEl) coinsEl.textContent = this.currentUser.shadow_coins;
        
        const contacts = [];
        if (this.currentUser.telegram) contacts.push(`📱 ${this.currentUser.telegram}`);
        if (this.currentUser.site_url) contacts.push(`🔗 ${this.currentUser.site_url}`);
        if (contactsEl) contactsEl.textContent = contacts.join(' • ');
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
        
        const content = document.getElementById('content');
        
        switch(section) {
            case 'game':
                content.innerHTML = this.getGameHTML();
                this.initGame();
                break;
            case 'wins':
                content.innerHTML = this.getWinsHTML();
                this.loadUserWins();
                break;
            case 'profile':
                content.innerHTML = this.getProfileHTML();
                this.initProfile();
                break;
        }
    }
    
            getGameHTML() {
            return `
                <div class="roulette-container">
                    <!-- Добавляем указатель над рулеткой -->
                    <div class="roulette-pointer">▼</div>
                    
                    <div class="roulette-wrapper">
                        <div class="roulette-track" id="rouletteTrack"></div>
                    </div>
                    
                    <button id="spinButton" class="spin-btn">
                        🌑 КРУТИТЬ РУЛЕТКУ (1 теневая монета) 🌑
                    </button>
                </div>
                
                <div class="prizes-section">
                    <h2>🎲 Доступные карты</h2>
                    <div class="prizes-scroll">
                        <div id="prizesGrid" class="prizes-grid"></div>
                    </div>
                </div>
                
                <div class="public-winners">
                    <h3>🏆 Последние победители</h3>
                    <div id="publicWinners"></div>
                </div>
            `;
        }
            
    getWinsHTML() {
        return `
            <h2>🏆 Мои выигрыши</h2>
            <div class="prizes-scroll">
                <div id="userWinsGrid" class="prizes-grid"></div>
            </div>
        `;
    }
    
    getProfileHTML() {
        return `
            <h2>👤 Мой профиль</h2>
            <div class="profile-info">
                <p><strong>Никнейм:</strong> ${this.currentUser.nickname}</p>
                <p><strong>Telegram:</strong> <span id="profileTelegram">${this.currentUser.telegram || 'не указан'}</span></p>
                <p><strong>Ссылка на профиль:</strong> <span id="profileSiteUrl">${this.currentUser.site_url ? `<a href="${this.currentUser.site_url}" target="_blank">перейти</a>` : 'не указана'}</span></p>
                <p><strong>Теневые монеты:</strong> ${this.currentUser.shadow_coins}</p>
                <p><strong>Дата регистрации:</strong> ${new Date(this.currentUser.created_at || Date.now()).toLocaleDateString()}</p>
            </div>
            
            <div class="profile-actions">
                <button onclick="window.gameInstance.showEditNickname()" class="profile-btn">✏️ Изменить ник</button>
                <button onclick="window.gameInstance.showEditTelegram()" class="profile-btn">📱 Изменить Telegram</button>
                <button onclick="window.gameInstance.showEditSiteUrl()" class="profile-btn">🔗 Изменить ссылку</button>
            </div>
        `;
        }

        async initGame() {
        await this.loadPrizes();
        await this.loadPublicWinners();
        this.initRoulette();
        
        document.getElementById('spinButton').addEventListener('click', () => this.spinRoulette());
    }
    
        async loadPrizes() {
        try {
            const response = await fetch('/api/prizes');
            const data = await response.json();
            
            const grid = document.getElementById('prizesGrid');
            const spinBtn = document.getElementById('spinButton');
            
            if (data.success) {
                // Сохраняем призы для рулетки
                this.rouletteCards = data.prizes;
                
                // Обновляем отображение в сетке призов
                if (grid) {
                    if (data.prizes.length > 0) {
                        grid.innerHTML = data.prizes.map(prize => `
                            <div class="prize-card" onclick="window.gameInstance.showPrizeDetails(${JSON.stringify(prize).replace(/"/g, '&quot;')})">
                                <img src="/static/images/${prize.image}" alt="${prize.name}">
                            </div>
                        `).join('');
                    } else {
                        grid.innerHTML = '<p class="no-prizes">✨ Все карты разыграны! ✨</p>';
                    }
                }
                
                // Обновляем кнопку
                if (spinBtn) {
                    if (data.prizes.length === 0) {
                        spinBtn.textContent = '✨ ВСЕ КАРТЫ РАЗЫГРАНЫ ✨';
                        spinBtn.disabled = true;
                    } else {
                        spinBtn.textContent = '🌑 КРУТИТЬ РУЛЕТКУ (1 теневая монета) 🌑';
                        spinBtn.disabled = false;
                    }
                }
                
                // Обновляем рулетку ТОЛЬКО если не идет прокрутка
                if (!this.isSpinning) {
                    this.initRoulette();
                }
            }

        } catch (error) {
            console.error('Ошибка загрузки призов:', error);
        }
    }

        safeRefreshRoulette() {
            const track = document.getElementById('rouletteTrack');
            if (!track) return;
            
            if (this.isSpinning) {
                // Если рулетка крутится, планируем обновление после остановки
                setTimeout(() => this.safeRefreshRoulette(), 500);
                return;
            }
            
            this.initRoulette();
        }
        
        initRoulette() {
            const track = document.getElementById('rouletteTrack');
            if (!track) return;
            
            if (!this.rouletteCards || this.rouletteCards.length === 0) {
                track.innerHTML = '<div class="roulette-empty">✨ Все карты разыграны! ✨</div>';
                return;
            }
            
            // РАССЧИТЫВАЕМ, СКОЛЬКО КОПИЙ НУЖНО
            const uniquePrizes = this.rouletteCards.length;
            const cardWidth = 175;
            const containerWidth = 1200;
            
            // Сколько карт помещается в контейнер
            const cardsVisible = Math.ceil(containerWidth / cardWidth); // ≈ 7 карт
            
            // МИНИМАЛЬНОЕ ЖЕЛАЕМОЕ КОЛИЧЕСТВО КАРТ В ТРЕКЕ
            // Хотим, чтобы было не меньше 3 полных экранов карт
            const minDesiredCards = cardsVisible * 3;
            
            // Вычисляем необходимое количество копий
            let copiesNeeded = Math.ceil(minDesiredCards / uniquePrizes);
            
            // Но делаем минимум 5 копий для красоты, даже если карт много
            copiesNeeded = Math.max(copiesNeeded, 5);
            
            console.log(`📊 Уникальных призов: ${uniquePrizes}, нужно копий: ${copiesNeeded}`);
            
            // Создаем массив с нужным количеством копий
            let cards = [];
            for (let i = 0; i < copiesNeeded; i++) {
                cards = [...cards, ...this.rouletteCards];
            }
            
            track.innerHTML = cards.map(prize => `
                <div class="roulette-card">
                    <img src="/static/images/${prize.image}" alt="${prize.name}">
                </div>
            `).join('');
            
            track.style.transition = 'none';
            track.style.transform = 'translateX(0)';
        }

        // Показать детали приза в модальном окне
    showPrizeDetails(prize) {
        // Удаляем существующее модальное окно, если есть
        const existingModal = document.querySelector('.modal-overlay');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Создаем модальное окно
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.style.display = 'flex';
        
        modal.innerHTML = `
            <div class="modal-content">
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">✕</button>
                <div class="modal-image">
                    <img src="/static/images/${prize.image}" alt="${prize.name}">
                </div>
                <h2 class="modal-title">${prize.name}</h2>
                <div class="modal-description">
                    ${prize.description || 'Нет описания'}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Закрытие по клику на фон
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
    
    // Показать модальное окно с выигрышем после рулетки
    showWinModal(prize) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.style.display = 'flex';
        
        modal.innerHTML = `
            <div class="modal-content" style="border-color: #ffaa00;">
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">✕</button>
                <div class="modal-image">
                    <img src="/static/images/${prize.image}" alt="${prize.name}">
                </div>
                <h2 class="modal-title" style="color: #ffaa00;">🎉 ПОБЕДА! 🎉</h2>
                <div class="modal-description">
                    <p style="text-align: center; font-size: 1.2em; color: #ffaa00;">Вы выиграли:</p>
                    <p style="text-align: center; font-size: 1.5em;">${prize.name}</p>
                    <p style="text-align: center;">${prize.description || 'Поздравляем с выигрышем!'}</p>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        setTimeout(() => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                }
            });
        }, 100);
    }

       async spinRoulette() {
    // ... (начальные проверки остаются теми же) ...
    
            this.isSpinning = true;
            spinBtn.disabled = true;
            spinBtn.textContent = '🎰 Крутим... 🎰';

            // ПОЛУЧАЕМ СЛУЧАЙНЫЙ ПРИЗ
            const prizeIndex = Math.floor(Math.random() * this.rouletteCards.length);
            this.winningPrize = this.rouletteCards[prizeIndex];
            
            console.log('🎯 Выигрышный приз индекс:', prizeIndex);

            // КОНСТАНТЫ
            const cardWidth = 175;
            const containerWidth = 1200;
            const cardsVisible = Math.ceil(containerWidth / cardWidth);
            
            // ВЫЧИСЛЯЕМ КОЛИЧЕСТВО КОПИЙ В ТРЕКЕ
            const track = document.getElementById('rouletteTrack');
            const totalCardsInTrack = track.children.length;
            const uniquePrizes = this.rouletteCards.length;
            const copiesCount = Math.floor(totalCardsInTrack / uniquePrizes);
            
            console.log(`📊 Всего карт в треке: ${totalCardsInTrack}, копий: ${copiesCount}`);

            // ===== ИСПРАВЛЕННЫЙ РАСЧЕТ =====
            
            // ВСЕГДА используем копию из середины (чтобы были карты слева и справа)
            const targetCopyIndex = Math.floor(copiesCount / 2); // Например, при 5 копиях: 0,1,2,3,4 -> 2
            
            // Индекс карты в треке
            const targetCardIndex = (targetCopyIndex * uniquePrizes) + prizeIndex;
            
            // Желаемая позиция - 5-я карта (чтобы быть под стрелкой)
            const desiredPosition = 5;
            
            // Сколько шагов нужно сделать, чтобы targetCardIndex оказался на позиции desiredPosition
            // ВАЖНО: stepsToTarget НЕ должен быть отрицательным!
            let stepsToTarget = targetCardIndex - desiredPosition;
            
            // Добавляем полные обороты, но гарантируем, что stepsToTarget остается в пределах
            const fullRotationSteps = totalCardsInTrack;
            
            // Выбираем количество оборотов (2-3, не слишком много)
            const extraRotations = 2 + Math.floor(Math.random() * 2); // 2 или 3
            
            // Итоговые шаги
            let totalSteps = (extraRotations * fullRotationSteps) + stepsToTarget;
            
            // ГАРАНТИРУЕМ, ЧТО МЫ В ПРЕДЕЛАХ ТРЕКА
            // Максимально возможное количество шагов (не дальше чем totalCardsInTrack * 3)
            const maxSteps = totalCardsInTrack * 3;
            totalSteps = Math.min(totalSteps, maxSteps);
            
            const targetPosition = -(totalSteps * cardWidth);
            
            console.log(`📊 targetCopyIndex: ${targetCopyIndex}, индекс в треке: ${targetCardIndex}`);
            console.log(`📊 stepsToTarget: ${stepsToTarget}, оборотов: ${extraRotations}`);
            console.log(`📊 totalSteps: ${totalSteps}, позиция: ${targetPosition}px`);

            // Проверка: не уедем ли мы слишком далеко?
            // Если targetPosition уводит нас за пределы 3-й копии, корректируем
            const safeMaxPosition = -(copiesCount * uniquePrizes * cardWidth * 0.8); // 80% от всех карт
            
            if (targetPosition < safeMaxPosition) {
                console.log('⚠️ Позиция скорректирована для безопасности');
                totalSteps = Math.floor(safeMaxPosition / -cardWidth);
            }

            // ТРЕХЭТАПНАЯ АНИМАЦИЯ (оставляем как есть)
            track.style.transition = 'transform 0.8s cubic-bezier(0.4, 0.0, 0.2, 1)';
            track.style.transform = `translateX(${targetPosition * 0.3}px)`;
            
            setTimeout(() => {
                track.style.transition = 'transform 2.5s cubic-bezier(0.0, 0.0, 0.2, 1)';
                track.style.transform = `translateX(${targetPosition}px)`;
            }, 800);
            
            setTimeout(() => {
                track.style.transition = 'transform 0.7s cubic-bezier(0.0, 0.0, 0.0, 1)';
                track.style.transform = `translateX(${targetPosition}px)`;
            }, 3300);

            // ... (остальной код с обработкой результата)
        }

        async loadUserWins() {
        const grid = document.getElementById('userWinsGrid');
        if (!grid) return;
        
        grid.innerHTML = '<div class="loading">Загрузка...</div>';
        
        try {
            const response = await fetch(`/api/user-wins?user_id=${this.currentUser.id}`);
            const data = await response.json();
            
            if (data.success && data.wins.length > 0) {
                grid.innerHTML = data.wins.map(win => `
                    <div class="prize-card" onclick="window.gameInstance.showPrizeDetails({name: '${win.name}', image: '${win.image}', description: '${win.description || ''}'})">
                        <img src="/static/images/${win.image}" alt="${win.name}">
                    </div>
                `).join('');
            } else {
                grid.innerHTML = '<p style="text-align: center;">У вас пока нет выигрышей</p>';
            }
        } catch (error) {
            console.error('Ошибка загрузки выигрышей:', error);
            grid.innerHTML = '<p style="text-align: center; color: red;">Ошибка загрузки</p>';
        }
    }

        async loadPublicWinners() {
        try {
            const response = await fetch('/api/public-winners');
            const data = await response.json();
            
            const container = document.getElementById('publicWinners');
            if (!container) return;
            
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
    
    showMessage(text, type) {
        const msgDiv = document.getElementById('message');
        msgDiv.textContent = text;
        msgDiv.className = `message message-${type}`;
        msgDiv.style.display = 'block';
        
        setTimeout(() => {
            msgDiv.style.display = 'none';
        }, 3000);
    }

        // Показать форму изменения ника
    showEditNickname() {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.style.display = 'flex';
        
        modal.innerHTML = `
            <div class="modal-content">
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">✕</button>
                <h2 class="modal-title">✏️ Изменить никнейм</h2>
                <div class="form-group">
                    <label for="editNickname">Новый никнейм (3-20 символов)</label>
                    <input type="text" id="editNickname" maxlength="20" value="${this.currentUser.nickname}">
                    <small id="nicknameCounter" class="char-counter">${this.currentUser.nickname.length}/20</small>
                </div>
                <button onclick="window.gameInstance.updateNickname()" class="register-btn">💾 Сохранить</button>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Добавляем счетчик
        const input = document.getElementById('editNickname');
        const counter = document.getElementById('nicknameCounter');
        
        input.addEventListener('input', () => {
            counter.textContent = `${input.value.length}/20`;
            counter.style.color = input.value.length > 20 ? '#ff4444' : '#8080a0';
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
    }
    
    // Обновление ника
    async updateNickname() {
        const newNickname = document.getElementById('editNickname').value.trim();
        
        if (!newNickname) {
            this.showMessage('Введите никнейм', 'error');
            return;
        }
        
        if (newNickname.length < 3) {
            this.showMessage('Никнейм должен быть не менее 3 символов', 'error');
            return;
        }
        
        if (newNickname.length > 20) {
            this.showMessage('Никнейм должен быть не более 20 символов', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/update_profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    nickname: newNickname
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentUser = data.user;
                localStorage.setItem('shadowUser', JSON.stringify(this.currentUser));
                document.querySelector('.modal-overlay').remove();
                this.showMessage('Никнейм успешно изменён!', 'success');
                this.loadSection('profile');
                this.updateUserDisplay();
            } else {
                this.showMessage(data.message, 'error');
            }
        } catch (error) {
            this.showMessage('Ошибка соединения с сервером', 'error');
        }
    }
    
    // Показать форму изменения Telegram
    showEditTelegram() {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.style.display = 'flex';
        
        modal.innerHTML = `
            <div class="modal-content">
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">✕</button>
                <h2 class="modal-title">📱 Изменить Telegram</h2>
                <div class="form-group">
                    <label for="editTelegram">Telegram (@username, макс. 15 символов)</label>
                    <input type="text" id="editTelegram" maxlength="15" value="${this.currentUser.telegram || ''}">
                    <small>Формат: @username</small>
                </div>
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button onclick="window.gameInstance.updateTelegram()" class="register-btn">💾 Сохранить</button>
                    <button onclick="window.gameInstance.clearTelegram()" class="register-btn" style="background: linear-gradient(135deg, #3a1a1a, #4a2a2a);">🗑️ Очистить</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
    }
    
    // Обновление Telegram
    async updateTelegram() {
        let telegram = document.getElementById('editTelegram').value.trim();
        
        if (telegram && !telegram.startsWith('@')) {
            telegram = '@' + telegram;
        }
        
        if (telegram && telegram.length > 15) {
            this.showMessage('Telegram не может быть длиннее 15 символов', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/update_profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    telegram: telegram || null
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentUser = data.user;
                localStorage.setItem('shadowUser', JSON.stringify(this.currentUser));
                document.querySelector('.modal-overlay').remove();
                this.showMessage('Telegram успешно обновлён!', 'success');
                this.loadSection('profile');
                this.updateUserDisplay();
            } else {
                this.showMessage(data.message, 'error');
            }
        } catch (error) {
            this.showMessage('Ошибка соединения с сервером', 'error');
        }
    }
    
    // Очистить Telegram
    async clearTelegram() {
        if (!confirm('Удалить Telegram из профиля?')) return;
        
        try {
            const response = await fetch('/api/update_profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    telegram: null
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentUser = data.user;
                localStorage.setItem('shadowUser', JSON.stringify(this.currentUser));
                document.querySelector('.modal-overlay').remove();
                this.showMessage('Telegram удалён', 'success');
                this.loadSection('profile');
                this.updateUserDisplay();
            }
        } catch (error) {
            this.showMessage('Ошибка соединения с сервером', 'error');
        }
    }
    
    // Показать форму изменения ссылки
    showEditSiteUrl() {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.style.display = 'flex';
        
        modal.innerHTML = `
            <div class="modal-content">
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">✕</button>
                <h2 class="modal-title">🔗 Изменить ссылку Remanga</h2>
                <div class="form-group">
                    <label for="editSiteUrl">Ссылка на профиль Remanga</label>
                    <input type="url" id="editSiteUrl" value="${this.currentUser.site_url || ''}" placeholder="https://remanga.org/user/48443/about">
                    <small>Формат: https://remanga.org/user/ID/about (макс. 100 символов)</small>
                </div>
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button onclick="window.gameInstance.updateSiteUrl()" class="register-btn">💾 Сохранить</button>
                    <button onclick="window.gameInstance.clearSiteUrl()" class="register-btn" style="background: linear-gradient(135deg, #3a1a1a, #4a2a2a);">🗑️ Очистить</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
    }
    
    // Обновление ссылки
    async updateSiteUrl() {
        const siteUrl = document.getElementById('editSiteUrl').value.trim();
        
        if (siteUrl) {
            const remangaRegex = /^https:\/\/remanga\.org\/user\/[0-9]+\/about$/;
            if (!remangaRegex.test(siteUrl)) {
                this.showMessage('Неверный формат ссылки Remanga', 'error');
                return;
            }
            
            if (siteUrl.length > 100) {
                this.showMessage('Ссылка слишком длинная', 'error');
                return;
            }
        }
        
        try {
            const response = await fetch('/api/update_profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    site_url: siteUrl || null
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentUser = data.user;
                localStorage.setItem('shadowUser', JSON.stringify(this.currentUser));
                document.querySelector('.modal-overlay').remove();
                this.showMessage('Ссылка успешно обновлена!', 'success');
                this.loadSection('profile');
                this.updateUserDisplay();
            } else {
                this.showMessage(data.message, 'error');
            }
        } catch (error) {
            this.showMessage('Ошибка соединения с сервером', 'error');
        }
    }
    
    // Очистить ссылку
    async clearSiteUrl() {
        if (!confirm('Удалить ссылку из профиля?')) return;
        
        try {
            const response = await fetch('/api/update_profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    site_url: null
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentUser = data.user;
                localStorage.setItem('shadowUser', JSON.stringify(this.currentUser));
                document.querySelector('.modal-overlay').remove();
                this.showMessage('Ссылка удалена', 'success');
                this.loadSection('profile');
                this.updateUserDisplay();
            }
        } catch (error) {
            this.showMessage('Ошибка соединения с сервером', 'error');
        }
    }
    
    initProfile() {
        // Профиль уже загружен через getProfileHTML
    }
    
    logout() {
        localStorage.removeItem('shadowUser');
        window.location.href = '/';
    }
}

// Создаем глобальный экземпляр
        document.addEventListener('DOMContentLoaded', () => {
            window.gameInstance = new ShadowRaffleGame();
        });