// auth.js - Client-side authentication functionality

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get tab elements
    const tabs = document.querySelectorAll('.tab');
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    
    // Password visibility toggling
    const passwordToggles = document.querySelectorAll('.password-toggle');
    
    // Password strength elements
    const passwordInput = document.getElementById('signup-password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    
    // All form inputs
    const allInputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"]');
    
    // Tab switching functionality
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            
            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // Show corresponding form with animation
            if (tabName === 'login') {
                signupForm.style.opacity = '0';
                signupForm.style.transform = 'translateX(20px)';
                
                setTimeout(() => {
                    loginForm.classList.remove('hidden');
                    signupForm.classList.add('hidden');
                    
                    setTimeout(() => {
                        loginForm.style.opacity = '1';
                        loginForm.style.transform = 'translateX(0)';
                    }, 50);
                }, 300);
                
                // Update URL without page reload
                history.pushState({}, '', '/auth/login');
            } else if (tabName === 'signup') {
                loginForm.style.opacity = '0';
                loginForm.style.transform = 'translateX(-20px)';
                
                setTimeout(() => {
                    signupForm.classList.remove('hidden');
                    loginForm.classList.add('hidden');
                    
                    setTimeout(() => {
                        signupForm.style.opacity = '1';
                        signupForm.style.transform = 'translateX(0)';
                    }, 50);
                }, 300);
                
                // Update URL without page reload
                history.pushState({}, '', '/auth/signup');
            }
        });
    });
    
    // Input focus effects
    allInputs.forEach(input => {
        input.addEventListener('focus', function() {
            const label = this.parentElement.parentElement.querySelector('label');
            if (label) {
                label.style.color = 'var(--primary-color)';
            }
        });
        
        input.addEventListener('blur', function() {
            const label = this.parentElement.parentElement.querySelector('label');
            if (label) {
                label.style.color = '';
            }
        });
    });
    
    // Password visibility toggle
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const passwordInput = this.parentElement.querySelector('input');
            const icon = this.querySelector('i');
            
            // Toggle password visibility
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                passwordInput.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });
    
    // Password strength checker
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const strength = calculatePasswordStrength(password);
            
            updatePasswordStrengthIndicator(strength);
        });
    }
    
    // Password match validation
    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            if (passwordInput.value !== this.value) {
                this.setCustomValidity("Passwords don't match");
            } else {
                this.setCustomValidity('');
            }
        });
    }
    
    // Form validation for login
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;
            
            if (!validateEmail(email)) {
                e.preventDefault();
                showFormError(loginForm, 'Please enter a valid email address');
                return false;
            }
            
            if (!password) {
                e.preventDefault();
                showFormError(loginForm, 'Please enter your password');
                return false;
            }
            
            // Show loading animation
            const submitBtn = this.querySelector('button[type="submit"]');
            submitBtn.classList.add('loading');
            
            return true;
        });
    }
    
    // Form validation for signup
    if (signupForm) {
        signupForm.addEventListener('submit', function(e) {
            const firstName = document.getElementById('first_name').value;
            const lastName = document.getElementById('last_name').value;
            const email = document.getElementById('signup-email').value;
            const password = document.getElementById('signup-password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            
            // Clear previous errors
            clearFormErrors(signupForm);
            
            // Name validation
            if (!firstName.trim()) {
                e.preventDefault();
                showFormError(signupForm, 'First name is required');
                return false;
            }
            
            if (!lastName.trim()) {
                e.preventDefault();
                showFormError(signupForm, 'Last name is required');
                return false;
            }
            
            // Email validation
            if (!validateEmail(email)) {
                e.preventDefault();
                showFormError(signupForm, 'Please enter a valid email address');
                return false;
            }
            
            // Password validation
            if (calculatePasswordStrength(password) < 2) {
                e.preventDefault();
                showFormError(signupForm, 'Password is too weak. Please use a stronger password.');
                return false;
            }
            
            if (password !== confirmPassword) {
                e.preventDefault();
                showFormError(signupForm, 'Passwords do not match');
                return false;
            }
            
            // Show loading animation
            const submitBtn = this.querySelector('button[type="submit"]');
            submitBtn.classList.add('loading');
            
            return true;
        });
    }
    
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(message => {
                message.style.opacity = '0';
                message.style.transform = 'translateY(-10px)';
                setTimeout(() => {
                    message.style.display = 'none';
                }, 500);
            });
        }, 5000);
    }
    
    // Add animations to the form elements
    animateFormElements();
    
    // Animate background shapes
    animateBackgroundShapes();
});

// Animate background shapes for additional visual interest
function animateBackgroundShapes() {
    const shapes = document.querySelectorAll('.shape');
    
    shapes.forEach((shape, index) => {
        // Set random initial positions
        const randomX = Math.random() * 20 - 10; // -10 to 10
        const randomY = Math.random() * 20 - 10; // -10 to 10
        
        shape.style.transform = `translate(${randomX}px, ${randomY}px)`;
    });
}

// Password strength calculation
function calculatePasswordStrength(password) {
    let strength = 0;
    
    // Length check
    if (password.length >= 8) {
        strength += 1;
    }
    
    // Complexity checks
    if (password.match(/[a-z]/) && password.match(/[A-Z]/)) {
        strength += 1;
    }
    
    if (password.match(/\d/)) {
        strength += 1;
    }
    
    if (password.match(/[^a-zA-Z\d]/)) {
        strength += 1;
    }
    
    return strength;
}

// Update password strength visual indicator
function updatePasswordStrengthIndicator(strength) {
    const strengthMeter = document.querySelector('.strength-meter-fill');
    const strengthText = document.querySelector('.strength-text');
    
    strengthMeter.setAttribute('data-strength', strength);
    
    switch (strength) {
        case 0:
            strengthText.textContent = '';
            break;
        case 1:
            strengthText.textContent = 'Weak';
            strengthText.style.color = 'var(--error)';
            break;
        case 2:
            strengthText.textContent = 'Fair';
            strengthText.style.color = 'var(--warning)';
            break;
        case 3:
            strengthText.textContent = 'Good';
            strengthText.style.color = 'var(--info)';
            break;
        case 4:
            strengthText.textContent = 'Strong';
            strengthText.style.color = 'var(--success)';
            break;
    }
}

// Email validation
function validateEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

// Show form error
function showFormError(form, message) {
    const flashContainer = document.querySelector('.flash-messages');
    
    // Create error alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger';
    
    // Add icon
    const icon = document.createElement('i');
    icon.className = 'fas fa-exclamation-circle';
    alert.appendChild(icon);
    
    // Add message
    const messageText = document.createTextNode(message);
    alert.appendChild(messageText);
    
    // Add to flash messages container
    flashContainer.appendChild(alert);
    
    // Initially hide the alert for animation
    alert.style.opacity = '0';
    alert.style.transform = 'translateY(-10px)';
    
    // Trigger animation
    setTimeout(() => {
        alert.style.opacity = '1';
        alert.style.transform = 'translateY(0)';
    }, 10);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => {
            alert.remove();
        }, 500);
    }, 5000);
}

// Clear form errors
function clearFormErrors(form) {
    const flashContainer = document.querySelector('.flash-messages');
    // Only clear client-side generated errors, not server-side ones
    const clientErrors = flashContainer.querySelectorAll('.alert:not(.alert-success)');
    clientErrors.forEach(error => error.remove());
}

// Subtle form animations
function animateFormElements() {
    // Elements to animate
    const elements = [
        '.brand',
        '.hero-text',
        '.tabs',
        '.form-group',
        '.features .feature',
        '.floating-image'
    ];
    
    // Base delay
    let delay = 100;
    
    // Animate each group of elements
    elements.forEach(selector => {
        const items = document.querySelectorAll(selector);
        
        items.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            
            setTimeout(() => {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, delay + (index * 100));
        });
        
        // Increase delay for next group
        delay += items.length * 50;
    });
}