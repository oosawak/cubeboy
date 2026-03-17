document.addEventListener('DOMContentLoaded', () => {
    // Reveal on scroll
    const reveals = document.querySelectorAll('.reveal');
    const revealOnScroll = () => {
        const windowHeight = window.innerHeight;
        reveals.forEach(el => {
            const elementTop = el.getBoundingClientRect().top;
            const elementVisible = 150;
            if (elementTop < windowHeight - elementVisible) {
                el.classList.add('active');
            }
        });
    };

    window.addEventListener('scroll', revealOnScroll);
    revealOnScroll(); // Initial check

    // Hero Parallax
    const heroImg = document.querySelector('.hero-bg img');
    window.addEventListener('mousemove', (e) => {
        const xPercent = (e.clientX / window.innerWidth - 0.5) * 2;
        const yPercent = (e.clientY / window.innerHeight - 0.5) * 2;
        
        if (heroImg) {
            heroImg.style.transform = `scale(1.1) translate(${xPercent * 20}px, ${yPercent * 20}px)`;
        }
    });

    // Logo hover interaction
    const logo = document.querySelector('.hero h1');
    if (logo) {
        logo.addEventListener('mouseover', () => {
            logo.style.filter = 'drop-shadow(0 0 30px rgba(0, 229, 255, 0.8))';
        });
        logo.addEventListener('mouseout', () => {
            logo.style.filter = 'drop-shadow(0 0 15px rgba(0, 229, 255, 0.4))';
        });
    }
    // BGM System
    const bgmFiles = [
        'BGM/ComfyUI_00001_.mp3',
        'BGM/ComfyUI_00002_.mp3',
        'BGM/ComfyUI_00003_.mp3',
        'BGM/ComfyUI_00004_.mp3'
    ];
    
    let currentTrackIndex = -1;
    const audio = document.getElementById('bgm-player');
    const musicBtn = document.getElementById('music-toggle');
    const musicIcon = musicBtn.querySelector('.icon');
    const musicText = musicBtn.querySelector('.text');
    let isPlaying = false;

    const updateUI = () => {
        if (isPlaying) {
            musicBtn.classList.add('playing');
            musicIcon.textContent = '🔊';
            musicText.textContent = 'Music: ON';
        } else {
            musicBtn.classList.remove('playing');
            musicIcon.textContent = '🔈';
            musicText.textContent = 'Music: OFF';
        }
    };

    const playRandomTrack = () => {
        let nextIndex;
        do {
            nextIndex = Math.floor(Math.random() * bgmFiles.length);
        } while (nextIndex === currentTrackIndex && bgmFiles.length > 1);
        
        currentTrackIndex = nextIndex;
        audio.src = bgmFiles[currentTrackIndex];
        audio.play().catch(err => console.log("Playback failed:", err));
        isPlaying = true;
        updateUI();
    };

    musicBtn.addEventListener('click', () => {
        if (!isPlaying) {
            if (currentTrackIndex === -1) {
                playRandomTrack();
            } else {
                audio.play();
                isPlaying = true;
                updateUI();
            }
        } else {
            audio.pause();
            isPlaying = false;
            updateUI();
        }
    });

    audio.addEventListener('ended', () => {
        playRandomTrack();
    });
});
