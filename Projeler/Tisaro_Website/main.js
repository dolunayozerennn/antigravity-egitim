// main.js - Simple animations and interactions

document.addEventListener('DOMContentLoaded', () => {
    // Animate bars on load
    const bars = document.querySelectorAll('.bar');
    
    // Store original heights
    bars.forEach(bar => {
        const height = bar.style.height;
        bar.style.height = '0%';
        bar.dataset.targetHeight = height;
    });

    // Trigger animation after a slight delay
    setTimeout(() => {
        bars.forEach(bar => {
            bar.style.height = bar.dataset.targetHeight;
        });
    }, 500);

    // Optional hover effects for the glass card
    const card = document.querySelector('.glass-card');
    card.addEventListener('mouseenter', () => {
        card.style.transform = 'translateY(-10px) scale(1.02)';
        card.style.transition = 'transform 0.3s ease';
    });
    
    card.addEventListener('mouseleave', () => {
        // Reset transform if not on mobile (which has a generic translateX)
        if(window.innerWidth > 1024) {
            card.style.transform = 'translateY(0) scale(1)';
        }
    });
});
