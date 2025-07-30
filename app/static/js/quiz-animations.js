/**
 * ŠUTĒRU QUIZ ANIMATIONS - KHAN ACADEMY STYLE
 * Advanced JavaScript animations for quiz feedback
 */

class QuizAnimations {
    constructor() {
        this.streak = 0;
        this.totalCorrect = 0;
        this.animationsEnabled = true;
        this.currentModal = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.createAnimationOverlay();
    }
    
    setupEventListeners() {
        // Option selection animations
        document.querySelectorAll('.option-item').forEach(option => {
            option.addEventListener('click', (e) => {
                this.animateOptionSelection(e.target.closest('.option-item'));
            });
        });
        
        // Submit button animation
        const submitBtn = document.getElementById('submit-btn');
        if (submitBtn) {
            submitBtn.addEventListener('click', (e) => {
                this.animateButtonPress(e.target);
            });
        }
    }
    
    createAnimationOverlay() {
        if (document.querySelector('.success-animation-overlay')) return;
        
        const overlay = document.createElement('div');
        overlay.className = 'success-animation-overlay';
        overlay.innerHTML = `
            <div class="confetti-container"></div>
            <div class="stars-container"></div>
        `;
        document.body.appendChild(overlay);
    }
    
    // ===== SUCCESS ANIMATIONS =====
    
    showSuccessAnimation(points = 10) {
        this.streak++;
        this.totalCorrect++;
        
        // Create confetti
        this.createConfetti();
        
        // Show points animation
        this.animatePointsGained(points);
        
        // Show success modal
        this.showSuccessModal(points);
        
        // Create stars
        this.createStars();
        
        // Check for streak bonuses
        if (this.streak >= 3) {
            setTimeout(() => this.showStreakAnimation(), 1000);
        }
        
        // Add screen shake for extra impact
        this.addScreenShake();
    }
    
    createConfetti() {
        const container = document.querySelector('.confetti-container');
        const colors = 8; // Number of confetti types
        
        // Generate 50 confetti pieces
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.className = `confetti type-${Math.floor(Math.random() * colors) + 1}`;
            
            // Random positioning
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.animationDelay = Math.random() * 2 + 's';
            confetti.style.animationDuration = (Math.random() * 2 + 2) + 's';
            
            container.appendChild(confetti);
            
            // Remove after animation
            setTimeout(() => {
                if (confetti.parentNode) {
                    confetti.parentNode.removeChild(confetti);
                }
            }, 4000);
        }
    }
    
    animatePointsGained(points) {
        const overlay = document.querySelector('.success-animation-overlay');
        const pointsEl = document.createElement('div');
        pointsEl.className = 'points-gained-animation';
        pointsEl.textContent = `+${points} pontos!`;
        
        overlay.appendChild(pointsEl);
        
        setTimeout(() => {
            if (pointsEl.parentNode) {
                pointsEl.parentNode.removeChild(pointsEl);
            }
        }, 2000);
    }
    
    showSuccessModal(points) {
        // Remove any existing modal
        this.hideCurrentModal();
        
        const modal = document.createElement('div');
        modal.className = 'success-feedback-modal';
        
        const messages = [
            'Excelente!',
            'Perfeito!', 
            'Incrível!',
            'Fantástico!',
            'Brilhante!'
        ];
        
        const message = messages[Math.floor(Math.random() * messages.length)];
        
        modal.innerHTML = `
            <div class="success-icon-animated">
                <i class="fas fa-check"></i>
            </div>
            <h3 class="success-title-animated">${message}</h3>
            <p class="success-subtitle-animated">Você ganhou ${points} pontos e ajudou a doar alimentos!</p>
        `;
        
        document.body.appendChild(modal);
        this.currentModal = modal;
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            this.hideModal(modal);
        }, 3000);
    }
    
    createStars() {
        const container = document.querySelector('.stars-container');
        
        // Generate 8 stars
        for (let i = 0; i < 8; i++) {
            const star = document.createElement('div');
            star.className = 'star';
            star.innerHTML = '⭐';
            
            // Random positioning
            star.style.left = Math.random() * 100 + '%';
            star.style.top = Math.random() * 100 + '%';
            star.style.animationDelay = Math.random() * 2 + 's';
            
            container.appendChild(star);
            
            // Remove after animation
            setTimeout(() => {
                if (star.parentNode) {
                    star.parentNode.removeChild(star);
                }
            }, 3000);
        }
    }
    
    showStreakAnimation() {
        const streakEl = document.createElement('div');
        streakEl.className = 'streak-animation';
        streakEl.textContent = `🔥 ${this.streak} acertos seguidos!`;
        
        document.body.appendChild(streakEl);
        
        setTimeout(() => {
            if (streakEl.parentNode) {
                streakEl.parentNode.removeChild(streakEl);
            }
        }, 2000);
    }
    
    addScreenShake() {
        document.body.style.animation = 'screenShake 0.5s ease-in-out';
        setTimeout(() => {
            document.body.style.animation = '';
        }, 500);
    }
    
    // ===== ERROR ANIMATIONS =====
    
    showErrorAnimation(correctAnswer) {
        this.streak = 0; // Reset streak
        
        // Show error modal
        this.showErrorModal(correctAnswer);
        
        // Add subtle screen shake
        this.addErrorShake();
    }
    
    showErrorModal(correctAnswer) {
        // Remove any existing modal
        this.hideCurrentModal();
        
        const modal = document.createElement('div');
        modal.className = 'incorrect-feedback-modal';
        
        modal.innerHTML = `
            <div class="incorrect-icon-animated">
                <i class="fas fa-times"></i>
            </div>
            <h3 class="success-title-animated">Quase lá!</h3>
            <p class="success-subtitle-animated">Não desista! Aprender faz parte do processo.</p>
            ${correctAnswer ? `<div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.2); border-radius: 12px;">
                <div style="font-size: 0.9rem; opacity: 0.8;">Resposta correta:</div>
                <div style="font-weight: 600; margin-top: 0.5rem;">${correctAnswer}</div>
            </div>` : ''}
        `;
        
        document.body.appendChild(modal);
        this.currentModal = modal;
        
        // Auto-hide after 4 seconds
        setTimeout(() => {
            this.hideModal(modal);
        }, 4000);
    }
    
    addErrorShake() {
        const quiz = document.querySelector('.question-card-modern');
        if (quiz) {
            quiz.style.animation = 'errorShake 0.5s ease-in-out';
            setTimeout(() => {
                quiz.style.animation = '';
            }, 500);
        }
    }
    
    // ===== INTERACTION ANIMATIONS =====
    
    animateOptionSelection(option) {
        // Add ripple effect
        option.classList.add('ripple');
        setTimeout(() => option.classList.remove('ripple'), 300);
        
        // Add selection pulse
        option.classList.add('selecting');
        setTimeout(() => option.classList.remove('selecting'), 300);
    }
    
    animateButtonPress(button) {
        button.classList.add('pressed');
        setTimeout(() => button.classList.remove('pressed'), 200);
    }
    
    // ===== UTILITY METHODS =====
    
    hideCurrentModal() {
        if (this.currentModal) {
            this.hideModal(this.currentModal);
        }
    }
    
    hideModal(modal) {
        if (modal && modal.parentNode) {
            modal.classList.add('hide');
            setTimeout(() => {
                if (modal.parentNode) {
                    modal.parentNode.removeChild(modal);
                }
                if (this.currentModal === modal) {
                    this.currentModal = null;
                }
            }, 300);
        }
    }
    
    // Reset animations for new question
    resetForNewQuestion() {
        // Clear confetti
        const confettiContainer = document.querySelector('.confetti-container');
        if (confettiContainer) {
            confettiContainer.innerHTML = '';
        }
        
        // Clear stars
        const starsContainer = document.querySelector('.stars-container');
        if (starsContainer) {
            starsContainer.innerHTML = '';
        }
        
        // Hide any modal
        this.hideCurrentModal();
    }
    
    // Enable/disable animations
    toggleAnimations(enabled) {
        this.animationsEnabled = enabled;
        const overlay = document.querySelector('.success-animation-overlay');
        if (overlay) {
            overlay.style.display = enabled ? 'block' : 'none';
        }
    }
}

// Additional CSS for screen shake and error animations
const additionalStyles = `
    @keyframes screenShake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-2px); }
        75% { transform: translateX(2px); }
    }
    
    @keyframes errorShake {
        0%, 100% { transform: translateX(0); }
        20% { transform: translateX(-5px); }
        40% { transform: translateX(5px); }
        60% { transform: translateX(-3px); }
        80% { transform: translateX(3px); }
    }
`;

// Add additional styles to head
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);

// Global instance
let quizAnimations;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    quizAnimations = new QuizAnimations();
});

// Global functions for triggering animations
window.triggerSuccessAnimation = function(points = 10) {
    if (quizAnimations) {
        quizAnimations.showSuccessAnimation(points);
    }
};

window.triggerErrorAnimation = function(correctAnswer = '') {
    if (quizAnimations) {
        quizAnimations.showErrorAnimation(correctAnswer);
    }
};

window.resetQuizAnimations = function() {
    if (quizAnimations) {
        quizAnimations.resetForNewQuestion();
    }
};

// Auto-trigger animations based on Flask flash messages
document.addEventListener('DOMContentLoaded', function() {
    // Check for success messages
    const successAlerts = document.querySelectorAll('.alert-success');
    successAlerts.forEach(alert => {
        if (alert.textContent.includes('Resposta correta')) {
            setTimeout(() => triggerSuccessAnimation(10), 100);
        }
    });
    
    // Check for error state (when correct answer is shown)
    const correctAnswerDiv = document.querySelector('.correct-answer-text');
    if (correctAnswerDiv) {
        const correctAnswer = correctAnswerDiv.textContent;
        setTimeout(() => triggerErrorAnimation(correctAnswer), 100);
    }
}); 