        class MusicWordleGame {
            constructor() {
                this.maxGuesses = 6;
                this.currentGuesses = 0;
                this.gameEnded = false;
                this.currentAlbum = null;
                
                this.initializeElements();
                this.setupEventListeners();
                this.startNewGame();
            }

            initializeElements() {
                this.guessInput = document.getElementById('guessInput');
                this.submitButton = document.getElementById('submitGuess');
                this.guessesContainer = document.getElementById('guessesContainer');
                this.statusMessage = document.getElementById('statusMessage');
                this.guessesLeftElement = document.getElementById('guessesLeft');
                this.artistElement = document.getElementById('artistName');
                this.yearElement = document.getElementById('releaseYear');
                this.genreElement = document.getElementById('genre');
            }

            setupEventListeners() {
                this.submitButton.addEventListener('click', () => this.submitGuess());
                this.guessInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.submitGuess();
                    }
                });
                this.guessInput.addEventListener('input', () => {
                    this.submitButton.disabled = this.guessInput.value.trim() === '';
                });
            }

            async startNewGame() {
                this.currentGuesses = 0;
                this.gameEnded = false;
                this.guessesContainer.innerHTML = '';
                this.statusMessage.innerHTML = '';
                this.guessInput.disabled = false;
                this.submitButton.disabled = true;
                this.guessInput.value = '';
                this.updateGuessesLeft();

                // Get new album from your Python API
                await this.fetchNewAlbum();
            }

            async fetchNewAlbum() {
                try {
                    // Replace this URL with your actual API endpoint
                    const response = await fetch('http://localhost:5000/api/new-game', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    });

                    if (!response.ok) {
                        throw new Error('Failed to fetch new album');
                    }

                    const data = await response.json();
                    this.currentAlbum = data;
                    
                    // Update the UI with album info (excluding the album name)
                    this.artistElement.textContent = data.artist;
                    this.yearElement.textContent = data.year;
                    this.genreElement.textContent = data.genre;
                    
                } catch (error) {
                    console.error('Error fetching new album:', error);
                    // For demo purposes, use mock data
                    this.currentAlbum = {
                        artist: "The Beatles",
                        year: "1967",
                        genre: "Rock",
                        album: "Sgt. Pepper's Lonely Hearts Club Band"
                    };
                    
                    this.artistElement.textContent = this.currentAlbum.artist;
                    this.yearElement.textContent = this.currentAlbum.year;
                    this.genreElement.textContent = this.currentAlbum.genre;
                }
            }

            async submitGuess() {
                if (this.gameEnded || this.guessInput.value.trim() === '') {
                    return;
                }

                const guess = this.guessInput.value.trim();
                this.currentGuesses++;
                
                // Disable input while processing
                this.setLoadingState(true);

                try {
                    // Send guess to your Python API
                    const isCorrect = await this.checkGuess(guess);
                    
                    // Add guess to the display
                    this.addGuessToDisplay(guess, isCorrect);
                    
                    // Check win/lose conditions
                    if (isCorrect) {
                        this.handleWin();
                    } else if (this.currentGuesses >= this.maxGuesses) {
                        this.handleLose();
                    } else {
                        this.updateGuessesLeft();
                        this.guessInput.value = '';
                        this.guessInput.focus();
                    }
                    
                } catch (error) {
                    console.error('Error checking guess:', error);
                    this.showError('Error checking guess. Please try again.');
                } finally {
                    this.setLoadingState(false);
                }
            }

            async checkGuess(guess) {
                try {
                    // Replace this URL with your actual API endpoint
                    const response = await fetch('http://localhost:5000/api/guess', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            guess: guess,
                            game_id: this.currentAlbum?.game_id // if you're tracking game sessions
                        })
                    });

                    if (!response.ok) {
                        throw new Error('Failed to check guess');
                    }

                    const data = await response.json();
                    return data.correct;
                    
                } catch (error) {
                    console.error('Error in checkGuess:', error);
                    // For demo purposes, check against mock data
                    return guess.toLowerCase() === this.currentAlbum.album.toLowerCase();
                }
            }

            addGuessToDisplay(guess, isCorrect) {
                const guessElement = document.createElement('div');
                guessElement.className = `guess-item ${isCorrect ? 'guess-correct' : 'guess-incorrect'}`;
                
                guessElement.innerHTML = `
                    <span>${guess}</span>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span class="guess-number">${this.currentGuesses}</span>
                        <span>${isCorrect ? '✅' : '❌'}</span>
                    </div>
                `;
                
                this.guessesContainer.appendChild(guessElement);
                guessElement.scrollIntoView({ behavior: 'smooth' });
            }

            handleWin() {
                this.gameEnded = true;
                this.guessInput.disabled = true;
                this.submitButton.disabled = true;
                
                this.statusMessage.innerHTML = `
                    <div class="status-message status-win">
                        🎉 Congratulations! You guessed "${this.currentAlbum.album}" in ${this.currentGuesses} ${this.currentGuesses === 1 ? 'try' : 'tries'}!
                        <button class="new-game-button" onclick="game.startNewGame()">Play Again</button>
                    </div>
                `;
            }

            handleLose() {
                this.gameEnded = true;
                this.guessInput.disabled = true;
                this.submitButton.disabled = true;
                
                this.statusMessage.innerHTML = `
                    <div class="status-message status-lose">
                        😔 Game Over! The album was "${this.currentAlbum.album}"
                        <button class="new-game-button" onclick="game.startNewGame()">Try Again</button>
                    </div>
                `;
            }

            updateGuessesLeft() {
                const remaining = this.maxGuesses - this.currentGuesses;
                this.guessesLeftElement.textContent = remaining;
            }

            setLoadingState(loading) {
                if (loading) {
                    document.querySelector('.game-container').classList.add('loading');
                    this.submitButton.textContent = 'Checking...';
                } else {
                    document.querySelector('.game-container').classList.remove('loading');
                    this.submitButton.textContent = 'Submit Guess';
                }
            }

            showError(message) {
                this.statusMessage.innerHTML = `
                    <div class="status-message" style="background: #fff3cd; color: #856404; border: 1px solid #ffeaa7;">
                        ⚠️ ${message}
                    </div>
                `;
                setTimeout(() => {
                    this.statusMessage.innerHTML = '';
                }, 3000);
            }
        }

        // Initialize the game
        const game = new MusicWordleGame();