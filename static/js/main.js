/**
 * Acharya Prashant AI Chatbot - Main Landing Page JavaScript
 * Handles animations, scroll effects, and navigation
 */

document.addEventListener('DOMContentLoaded', () => {
    // ==================== SPLASH SCREEN ====================
    const splashScreen = document.getElementById('splashScreen');
    
    // Hide splash on click
    if (splashScreen) {
        splashScreen.addEventListener('click', () => {
            splashScreen.classList.add('hidden');
            document.body.style.overflow = 'auto';
        });
        
        // Auto-hide splash after 3 seconds
        setTimeout(() => {
            splashScreen.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }, 3000);
        
        // Prevent scroll while splash is visible
        document.body.style.overflow = 'hidden';
    }

    // ==================== NAVIGATION SCROLL ====================
    const navbar = document.getElementById('navbar');
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        // Add scrolled class for background
        if (currentScroll > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        
        lastScroll = currentScroll;
    });

    // ==================== HAMBURGER MENU ====================
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    const fullscreenMenu = document.getElementById('fullscreenMenu');
    
    if (hamburgerBtn && fullscreenMenu) {
        hamburgerBtn.addEventListener('click', () => {
            hamburgerBtn.classList.toggle('active');
            fullscreenMenu.classList.toggle('active');
            
            // Toggle body scroll
            if (fullscreenMenu.classList.contains('active')) {
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.overflow = 'auto';
            }
        });
        
        // Close menu when clicking a link
        const menuLinks = fullscreenMenu.querySelectorAll('a');
        menuLinks.forEach(link => {
            link.addEventListener('click', () => {
                hamburgerBtn.classList.remove('active');
                fullscreenMenu.classList.remove('active');
                document.body.style.overflow = 'auto';
            });
        });
    }

    // ==================== SCROLL REVEAL ANIMATIONS ====================
    const revealElements = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');
    
    const revealOnScroll = () => {
        const windowHeight = window.innerHeight;
        const revealPoint = 150;
        
        revealElements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            
            if (elementTop < windowHeight - revealPoint) {
                element.classList.add('active');
            }
        });
    };
    
    // Initial check
    revealOnScroll();
    
    // On scroll
    window.addEventListener('scroll', revealOnScroll);

    // ==================== SMOOTH SCROLL FOR ANCHOR LINKS ====================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // ==================== PARALLAX EFFECT ON HERO ====================
    const heroGlow = document.querySelector('.hero-glow');
    
    if (heroGlow) {
        window.addEventListener('mousemove', (e) => {
            const x = (e.clientX - window.innerWidth / 2) / 50;
            const y = (e.clientY - window.innerHeight / 2) / 50;
            
            heroGlow.style.transform = `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`;
        });
    }

    // ==================== MARQUEE DUPLICATION ====================
    // Duplicate marquee items for seamless loop
    const marquee = document.querySelector('.marquee');
    if (marquee) {
        const marqueeContent = marquee.innerHTML;
        marquee.innerHTML = marqueeContent + marqueeContent;
    }

    // ==================== GALLERY HOVER EFFECTS ====================
    const galleryItems = document.querySelectorAll('.gallery-item');
    
    galleryItems.forEach(item => {
        item.addEventListener('mouseenter', () => {
            galleryItems.forEach(other => {
                if (other !== item) {
                    other.style.opacity = '0.5';
                }
            });
        });
        
        item.addEventListener('mouseleave', () => {
            galleryItems.forEach(other => {
                other.style.opacity = '1';
            });
        });
    });

    // ==================== SPLIT PANEL HOVER ====================
    const splitPanels = document.querySelectorAll('.split-panel');
    
    splitPanels.forEach(panel => {
        panel.addEventListener('mouseenter', () => {
            panel.style.flex = '1.2';
        });
        
        panel.addEventListener('mouseleave', () => {
            panel.style.flex = '1';
        });
    });

    // ==================== TEXT HIGHLIGHT ON SCROLL ====================
    const quoteHighlight = document.querySelector('.quote-highlight');
    
    if (quoteHighlight) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    quoteHighlight.style.animation = 'glowPulse 2s ease-in-out infinite';
                }
            });
        }, { threshold: 0.5 });
        
        observer.observe(quoteHighlight);
    }

    // ==================== PRELOAD CHAT PAGE ====================
    // Prefetch chat page for faster navigation
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = '/chat';
    document.head.appendChild(link);

    console.log('✨ Acharya Prashant AI - Landing page initialized');
});
