document.addEventListener('DOMContentLoaded', () => {
    const stages = document.querySelectorAll('.stage');
    const dots = document.querySelectorAll('.dot');
    const progressFill = document.getElementById('progressFill');
    let isScrolling = false;

    // Intersection Observer for Animations
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.5
    };

    const stageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                updateNav(entry.target);
            }
        });
    }, observerOptions);

    stages.forEach(stage => {
        stageObserver.observe(stage);
    });

    // Update Dots and Progress Bar
    function updateNav(activeStage) {
        const index = Array.from(stages).indexOf(activeStage);
        
        // Update Dots
        dots.forEach(dot => dot.classList.remove('active'));
        if(dots[index]) dots[index].classList.add('active');

        // Update Progress
        const percent = ((index) / (stages.length - 1)) * 100;
        progressFill.style.width = `${percent}%`;

        // Update Orb Colors based on stage to add dynamism
        updateBgColors(index);
    }

    function updateBgColors(index) {
        const orb1 = document.querySelector('.orb-1');
        const orb2 = document.querySelector('.orb-2');
        
        // Change colors slightly based on the index to give a feeling of evolution
        const colors = [
            ['#00d2ff', '#9d00ff'], // Stage 1 (Blue/Purple)
            ['#00f0ff', '#00d2ff'], // Stage 2 (Cyan/Blue)
            ['#0090ff', '#00ffd0'], // Stage 3 (Dark Blue/Teal)
            ['#ff5e00', '#ff003c']  // Stage 4 (Orange/Red)
        ];

        orb1.style.background = `radial-gradient(circle, ${colors[index][0]} 0%, transparent 70%)`;
        orb2.style.background = `radial-gradient(circle, ${colors[index][1]} 0%, transparent 70%)`;
    }

    // Dot click navigation
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => {
            stages[index].scrollIntoView({ behavior: 'smooth' });
        });
    });

    // Handle scroll progress bar calculation more smoothly
    document.body.addEventListener('scroll', () => {
        if (!isScrolling) {
            window.requestAnimationFrame(() => {
                const totalScroll = document.body.scrollTop;
                const windowHeight = document.body.scrollHeight - document.body.clientHeight;
                const scrollPercent = (totalScroll / windowHeight) * 100;
                
                // Only update progress bar smoothly if we want exact precision, 
                // but above we snap it by section. Doing both is fine for nice UX.
                progressFill.style.width = `${scrollPercent}%`;
                
                isScrolling = false;
            });
            isScrolling = true;
        }
    });
});
