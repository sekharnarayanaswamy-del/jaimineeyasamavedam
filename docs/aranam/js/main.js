// Jaimineeya Samavedam Website JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                // Update URL without jumping
                history.pushState(null, null, this.getAttribute('href'));
            }
        });
    });

    // Highlight current section in jump links
    const observerOptions = {
        root: null,
        rootMargin: '-20% 0px -70% 0px',
        threshold: 0
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            const id = entry.target.getAttribute('id');
            const jumpLink = document.querySelector(`.jump-links a[href="#${id}"]`);
            if (jumpLink) {
                if (entry.isIntersecting) {
                    document.querySelectorAll('.jump-links a').forEach(a => a.classList.remove('active'));
                    jumpLink.classList.add('active');
                }
            }
        });
    }, observerOptions);

    document.querySelectorAll('.sama-entry').forEach(entry => {
        observer.observe(entry);
    });

    // Sidebar Jump Logic
    const jumpInput = document.getElementById('sidebar-jump');
    const searchBtn = document.querySelector('.search-btn');
    
    const handleJump = () => {
        const val = jumpInput ? jumpInput.value.trim() : '';
        if (!val) return;
        
        const path = window.location.pathname;
        let depth = 0;
        if (path.includes('/kandah/')) depth = 2;
        else if (path.includes('/classification/') || path.includes('/vargeekaran/')) depth = 1;
        
        const prefix = '../'.repeat(depth);
        const parts = val.split('.');
        
        if (parts.length >= 2) {
            const parvaId = `supersection_${parts[0]}`;
            const kandahId = parts[1];
            let url = `${prefix}kandah/${parvaId}/${kandahId}.html`;
            if (parts.length === 3) {
                url += `#sama-${parts[2]}`;
            }
            window.location.assign(url);
        }
    };

    if (jumpInput) {
        jumpInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                handleJump();
            }
        });
    }

    if (searchBtn) {
        searchBtn.addEventListener('click', function(e) {
            e.preventDefault();
            handleJump();
        });
    }
    
    // Audio error handling
    document.querySelectorAll('audio').forEach(audio => {
        audio.addEventListener('error', function() {
            const container = this.closest('.audio-section');
            if (container) {
                container.innerHTML = `
                    <div class="audio-pending">
                        <span>🎵</span>
                        <span>Audio coming soon</span>
                    </div>
                `;
            }
        });
    });
});
