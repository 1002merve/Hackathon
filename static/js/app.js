/* Enhanced BinaryGirls Main JavaScript with Video Features */

// Enhanced Configuration and Constants
const CONFIG = {
    ANIMATION_DURATION: 300,
    NOTIFICATION_DURATION: 5000,
    TYPING_DELAY: 500,
    VIDEO_GENERATION_TIME: 3000,
    DEBOUNCE_DELAY: 300,
    THROTTLE_LIMIT: 100,
    MAX_MESSAGE_LENGTH: 500,
    MAX_VIDEO_DURATION: 600, // 10 minutes
    API_ENDPOINTS: {
        CHAT: '/core/chat/',
        VIDEO_GENERATE: '/api/generate-video/',
        USER_STATS: '/core/api/user-stats/'
    }
};

// Enhanced Dark Mode Management
class DarkModeManager {
    constructor() {
        this.init();
    }

    init() {
        const savedMode = localStorage.getItem('darkMode');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (savedMode !== null) {
            this.setDarkMode(savedMode === 'true');
        } else if (prefersDark) {
            this.setDarkMode(true);
        }

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (localStorage.getItem('darkMode') === null) {
                this.setDarkMode(e.matches);
            }
        });
    }

    setDarkMode(isDark) {
        const html = document.documentElement;
        const sunIcon = document.getElementById('sunIcon');
        const moonIcon = document.getElementById('moonIcon');

        if (isDark) {
            html.classList.add('dark');
            if (sunIcon) sunIcon.classList.add('hidden');
            if (moonIcon) moonIcon.classList.remove('hidden');
        } else {
            html.classList.remove('dark');
            if (sunIcon) sunIcon.classList.remove('hidden');
            if (moonIcon) moonIcon.classList.add('hidden');
        }

        localStorage.setItem('darkMode', isDark.toString());
        
        // Dispatch custom event for theme change
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { isDark } }));
    }

    toggle() {
        const html = document.documentElement;
        const isDark = !html.classList.contains('dark');
        this.setDarkMode(isDark);
        return isDark;
    }
}

// Enhanced Notification System
class NotificationManager {
    constructor() {
        this.container = this.createContainer();
        this.notifications = new Map();
        document.body.appendChild(this.container);
    }

    createContainer() {
        const container = document.createElement('div');
        container.className = 'fixed top-4 right-4 z-50 space-y-2 pointer-events-none';
        container.id = 'notification-container';
        return container;
    }

    show(message, type = 'info', duration = CONFIG.NOTIFICATION_DURATION, options = {}) {
        const id = Date.now() + Math.random();
        const notification = this.createNotification(message, type, options);
        
        this.container.appendChild(notification);
        this.notifications.set(id, notification);

        // Trigger entrance animation
        requestAnimationFrame(() => {
            notification.classList.add('animate-slideInRight');
        });

        // Auto remove
        if (duration > 0) {
            setTimeout(() => this.remove(id), duration);
        }

        return { id, remove: () => this.remove(id) };
    }

    createNotification(message, type, options) {
        const notification = document.createElement('div');
        notification.className = `notification ${type} pointer-events-auto transform translate-x-full transition-all duration-300`;
        
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <span class="text-lg">${icons[type] || icons.info}</span>
                    <span class="font-medium">${message}</span>
                </div>
                <button onclick="this.closest('.notification').remove()" 
                        class="ml-4 text-white hover:text-gray-200 transition-colors focus:outline-none">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                    </svg>
                </button>
            </div>
        `;

        // Make notification interactive
        notification.addEventListener('mouseenter', () => {
            notification.style.animationPlayState = 'paused';
        });

        notification.addEventListener('mouseleave', () => {
            notification.style.animationPlayState = 'running';
        });

        return notification;
    }

    remove(id) {
        const notification = this.notifications.get(id);
        if (notification && notification.parentElement) {
            notification.classList.add('animate-slideInRight');
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
                this.notifications.delete(id);
            }, 300);
        }
    }

    success(message, duration, options) {
        return this.show(message, 'success', duration, options);
    }

    error(message, duration, options) {
        return this.show(message, 'error', duration, options);
    }

    warning(message, duration, options) {
        return this.show(message, 'warning', duration, options);
    }

    info(message, duration, options) {
        return this.show(message, 'info', duration, options);
    }

    clear() {
        this.notifications.forEach((_, id) => this.remove(id));
    }
}

// Enhanced Form Utilities
class FormUtils {
    static serializeForm(form) {
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            if (data[key]) {
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }
        
        return data;
    }

    static validateForm(form, customRules = {}) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        const errors = [];

        requiredFields.forEach(field => {
            const value = field.value.trim();
            const fieldName = field.name || field.id || 'Field';

            if (!value) {
                this.setFieldError(field, `${fieldName} is required`);
                errors.push(`${fieldName} is required`);
                isValid = false;
            } else {
                this.clearFieldError(field);
                
                // Apply custom validation rules
                if (customRules[field.name]) {
                    const rule = customRules[field.name];
                    if (typeof rule === 'function' && !rule(value)) {
                        this.setFieldError(field, rule.message || `Invalid ${fieldName}`);
                        errors.push(rule.message || `Invalid ${fieldName}`);
                        isValid = false;
                    }
                }
            }
        });

        // Email validation
        form.querySelectorAll('input[type="email"]').forEach(field => {
            if (field.value && !this.isValidEmail(field.value)) {
                this.setFieldError(field, 'Please enter a valid email address');
                errors.push('Please enter a valid email address');
                isValid = false;
            }
        });

        return { isValid, errors };
    }

    static setFieldError(field, message) {
        field.classList.add('border-red-500', 'border-2');
        field.classList.remove('border-gray-300', 'border-green-500');
        
        // Remove existing error message
        const existingError = field.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }

        // Add error message
        const errorElement = document.createElement('div');
        errorElement.className = 'field-error text-red-500 text-sm mt-1 animate-fadeIn';
        errorElement.textContent = message;
        field.parentNode.appendChild(errorElement);
    }

    static clearFieldError(field) {
        field.classList.remove('border-red-500', 'border-2');
        field.classList.add('border-gray-300');
        
        const errorElement = field.parentNode.querySelector('.field-error');
        if (errorElement) {
            errorElement.remove();
        }
    }

    static isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    static addLoadingState(button, text = 'Loading...') {
        const originalText = button.innerHTML;
        const originalDisabled = button.disabled;
        
        button.innerHTML = `
            <div class="flex items-center space-x-2">
                <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>${text}</span>
            </div>
        `;
        button.disabled = true;
        button.classList.add('loading');
        
        return () => {
            button.innerHTML = originalText;
            button.disabled = originalDisabled;
            button.classList.remove('loading');
        };
    }
}

// Enhanced AJAX Utilities
class AjaxUtils {
    static async request(url, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin',
        };
        
        const config = { ...defaultOptions, ...options };
        
        // Add loading indicator for requests that take longer than 500ms
        const loadingTimeout = setTimeout(() => {
            document.body.classList.add('loading');
        }, 500);

        try {
            const response = await fetch(url, config);
            clearTimeout(loadingTimeout);
            document.body.classList.remove('loading');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
        } catch (error) {
            clearTimeout(loadingTimeout);
            document.body.classList.remove('loading');
            console.error('AJAX request failed:', error);
            throw error;
        }
    }

    static getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    static async get(url, params = {}) {
        const urlParams = new URLSearchParams(params);
        const fullUrl = urlParams.toString() ? `${url}?${urlParams}` : url;
        return this.request(fullUrl);
    }

    static async post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    static async put(url, data = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    static async delete(url) {
        return this.request(url, {
            method: 'DELETE',
        });
    }

    static async uploadFile(url, file, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('csrfmiddlewaretoken', this.getCSRFToken());

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && onProgress) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    onProgress(percentComplete);
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (e) {
                        resolve(xhr.responseText);
                    }
                } else {
                    reject(new Error(`Upload failed with status ${xhr.status}`));
                }
            });

            xhr.addEventListener('error', () => {
                reject(new Error('Upload failed'));
            });

            xhr.open('POST', url);
            xhr.send(formData);
        });
    }
}

// Enhanced Animation Utilities
class AnimationUtils {
    static fadeIn(element, duration = CONFIG.ANIMATION_DURATION) {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        const start = performance.now();
        
        function animate(currentTime) {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.opacity = progress;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    }

    static fadeOut(element, duration = CONFIG.ANIMATION_DURATION) {
        const start = performance.now();
        const startOpacity = parseFloat(getComputedStyle(element).opacity);
        
        function animate(currentTime) {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.opacity = startOpacity * (1 - progress);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.style.display = 'none';
            }
        }
        
        requestAnimationFrame(animate);
    }

    static slideDown(element, duration = CONFIG.ANIMATION_DURATION) {
        element.style.height = '0';
        element.style.overflow = 'hidden';
        element.style.display = 'block';
        
        const targetHeight = element.scrollHeight;
        const start = performance.now();
        
        function animate(currentTime) {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.height = `${targetHeight * progress}px`;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.style.height = 'auto';
                element.style.overflow = 'visible';
            }
        }
        
        requestAnimationFrame(animate);
    }

    static slideUp(element, duration = CONFIG.ANIMATION_DURATION) {
        const startHeight = element.scrollHeight;
        const start = performance.now();
        
        element.style.height = `${startHeight}px`;
        element.style.overflow = 'hidden';
        
        function animate(currentTime) {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.height = `${startHeight * (1 - progress)}px`;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.style.display = 'none';
                element.style.height = 'auto';
                element.style.overflow = 'visible';
            }
        }
        
        requestAnimationFrame(animate);
    }

    static typeWriter(element, text, speed = 50) {
        let i = 0;
        element.textContent = '';
        
        function typeChar() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(typeChar, speed);
            }
        }
        
        typeChar();
    }

    static countUp(element, target, duration = 1000) {
        const start = performance.now();
        const startValue = 0;
        
        function animate(currentTime) {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            const currentValue = Math.floor(startValue + (target - startValue) * progress);
            element.textContent = currentValue.toLocaleString();
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    }
}

// Enhanced Video Feature Manager
class VideoManager {
    constructor() {
        this.currentVideoData = null;
        this.isGenerating = false;
    }

    async generateVideo(chatData, options = {}) {
        if (this.isGenerating) {
            throw new Error('Video generation already in progress');
        }

        this.isGenerating = true;
        
        try {
            const response = await AjaxUtils.post(CONFIG.API_ENDPOINTS.VIDEO_GENERATE, {
                chatData,
                options
            });

            if (response.success) {
                this.currentVideoData = response.videoData;
                return response;
            } else {
                throw new Error(response.error || 'Video generation failed');
            }
        } finally {
            this.isGenerating = false;
        }
    }

    createVideoElement(videoData) {
        const videoContainer = document.createElement('div');
        videoContainer.className = 'video-container';
        
        videoContainer.innerHTML = `
            <div class="video-overlay">
                <button class="video-play-button" onclick="this.parentElement.style.display='none'">
                    <svg class="video-play-icon" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"/>
                    </svg>
                </button>
            </div>
            <video controls class="w-full h-full object-cover">
                <source src="${videoData.url}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            <div class="absolute top-2 right-2 px-2 py-1 bg-black/50 text-white text-xs rounded">
                ${this.formatDuration(videoData.duration)}
            </div>
        `;

        return videoContainer;
    }

    formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    extractChatSummary(messageId) {
        const messageElements = document.querySelectorAll('.message-container');
        const messages = [];
        
        for (let element of messageElements) {
            const id = element.getAttribute('data-message-id');
            const content = element.querySelector('.message-content')?.textContent || '';
            const isBot = !element.querySelector('.gradient-bg');
            
            messages.push({
                id: id,
                content: content.trim(),
                isBot: isBot,
                timestamp: new Date().toISOString()
            });
            
            if (id == messageId) break;
        }
        
        return messages;
    }

    async downloadVideo(videoData) {
        try {
            const response = await fetch(videoData.url);
            const blob = await response.blob();
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `binarygirls-video-${Date.now()}.mp4`;
            
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Download failed:', error);
            throw error;
        }
    }
}

// Enhanced Utility Functions
function debounce(func, delay = CONFIG.DEBOUNCE_DELAY) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

function throttle(func, limit = CONFIG.THROTTLE_LIMIT) {
    let inThrottle;
    return function (...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function formatDate(date, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    };
    
    const formatOptions = { ...defaultOptions, ...options };
    return new Intl.DateTimeFormat('tr-TR', formatOptions).format(date);
}

function formatNumber(number, options = {}) {
    const defaultOptions = {
        style: 'decimal',
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
    };
    
    const formatOptions = { ...defaultOptions, ...options };
    return new Intl.NumberFormat('tr-TR', formatOptions).format(number);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        return new Promise((resolve, reject) => {
            if (document.execCommand('copy')) {
                resolve();
            } else {
                reject(new Error('Copy failed'));
            }
            document.body.removeChild(textArea);
        });
    }
}

// Enhanced Performance Monitor
class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.observers = {};
        this.initObservers();
    }

    initObservers() {
        // Intersection Observer for lazy loading
        this.observers.intersection = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    
                    // Lazy load images
                    if (element.hasAttribute('data-src')) {
                        element.src = element.getAttribute('data-src');
                        element.removeAttribute('data-src');
                        this.observers.intersection.unobserve(element);
                    }
                    
                    // Trigger animations
                    if (element.hasAttribute('data-animate')) {
                        element.classList.add(element.getAttribute('data-animate'));
                        element.removeAttribute('data-animate');
                        this.observers.intersection.unobserve(element);
                    }
                }
            });
        }, { threshold: 0.1 });

        // Resize Observer for responsive components
        this.observers.resize = new ResizeObserver((entries) => {
            entries.forEach(entry => {
                const element = entry.target;
                const { width, height } = entry.contentRect;
                
                // Dispatch custom resize event
                element.dispatchEvent(new CustomEvent('elementResize', {
                    detail: { width, height }
                }));
            });
        });
    }

    startTiming(name) {
        this.metrics[name] = { start: performance.now() };
    }

    endTiming(name) {
        if (this.metrics[name]) {
            this.metrics[name].end = performance.now();
            this.metrics[name].duration = this.metrics[name].end - this.metrics[name].start;
        }
    }

    getMetric(name) {
        return this.metrics[name];
    }

    getAllMetrics() {
        return this.metrics;
    }

    observeElement(element, type = 'intersection') {
        if (this.observers[type]) {
            this.observers[type].observe(element);
        }
    }

    unobserveElement(element, type = 'intersection') {
        if (this.observers[type]) {
            this.observers[type].unobserve(element);
        }
    }
}

// Global instances
const darkModeManager = new DarkModeManager();
const notifications = new NotificationManager();
const videoManager = new VideoManager();
const performanceMonitor = new PerformanceMonitor();

// Enhanced initialization function
function initializeApp() {
    performanceMonitor.startTiming('appInit');
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize lazy loading
    initializeLazyLoading();
    
    // Initialize form enhancements
    initializeFormEnhancements();
    
    // Initialize keyboard navigation
    initializeKeyboardNavigation();
    
    // Initialize accessibility features
    initializeAccessibility();
    
    // Initialize error handling
    initializeErrorHandling();
    
    // Initialize PWA features if available
    initializePWA();
    
    performanceMonitor.endTiming('appInit');
    console.log('App initialized in', performanceMonitor.getMetric('appInit').duration.toFixed(2), 'ms');
}

function initializeTooltips() {
    const tooltip = document.createElement('div');
    tooltip.id = 'global-tooltip';
    tooltip.className = 'tooltip';
    document.body.appendChild(tooltip);

    document.addEventListener('mouseover', (e) => {
        const element = e.target.closest('[title], [data-tooltip]');
        if (element) {
            const text = element.getAttribute('data-tooltip') || element.getAttribute('title');
            if (text) {
                showTooltip(element, text);
                if (element.hasAttribute('title')) {
                    element.setAttribute('data-original-title', element.getAttribute('title'));
                    element.removeAttribute('title');
                }
            }
        }
    });

    document.addEventListener('mouseout', (e) => {
        const element = e.target.closest('[data-tooltip], [data-original-title]');
        if (element) {
            hideTooltip();
            if (element.hasAttribute('data-original-title')) {
                element.setAttribute('title', element.getAttribute('data-original-title'));
                element.removeAttribute('data-original-title');
            }
        }
    });
}

function showTooltip(element, text) {
    const tooltip = document.getElementById('global-tooltip');
    if (!tooltip) return;

    tooltip.textContent = text;
    tooltip.classList.add('show');

    const rect = element.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();

    let top = rect.top - tooltipRect.height - 10;
    let left = rect.left + (rect.width - tooltipRect.width) / 2;

    // Adjust position if tooltip goes off-screen
    if (top < 10) {
        top = rect.bottom + 10;
    }
    if (left < 10) {
        left = 10;
    }
    if (left + tooltipRect.width > window.innerWidth - 10) {
        left = window.innerWidth - tooltipRect.width - 10;
    }

    tooltip.style.top = `${top}px`;
    tooltip.style.left = `${left}px`;
}

function hideTooltip() {
    const tooltip = document.getElementById('global-tooltip');
    if (tooltip) {
        tooltip.classList.remove('show');
    }
}

function initializeLazyLoading() {
    // Lazy load images
    document.querySelectorAll('img[data-src]').forEach(img => {
        performanceMonitor.observeElement(img);
    });

    // Lazy load components
    document.querySelectorAll('[data-animate]').forEach(element => {
        performanceMonitor.observeElement(element);
    });
}

function initializeFormEnhancements() {
    // Enhanced form validation
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function (e) {
            const validation = FormUtils.validateForm(this);
            if (!validation.isValid) {
                e.preventDefault();
                notifications.error('Please fix the errors in the form');
            }
        });

        // Real-time validation
        form.querySelectorAll('input, textarea, select').forEach(field => {
            field.addEventListener('blur', () => {
                FormUtils.validateForm(form);
            });
        });
    });

    // Auto-save functionality
    document.querySelectorAll('[data-autosave]').forEach(field => {
        const debouncedSave = debounce(() => {
            const key = `autosave_${field.name || field.id}`;
            localStorage.setItem(key, field.value);
        }, 1000);

        field.addEventListener('input', debouncedSave);

        // Restore saved value
        const key = `autosave_${field.name || field.id}`;
        const savedValue = localStorage.getItem(key);
        if (savedValue && !field.value) {
            field.value = savedValue;
        }
    });
}

function initializeKeyboardNavigation() {
    let isKeyboardNavigation = false;

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            isKeyboardNavigation = true;
            document.body.classList.add('keyboard-navigation');
        }

        // Enhanced keyboard shortcuts
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case 'k':
                    e.preventDefault();
                    // Focus search input
                    const searchInput = document.querySelector('input[type="search"], input[placeholder*="search"], input[placeholder*="ara"]');
                    if (searchInput) {
                        searchInput.focus();
                    }
                    break;
                case '/':
                    e.preventDefault();
                    // Toggle dark mode
                    darkModeManager.toggle();
                    break;
            }
        }

        // Escape key to close modals
        if (e.key === 'Escape') {
            const modal = document.querySelector('.modal:not(.hidden), .video-modal:not(.hidden)');
            if (modal) {
                const closeBtn = modal.querySelector('[onclick*="close"], .close-modal');
                if (closeBtn) {
                    closeBtn.click();
                }
            }
        }
    });

    document.addEventListener('mousedown', () => {
        if (isKeyboardNavigation) {
            isKeyboardNavigation = false;
            document.body.classList.remove('keyboard-navigation');
        }
    });
}

function initializeAccessibility() {
    // Add ARIA labels to interactive elements
    document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])').forEach(button => {
        if (!button.textContent.trim()) {
            const icon = button.querySelector('svg');
            if (icon) {
                button.setAttribute('aria-label', 'Button');
            }
        }
    });

    // Improve focus management
    document.addEventListener('focusin', (e) => {
        const element = e.target;
        if (element.closest('.modal, .dropdown, .tooltip')) {
            // Keep focus within modal/dropdown
        }
    });

    // Add skip links
    if (!document.querySelector('.skip-links')) {
        const skipLinks = document.createElement('div');
        skipLinks.className = 'skip-links sr-only focus:not-sr-only';
        skipLinks.innerHTML = `
            <a href="#main-content" class="bg-blue-600 text-white p-2 rounded">Skip to main content</a>
        `;
        document.body.insertBefore(skipLinks, document.body.firstChild);
    }
}

function initializeErrorHandling() {
    // Global error handler
    window.addEventListener('error', (e) => {
        console.error('Global error:', e.error);
        
        // Don't show notifications for script errors in development
        if (process?.env?.NODE_ENV !== 'development') {
            notifications.error('An unexpected error occurred. Please refresh the page.');
        }
    });

    // Promise rejection handler
    window.addEventListener('unhandledrejection', (e) => {
        console.error('Unhandled promise rejection:', e.reason);
        
        if (process?.env?.NODE_ENV !== 'development') {
            notifications.error('A network error occurred. Please check your connection.');
        }
    });

    // AJAX error interceptor
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        try {
            const response = await originalFetch.apply(this, args);
            if (!response.ok && response.status >= 500) {
                notifications.error('Server error occurred. Please try again later.');
            }
            return response;
        } catch (error) {
            notifications.error('Network error. Please check your connection.');
            throw error;
        }
    };
}

function initializePWA() {
    // Service worker registration
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .catch(error => console.log('SW registration failed:', error));
    }

    // Install prompt
    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        
        // Show install button
        const installBtn = document.querySelector('.install-app-btn');
        if (installBtn) {
            installBtn.style.display = 'block';
            installBtn.addEventListener('click', async () => {
                if (deferredPrompt) {
                    deferredPrompt.prompt();
                    const { outcome } = await deferredPrompt.userChoice;
                    deferredPrompt = null;
                    installBtn.style.display = 'none';
                }
            });
        }
    });
}

// Global functions for backward compatibility
function toggleDarkMode() {
    return darkModeManager.toggle();
}

function showNotification(message, type, duration) {
    return notifications.show(message, type, duration);
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', initializeApp);

// Export for global use
window.BinaryGirls = {
    notifications,
    videoManager,
    FormUtils,
    AjaxUtils,
    AnimationUtils,
    darkModeManager,
    performanceMonitor,
    toggleDarkMode,
    showNotification,
    debounce,
    throttle,
    formatDate,
    formatNumber,
    formatFileSize,
    generateId,
    copyToClipboard,
    CONFIG
};

// Performance monitoring
window.addEventListener('load', () => {
    performanceMonitor.startTiming('pageLoad');
    
    // Log performance metrics
    setTimeout(() => {
        const navigation = performance.getEntriesByType('navigation')[0];
        console.log('Page load performance:', {
            DNS: navigation.domainLookupEnd - navigation.domainLookupStart,
            TCP: navigation.connectEnd - navigation.connectStart,
            Request: navigation.responseStart - navigation.requestStart,
            Response: navigation.responseEnd - navigation.responseStart,
            DOM: navigation.domContentLoadedEventEnd - navigation.navigationStart,
            Load: navigation.loadEventEnd - navigation.navigationStart
        });
        
        performanceMonitor.endTiming('pageLoad');
    }, 0);
});

console.log('🚀 BinaryGirls Enhanced JavaScript loaded successfully!');