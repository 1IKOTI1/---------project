class RaffleGame{
    constructor(){
        this.nicknameInput = document.getElementById('nicknameInput');
        this.playButton = document.getElementById('playButton');
        this.messageDiv = document.getElementById('message');
        this.prizesGrid = document.getElementById('prizesGrid');
        
        this.init();
    }

    async init(){
        await this.loadPrizes();

        this.playButton.addEventListener('click', () => this.handlePlay());
    }

    async loadPrizes(){
        try{
            const response = await fetch('/api/prizes');
            const data = await response.json();

            if(data.success){
                this.renderPrizes(data.prizes);
            }
           
        } catch (error){
            this.showMessage('ошибка загрузки наград', 'error');
        }
    }

    renderPrizes(prizes){
        this.prizesGrid.innerHTML = '';

        if(prizes.length === 0){
            this.prizesGrid.innerHTML = '<p class ="no-prizes">Все призы разыграны!</p>';
            this.playButton.disabled = true;
            return;
        }

        prizes.forEach(prizes => {
            const card = document.createElement('div');
            card.className = 'prize-card';
            card.innerHTML = `
                 <img src="/static/images/${prizes.image}" alt="${prizes.name}">
                 <h3>${prizes.name}</h3>
                 <p>${prizes.description || ''}</p>
                 `;
                 this.prizesGrid.appendChild(card);
                });             
    }

    async handlePlay(){
        const nickname = this.nicknameInput.value.trim();

        if (!nickname){
            this.showMessage('Введите имя', 'error');
            return;
        }

        this.playButton.disabled = true;
        this.playButton.textContent = 'обработка...';

        try{
            const response = await fetch('/api/play',{
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({nickname: nickname})
            });

            const data = await response.json();

            if(data.success){
                this.showMessage(data.message, 'success');
                await this.loadPrizes();
                this.nicknameInput.value = '';
            }else{
                this.showMessage(data.message, 'error');
            }
        }catch (error){
            this.showMessage('Ошибка соеденения с сервером', 'error');
        }finally{
            this.playButton.disabled = false;
            this.playButton.textContent = 'Забрать приз';
        }
    }

    showMessage(text, type){
        this.messageDiv.textContent = text;
        this.messageDiv.className = `message message-${type}`;
    }
}

document.addEventListener('DOMContentLoaded',() =>{
    new RaffleGame();
})