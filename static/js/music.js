(function initMusicPlayer() {
    const dataEl = document.getElementById('music-tracks-data');
    const audio = document.getElementById('music-audio');
    if (!audio) return;

    let tracks = [];
    try {
        tracks = dataEl ? JSON.parse(dataEl.textContent || '[]') : [];
    } catch (e) {
        tracks = [];
    }

    const playBtn = document.getElementById('player-play');
    const prevBtn = document.getElementById('player-prev');
    const nextBtn = document.getElementById('player-next');
    const progress = document.getElementById('player-progress');
    const curEl = document.getElementById('player-current');
    const endEl = document.getElementById('player-end');
    const titleEl = document.getElementById('player-title');
    const artistEl = document.getElementById('player-artist');
    const coverEl = document.getElementById('player-cover');
    const heroCover = document.getElementById('music-hero-cover');
    const playlistPlay = document.getElementById('music-play-playlist');
    const listEl = document.getElementById('music-track-list');

    let currentIndex = -1;
    let isPlaying = false;

    function formatTime(sec) {
        if (!Number.isFinite(sec) || sec < 0) return '0:00';
        const m = Math.floor(sec / 60);
        const s = Math.floor(sec % 60);
        return `${m}:${s.toString().padStart(2, '0')}`;
    }

    function setCover(url) {
        const setBlock = (container, src) => {
            if (!container) return;
            container.innerHTML = '';
            if (src) {
                const img = document.createElement('img');
                img.src = src;
                img.alt = '';
                img.width = 56;
                img.height = 56;
                container.appendChild(img);
            } else {
                const ph = document.createElement('span');
                ph.className = container.id === 'music-hero-cover'
                    ? 'music-spotify-hero-placeholder'
                    : 'music-spotify-now-placeholder';
                ph.textContent = '♪';
                container.appendChild(ph);
            }
        };
        setBlock(coverEl, url);
        if (heroCover) {
            heroCover.innerHTML = '';
            if (url) {
                const img = document.createElement('img');
                img.src = url;
                img.alt = '';
                img.className = 'music-spotify-hero-img';
                heroCover.appendChild(img);
            } else {
                const ph = document.createElement('div');
                ph.className = 'music-spotify-hero-placeholder';
                ph.textContent = '💗';
                heroCover.appendChild(ph);
            }
        }
    }

    function highlightRow() {
        document.querySelectorAll('.music-spotify-row').forEach((row, i) => {
            row.classList.toggle('is-playing', i === currentIndex);
        });
    }

    function loadTrack(index) {
        if (index < 0 || index >= tracks.length) return;
        currentIndex = index;
        const t = tracks[index];
        audio.src = t.src;
        titleEl.textContent = t.title;
        artistEl.textContent = t.artist;
        setCover(t.cover || null);
        highlightRow();
        audio.load();
    }

    function togglePlay() {
        if (currentIndex < 0 && tracks.length) {
            loadTrack(0);
        }
        if (!audio.src) return;
        if (audio.paused) {
            audio.play().catch(() => {});
        } else {
            audio.pause();
        }
    }

    function playIndex(index) {
        if (index === currentIndex && audio.src) {
            togglePlay();
            return;
        }
        loadTrack(index);
        audio.play().catch(() => {});
    }

    function syncPlayButton() {
        const label = isPlaying ? 'Pausar' : 'Reproducir';
        if (playBtn) {
            playBtn.setAttribute('aria-label', label);
            playBtn.setAttribute('title', label);
            playBtn.textContent = isPlaying ? '⏸' : '▶';
        }
    }

    audio.addEventListener('play', () => {
        isPlaying = true;
        syncPlayButton();
    });
    audio.addEventListener('pause', () => {
        isPlaying = false;
        syncPlayButton();
    });
    audio.addEventListener('timeupdate', () => {
        if (!progress || !audio.duration) return;
        const pct = (audio.currentTime / audio.duration) * 100;
        progress.value = Number.isFinite(pct) ? pct : 0;
        if (curEl) curEl.textContent = formatTime(audio.currentTime);
    });
    audio.addEventListener('loadedmetadata', () => {
        if (endEl) endEl.textContent = formatTime(audio.duration);
        const durCell = document.querySelector(`[data-duration-for="${currentIndex}"]`);
        if (durCell) durCell.textContent = formatTime(audio.duration);
    });
    audio.addEventListener('ended', () => {
        if (currentIndex < tracks.length - 1) {
            playIndex(currentIndex + 1);
        } else {
            isPlaying = false;
            syncPlayButton();
        }
    });

    playBtn?.addEventListener('click', togglePlay);
    prevBtn?.addEventListener('click', () => {
        if (currentIndex > 0) playIndex(currentIndex - 1);
    });
    nextBtn?.addEventListener('click', () => {
        if (currentIndex < tracks.length - 1) playIndex(currentIndex + 1);
    });

    progress?.addEventListener('input', () => {
        if (!audio.duration) return;
        audio.currentTime = (Number(progress.value) / 100) * audio.duration;
    });

    listEl?.querySelectorAll('.music-spotify-row').forEach((row) => {
        row.addEventListener('click', () => {
            const i = parseInt(row.getAttribute('data-index'), 10);
            if (!Number.isNaN(i)) playIndex(i);
        });
    });

    playlistPlay?.addEventListener('click', () => {
        if (!tracks.length) return;
        if (currentIndex < 0) loadTrack(0);
        audio.play().catch(() => {});
    });

    tracks.forEach((t, i) => {
        const a = new Audio();
        a.preload = 'metadata';
        a.src = t.src;
        a.addEventListener('loadedmetadata', () => {
            const durCell = document.querySelector(`[data-duration-for="${i}"]`);
            if (durCell) durCell.textContent = formatTime(a.duration);
        });
    });

    syncPlayButton();
})();
