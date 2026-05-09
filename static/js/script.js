(function initSubpageToHomeRedirect() {
    const INNER_PATHS = new Set(['/carta', '/galeria', '/cancion']);
    const path = (window.location.pathname || '/').replace(/\/$/, '') || '/';
    if (!INNER_PATHS.has(path)) return;
    if (sessionStorage.getItem('mom_allow_subpage')) {
        sessionStorage.removeItem('mom_allow_subpage');
        return;
    }
    window.location.replace('/');
})();

(function markInternalNavToSubpages() {
    const INNER_PATHS = new Set(['/carta', '/galeria', '/cancion']);
    document.addEventListener('click', (event) => {
        const anchor = event.target.closest('a');
        if (!anchor) return;
        const href = anchor.getAttribute('href');
        if (!href || href.startsWith('//') || /^https?:/i.test(href)) return;
        if (!href.startsWith('/')) return;
        if (anchor.target === '_blank' || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        const pathOnly = href.split('?')[0].split('#')[0];
        const subpath = pathOnly.replace(/\/$/, '') || '/';
        if (INNER_PATHS.has(subpath)) sessionStorage.setItem('mom_allow_subpage', '1');
        if (subpath === '/') {
            sessionStorage.setItem('mom_skip_intro_nav', '1');
            const hashPart = href.includes('#') ? href.split('#').pop() : '';
            sessionStorage.setItem('mom_scroll_after_skip', hashPart || 'inicio');
        }
    }, true);
})();

function scrollToMainInicio() {
    const target = document.getElementById('inicio');
    if (!target) return;
    requestAnimationFrame(() => {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
}

function scrollToIdOrInicio(id) {
    const safe = id && /^[a-zA-Z0-9_-]+$/.test(id) ? id : 'inicio';
    const target = document.getElementById(safe) || document.getElementById('inicio');
    if (!target) return;
    requestAnimationFrame(() => {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
}

(function stripIntroIfNavigatingHomeWithoutReload() {
    const path = (window.location.pathname || '/').replace(/\/$/, '') || '/';
    if (path !== '/') return;

    function isPageReload() {
        const entry = performance.getEntriesByType?.('navigation')?.[0];
        if (entry && entry.type === 'reload') return true;
        return typeof performance.navigation !== 'undefined' && performance.navigation.type === 1;
    }

    if (isPageReload()) {
        sessionStorage.removeItem('mom_skip_intro_nav');
        sessionStorage.removeItem('mom_scroll_after_skip');
        return;
    }

    if (!sessionStorage.getItem('mom_skip_intro_nav')) return;

    const el = document.getElementById('dev-intro');
    if (!el) return;

    el.remove();
    document.body.classList.remove('intro-lock');
    document.body.classList.add('page-enter');
    sessionStorage.removeItem('mom_skip_intro_nav');
    const scrollId = sessionStorage.getItem('mom_scroll_after_skip');
    sessionStorage.removeItem('mom_scroll_after_skip');
    if ('scrollRestoration' in history) {
        history.scrollRestoration = 'auto';
    }

    if (window.location.hash && window.location.hash.length > 1) {
        scrollToIdOrInicio(window.location.hash.slice(1));
    } else {
        scrollToIdOrInicio(scrollId || 'inicio');
    }
})();

const colorBtn = document.getElementById('color-btn');
const menuToggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('.nav');

const intro = document.getElementById('dev-intro');
const introLoader = document.getElementById('intro-loader');
const enterSiteBtn = document.getElementById('enter-site');
const soundToggle = document.getElementById('sound-toggle');
const codeStream = document.getElementById('code-stream');
const tagline = document.getElementById('intro-tagline');
const dashboard = document.getElementById('future-dashboard');
const introCanvas = document.getElementById('intro-canvas');

if ('scrollRestoration' in history) {
    history.scrollRestoration = intro ? 'manual' : 'auto';
}

function moveToPageStart() {
    window.scrollTo(0, 0);
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
}

if (intro) {
    moveToPageStart();
    window.addEventListener('pageshow', moveToPageStart, { once: true });
    window.addEventListener('load', moveToPageStart, { once: true });
}

const palettes = [
    {
        accent: '#ff4f9a',
        accent2: '#ffb3d9',
        glow: 'rgba(255, 79, 154, 0.24)',
        shadow: 'rgba(255, 79, 154, 0.26)',
        background: '#ffd6e8'
    },
    {
        accent: '#ff7ab8',
        accent2: '#ffd166',
        glow: 'rgba(255, 122, 184, 0.26)',
        shadow: 'rgba(190, 24, 93, 0.32)',
        background: '#30071a'
    },
    {
        accent: '#e879f9',
        accent2: '#f9a8d4',
        glow: 'rgba(232, 121, 249, 0.24)',
        shadow: 'rgba(168, 85, 247, 0.28)',
        background: '#25071f'
    },
    {
        accent: '#fb7185',
        accent2: '#fbcfe8',
        glow: 'rgba(251, 113, 133, 0.26)',
        shadow: 'rgba(225, 29, 72, 0.3)',
        background: '#2b0710'
    }
];

let paletteIndex = 0;

// Cargar color guardado al iniciar
function loadSavedColor() {
    console.log('Cargando color guardado...');
    const savedIndex = localStorage.getItem('selectedPaletteIndex');
    console.log('Índice guardado:', savedIndex);
    
    // SIEMPRE cargar el color guardado si existe, sino rosa predeterminado
    if (savedIndex !== null) {
        paletteIndex = parseInt(savedIndex);
        console.log('Aplicando color guardado:', paletteIndex);
    } else {
        paletteIndex = 0;
        console.log('No hay color guardado, aplicando rosa predeterminado');
    }
    
    applyPalette(paletteIndex);
}

// Aplicar paleta de colores
function applyPalette(index) {
    const palette = palettes[index];
    document.documentElement.style.setProperty('--accent', palette.accent);
    document.documentElement.style.setProperty('--accent-2', palette.accent2);
    document.documentElement.style.setProperty('--accent-glow', palette.glow);
    document.documentElement.style.setProperty('--shadow-2', `0 20px 64px ${palette.shadow}`);
    document.documentElement.style.setProperty('--shadow-3', `0 28px 90px ${palette.shadow}`);
    document.documentElement.style.setProperty('--background', palette.background);
}

colorBtn?.addEventListener('click', function() {
    paletteIndex = (paletteIndex + 1) % palettes.length;
    console.log('Botón presionado, nuevo índice:', paletteIndex);
    applyPalette(paletteIndex);
    localStorage.setItem('selectedPaletteIndex', paletteIndex);
    console.log('Color guardado en localStorage:', localStorage.getItem('selectedPaletteIndex'));
});

// Cargar color guardado cuando la página carga
document.addEventListener('DOMContentLoaded', function() {
    console.log('Página cargada, navigation.type:', performance.navigation.type);
    
    // Limpiar localStorage solo si es recarga manual (F5 o Ctrl+R)
    if (performance.navigation.type === 1) {
        console.log('Detectada recarga manual, limpiando localStorage');
        localStorage.removeItem('selectedPaletteIndex');
    }
    
    loadSavedColor();
});

function setNavOpen(isOpen) {
    if (!nav || !menuToggle) return;
    nav.classList.toggle('is-open', isOpen);
    menuToggle.setAttribute('aria-expanded', String(isOpen));
    menuToggle.setAttribute('aria-label', isOpen ? 'Cerrar menú' : 'Abrir menú');
}

menuToggle?.addEventListener('click', function() {
    setNavOpen(!nav.classList.contains('is-open'));
});

nav?.querySelectorAll('a, button').forEach((item) => {
    item.addEventListener('click', () => setNavOpen(false));
});

const introLines = [
    '$ iniciar_sorpresa --para=mama',
    '> Cargando recuerdos bonitos...',
    '> Preparando flores, abrazos y sonrisas...',
    '> Escribiendo mensaje: gracias por todo',
    '> Guardando amor infinito en el corazon',
    '> Compilando pagina hecha con carino',
    'estado: Feliz Dia de la Madre, mama.'
];

const taglines = [
    'Porque ningún código puede medir todo lo que significas para mí.',
    'Esta página está hecha con amor, recuerdos y gratitud.',
    'Gracias por tu fuerza, tu ternura y por estar siempre conmigo.'
];

let soundEnabled = false;
let audioContext;

function playInterfaceTone() {
    if (!soundEnabled) return;

    audioContext = audioContext || new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();

    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(460, audioContext.currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(920, audioContext.currentTime + 0.18);
    gain.gain.setValueAtTime(0.0001, audioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.045, audioContext.currentTime + 0.03);
    gain.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + 0.38);

    oscillator.connect(gain);
    gain.connect(audioContext.destination);
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.4);
}

function typeIntroCode() {
    if (!codeStream) return;

    let lineIndex = 0;
    let charIndex = 0;
    codeStream.textContent = '';

    const typeNext = () => {
        if (lineIndex >= introLines.length) {
            return;
        }

        const line = introLines[lineIndex];
        codeStream.textContent += line[charIndex] || '';
        charIndex += 1;

        if (charIndex > line.length) {
            codeStream.textContent += '\n';
            lineIndex += 1;
            charIndex = 0;
            setTimeout(typeNext, 260);
            return;
        }

        setTimeout(typeNext, 22 + Math.random() * 22);
    };

    typeNext();
}

function rotateTaglines() {
    if (!tagline) return;

    let index = 0;
    setInterval(() => {
        index = (index + 1) % taglines.length;
        if (window.gsap) {
            gsap.to(tagline, {
                opacity: 0,
                y: 8,
                duration: 0.28,
                onComplete: () => {
                    tagline.textContent = taglines[index];
                    gsap.to(tagline, { opacity: 1, y: 0, duration: 0.42, ease: 'power2.out' });
                }
            });
        } else {
            tagline.textContent = taglines[index];
        }
    }, 3300);
}

function revealIntro() {
    introLoader?.classList.add('is-complete');
    typeIntroCode();
    rotateTaglines();

    if (window.gsap) {
        gsap.timeline({ defaults: { ease: 'power3.out' } })
            .to('.intro-copy', { opacity: 1, y: 0, duration: 0.9 })
            .to('.future-dashboard', { opacity: 1, y: 0, duration: 0.9 }, '-=0.58')
            .from('.stack-marquee span', { opacity: 0, y: 14, stagger: 0.055, duration: 0.5 }, '-=0.42')
            .from('.metric-card', { opacity: 0, y: 12, stagger: 0.08, duration: 0.5 }, '-=0.38');
    } else {
        document.querySelectorAll('.intro-copy, .future-dashboard').forEach((element) => {
            element.style.opacity = '1';
            element.style.transform = 'translate3d(0, 0, 0)';
        });
    }
}

function closeIntro() {
    moveToPageStart();
    playInterfaceTone();
    intro?.classList.add('is-transitioning');

    setTimeout(() => {
        intro?.classList.add('is-hidden');
        document.body.classList.remove('intro-lock');
        document.body.classList.add('page-enter');
        if ('scrollRestoration' in history) {
            history.scrollRestoration = 'auto';
        }
        scrollToMainInicio();
    }, 620);

    setTimeout(() => intro?.remove(), 1500);
}

function initIntro3D() {
    if (!introCanvas || !window.THREE) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(62, window.innerWidth / window.innerHeight, 0.1, 1200);
    camera.position.z = 34;

    const renderer = new THREE.WebGLRenderer({
        canvas: introCanvas,
        antialias: true,
        alpha: true,
        powerPreference: 'high-performance'
    });

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.7));
    renderer.setSize(window.innerWidth, window.innerHeight);

    const geometry = new THREE.BufferGeometry();
    const count = window.innerWidth < 640 ? 650 : 1400;
    const positions = new Float32Array(count * 3);

    for (let i = 0; i < count; i += 1) {
        positions[i * 3] = (Math.random() - 0.5) * 95;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 55;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 55;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({
        color: 0xffb3d9,
        size: 0.1,
        transparent: true,
        opacity: 0.86,
        blending: THREE.AdditiveBlending
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    const ringGeometry = new THREE.TorusGeometry(12, 0.025, 12, 128);
    const ringMaterial = new THREE.MeshBasicMaterial({
        color: 0xfbbf24,
        transparent: true,
        opacity: 0.42
    });
    const ring = new THREE.Mesh(ringGeometry, ringMaterial);
    ring.rotation.x = Math.PI / 2.7;
    scene.add(ring);

    function resize() {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    }

    function animate() {
        if (!document.body.contains(introCanvas)) return;
        particles.rotation.y += 0.0016;
        particles.rotation.x += 0.0006;
        ring.rotation.z += 0.004;
        renderer.render(scene, camera);
        requestAnimationFrame(animate);
    }

    window.addEventListener('resize', resize);
    animate();
}

function initIntroParallax() {
    if (!intro || !dashboard) return;

    intro.addEventListener('mousemove', (event) => {
        const x = (event.clientX / window.innerWidth - 0.5) * 2;
        const y = (event.clientY / window.innerHeight - 0.5) * 2;
        dashboard.style.transform = `translate3d(${x * 8}px, ${y * 8}px, 0) rotateY(${x * 4}deg) rotateX(${-y * 4}deg)`;
    });

    intro.addEventListener('mouseleave', () => {
        dashboard.style.transform = 'translate3d(0, 0, 0)';
    });
}

if (intro) {
    initIntro3D();
    initIntroParallax();
    setTimeout(revealIntro, 1400);
    enterSiteBtn?.addEventListener('click', closeIntro);
    soundToggle?.addEventListener('click', () => {
        soundEnabled = !soundEnabled;
        soundToggle.setAttribute('aria-pressed', String(soundEnabled));
        if (soundEnabled) playInterfaceTone();
    });
    window.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === 'Escape') closeIntro();
    });
}

function initScrollReveal() {
    const revealItems = document.querySelectorAll('.hero, .web-slider, .messages, .message-card, .letter-hero, .letter-terminal, .gallery-hero, .apple-gallery, .photo-tile, .memory-slider-section, footer:not(.music-spotify-footer-note)');
    if (!revealItems.length) return;

    revealItems.forEach((item, index) => {
        item.classList.add('scroll-reveal');
        item.style.setProperty('--reveal-delay', `${Math.min(index * 55, 260)}ms`);
    });

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || !('IntersectionObserver' in window)) {
        revealItems.forEach((item) => item.classList.add('is-visible'));
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
        });
    }, {
        threshold: 0.16,
        rootMargin: '0px 0px -8% 0px'
    });

    revealItems.forEach((item) => observer.observe(item));
}

initScrollReveal();

function initLetterEditor() {
    const editor = document.getElementById('letter-editor');
    const status = document.getElementById('letter-save-status');
    if (!editor) return;

    const savedLetter = localStorage.getItem('carta-para-mama');
    if (savedLetter) {
        editor.value = savedLetter;
        if (status) status.textContent = 'Carta recuperada y lista para seguir escribiendo.';
    }

    let saveTimer;
    editor.addEventListener('input', () => {
        clearTimeout(saveTimer);
        if (status) status.textContent = 'Guardando...';
        saveTimer = setTimeout(() => {
            localStorage.setItem('carta-para-mama', editor.value);
            if (status) status.textContent = 'Guardado automáticamente.';
        }, 350);
    });
}

initLetterEditor();

function initMemorySlider() {
    const track = document.querySelector('.memory-track');
    const slides = document.querySelectorAll('.memory-slide');
    const prev = document.querySelector('.memory-prev');
    const next = document.querySelector('.memory-next');
    const dotsWrap = document.querySelector('.memory-dots');
    if (!track || !slides.length || !dotsWrap) return;

    let activeIndex = 0;

    slides.forEach((_, index) => {
        const dot = document.createElement('button');
        dot.className = 'memory-dot';
        dot.type = 'button';
        dot.setAttribute('aria-label', `Ver foto ${index + 1}`);
        dot.addEventListener('click', () => goToMemory(index));
        dotsWrap.appendChild(dot);
    });

    const dots = dotsWrap.querySelectorAll('.memory-dot');

    function updateMemorySlider() {
        track.style.transform = `translateX(-${activeIndex * 100}%)`;
        dots.forEach((dot, index) => {
            dot.classList.toggle('is-active', index === activeIndex);
        });
    }

    function goToMemory(index) {
        activeIndex = (index + slides.length) % slides.length;
        updateMemorySlider();
    }

    prev?.addEventListener('click', () => goToMemory(activeIndex - 1));
    next?.addEventListener('click', () => goToMemory(activeIndex + 1));
    setInterval(() => goToMemory(activeIndex + 1), 5200);
    updateMemorySlider();
}

initMemorySlider();

// Slider functionality
let currentSlide = 0;
const slides = document.querySelectorAll('.slide-card');
const dots = document.querySelectorAll('.slider-dot');
const prevBtn = document.querySelector('.slider-nav.prev');
const nextBtn = document.querySelector('.slider-nav.next');
const totalSlides = slides.length;

function updateSlider() {
    const track = document.querySelector('.slider-track');
    if (!track) return;
    track.style.transform = `translateX(-${currentSlide * 100}%)`;
    dots.forEach((dot, index) => {
        dot.classList.toggle('active', index === currentSlide);
    });
}

function nextSlide() {
    currentSlide = (currentSlide + 1) % totalSlides;
    updateSlider();
}

function prevSlide() {
    currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
    updateSlider();
}

function goToSlide(index) {
    currentSlide = index;
    updateSlider();
}

// Auto-play
if (totalSlides > 0) {
    setInterval(nextSlide, 5000); // Change slide every 5 seconds
}

// Event listeners
nextBtn?.addEventListener('click', nextSlide);
prevBtn?.addEventListener('click', prevSlide);
dots.forEach((dot, index) => {
    dot.addEventListener('click', () => goToSlide(index));
});

// Initialize
if (totalSlides > 0) {
    updateSlider();
}
