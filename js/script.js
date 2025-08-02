        class MusicWordleGame {
            constructor() {
                this.maxGuesses = 6;
                this.currentGuesses = 0;
                this.gameEnded = false;
                this.targetAlbum = null;
                this.searchTimeout = null;
                this.gameId = null;
                
                this.initializeElements();
                this.setupEventListeners();
                this.startNewGame();
            }

            initializeElements() {
             this.searchInput = document.getElementById('searchInput');
                this.searchSuggestions = document.getElementById('searchSuggestions');
                this.guessesContainer = document.getElementById('guessesContainer');
                this.statusMessage = document.getElementById('statusMessage');
                this.guessCountElement = document.getElementById('guessCount');
                this.guessesLeftElement = document.getElementById('guessesLeft');
            }

            setupEventListeners() {
                this.searchInput.addEventListener('input', (e) => {
                    this.handleSearch(e.target.value);
                });

                this.searchInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        this.selectFirstSuggestion();
                    }
                });

                // Close suggestions when clicking outside
                document.addEventListener('click', (e) => {
                    if (!this.searchInput.contains(e.target) && !this.searchSuggestions.contains(e.target)) {
                        this.hideSuggestions();
                    }
                });
            }

            async startNewGame() {
                this.currentGuesses = 0;
                this.gameEnded = false;
                this.guessesContainer.innerHTML = '';
                this.statusMessage.innerHTML = '';
                this.searchInput.disabled = false;
                this.searchInput.value = '';
                this.hideSuggestions();
                this.updateStats();

                await this.fetchNewGame();
            }

            async fetchNewGame() {
                try {
                    const response = await fetch('http://localhost:5000/api/new-game', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    });

                    if (!response.ok) {
                        throw new Error('Failed to fetch new game');
                    }

                    const data = await response.json();
                    this.targetAlbum = data;
                    this.gameId = data.game_id

                } catch (error) {
                    console.error('Error fetching new game:', error);
                    this.showError('Failed to start new game. Please try again.');
                }
            }

            async handleSearch(query) {
                clearTimeout(this.searchTimeout);

                if (query.length < 2) {
                    this.hideSuggestions();
                    return;
                }

                this.searchTimeout = setTimeout(async () => {
                    try {
                        const response = await fetch('http://localhost:5000/api/search-albums', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ query: query })
                        });

                        if (!response.ok) {
                            throw new Error('Search failed');
                        }

                        const data = await response.json();
                        this.showSuggestions(data.albums || []);

                    } catch (error) {
                        console.error('Error searching albums:', error);
                        this.hideSuggestions();
                    }
                }, 300);
            }

            showSuggestions(albums) {
                if (albums.length === 0) {
                    this.hideSuggestions();
                    return;
                }

                this.searchSuggestions.innerHTML = '';
                albums.slice(0, 8).forEach(album => {
                    const item = document.createElement('div');
                    item.className = 'suggestion-item';
                    item.innerHTML = `
                        <div class="album-name">${album.name}</div>
                        <div class="album-artist">${album.artist} • ${album.year}</div>
                    `;
                    item.addEventListener('click', () => {
                        this.selectAlbum(album);
                    });
                    this.searchSuggestions.appendChild(item);
                });

                this.searchSuggestions.style.display = 'block';
            }

            hideSuggestions() {
                this.searchSuggestions.style.display = 'none';
            }

            selectFirstSuggestion() {
                const firstSuggestion = this.searchSuggestions.querySelector('.suggestion-item');
                if (firstSuggestion) {
                    firstSuggestion.click();
                }
            }

            async selectAlbum(album) {
                if (this.gameEnded) return;

                this.hideSuggestions();
                this.searchInput.value = '';
                this.setLoadingState(true);

                try {
                    const response = await fetch('http://localhost:5000/api/guess', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            album_id: album.id,
                            album_name: album.name,
                            game_id: this.gameId
                        })
                    });

                    if (!response.ok) {
                        throw new Error('Failed to submit guess');
                    }

                    const result = await response.json();
                    this.processGuessResult(album, result);

                } catch (error) {
                    console.error('Error submitting guess:', error);
                    this.showError('Error submitting guess. Please try again.');
                } finally {
                    this.setLoadingState(false);
                }
            }

            processGuessResult(guessedAlbum, result) {
                this.currentGuesses++;

                // Add guess to display
                this.addGuessToDisplay(guessedAlbum, result.comparison);

                // Update stats
                this.updateStats();

                // Check win/lose conditions
                if (result.correct) {
                    this.handleWin();
                } else if (this.currentGuesses >= this.maxGuesses) {
                    this.handleLose(result.target_album);
                }
            }

            addGuessToDisplay(album, comparison) {
                const row = document.createElement('div');
                row.className = 'guess-row';

                // Album name
                const albumCell = this.createCell(album.name, comparison.album);
                albumCell.style.textAlign = 'left';
                albumCell.style.justifyContent = 'flex-start';

                // Artist
                const artistCell = this.createCell(album.artist, comparison.artist);
                artistCell.style.textAlign = 'left';
                artistCell.style.justifyContent = 'flex-start';

                // Year
                const yearCell = this.createCell(album.year, comparison.year);
                if (comparison.year.status === 'close') {
                    const arrow = comparison.year.direction === 'higher' ? 'arrow-up' : 'arrow-down';
                    yearCell.classList.add(arrow);
                }

                // Decade
                const decadeCell = this.createCell(this.getDecade(album.year), comparison.decade);

                // Genre
                const genreCell = this.createCell(album.genre, comparison.genre);
                genreCell.style.textAlign = 'left';
                genreCell.style.justifyContent = 'flex-start';

                // Track count
                const tracksCell = this.createCell(album.total_tracks || 'Unknown', comparison.tracks);
                if (comparison.tracks.status === 'close') {
                    const arrow = comparison.tracks.direction === 'higher' ? 'arrow-up' : 'arrow-down';
                    tracksCell.classList.add(arrow);
                }

                // Set mobile labels
                albumCell.setAttribute('data-label', 'Album');
                artistCell.setAttribute('data-label', 'Artist');
                yearCell.setAttribute('data-label', 'Year');
                decadeCell.setAttribute('data-label', 'Decade');
                genreCell.setAttribute('data-label', 'Genre');
                tracksCell.setAttribute('data-label', 'Tracks');

                row.appendChild(albumCell);
                row.appendChild(artistCell);
                row.appendChild(yearCell);
                row.appendChild(decadeCell);
                row.appendChild(genreCell);
                row.appendChild(tracksCell);

                this.guessesContainer.appendChild(row);
                row.scrollIntoView({ behavior: 'smooth' });
            }

            createCell(content, comparison) {
                const cell = document.createElement('div');
                cell.className = 'guess-cell';
                cell.textContent = content;

                switch (comparison.status) {
                    case 'correct':
                        cell.classList.add('cell-correct');
                        break;
                    case 'partial':
                        cell.classList.add('cell-partial');
                        break;
                    case 'close':
                        cell.classList.add('cell-year-close');
                        break;
                    case 'incorrect':
                    default:
                        cell.classList.add('cell-incorrect');
                        break;
                }

                return cell;
            }

            getDecade(year) {
                const decade = Math.floor(parseInt(year) / 10) * 10;
                return `${decade}s`;
            }

            handleWin() {
                this.gameEnded = true;
                this.searchInput.disabled = true;

                this.statusMessage.innerHTML = `
                    <div class="status-message status-win">
                        🎉 Congratulations! You guessed it in ${this.currentGuesses} ${this.currentGuesses === 1 ? 'try' : 'tries'}!
                        <button class="new-game-button" onclick="game.startNewGame()">Play Again</button>
                    </div>
                `;
            }

            handleLose(targetAlbum) {
                this.gameEnded = true;
                this.searchInput.disabled = true;

                this.statusMessage.innerHTML = `
                    <div class="status-message status-lose">
                        😔 Game Over! The album was "${targetAlbum.name}" by ${targetAlbum.artist}
                        <button class="new-game-button" onclick="game.startNewGame()">Try Again</button>
                    </div>
                `;
            }

            updateStats() {
                this.guessCountElement.textContent = this.currentGuesses;
                this.guessesLeftElement.textContent = this.maxGuesses - this.currentGuesses;
            }

            setLoadingState(loading) {
                if (loading) {
                    document.querySelector('.game-container').classList.add('loading');
                } else {
                    document.querySelector('.game-container').classList.remove('loading');
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
                }, 5000);
            }
        }

        // Initialize the game
        const game = new MusicWordleGame();