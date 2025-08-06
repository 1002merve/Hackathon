/* Enhanced Guest Avatar System - static/js/avatar-system.js */

class GuestAvatarSystem {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.avatarAssistant = null;
        this.resizeHandle = null;
        
        // --- DEĞİŞİKLİK BAŞLANGICI: Sessize alma butonu ve durumu eklendi ---
        this.muteButton = null;
        this.isMuted = false;
        // --- DEĞİŞİKLİK SONU ---
        
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.avatar = null;
        this.mixer = null;
        this.animations = {};
        this.currentAnimation = null;
        this.isLoaded = false;
        
        // Configuration
        this.config = {
            initialSize: options.size || 120,
            position: options.position || { bottom: '20px', right: '20px' },
            autoStart: options.autoStart !== false,
            messages: options.messages || {},
            showTooltip: options.showTooltip !== false,
            ...options
        };
        
        // Avatar expressions for emotions
        this.facialExpressions = {
            default: {},
            smile: { browInnerUp: 0.17, eyeSquintLeft: 0.4, eyeSquintRight: 0.44, mouthSmileLeft: 0.8, mouthSmileRight: 0.8 },
            happy: { browInnerUp: 0.17, eyeSquintLeft: 0.4, eyeSquintRight: 0.44, mouthSmileLeft: 1.0, mouthSmileRight: 1.0 },
            surprised: { eyeWideLeft: 0.5, eyeWideRight: 0.5, jawOpen: 0.35, mouthFunnel: 1, browInnerUp: 1 },
            thinking: { browDownLeft: 0.3, browDownRight: 0.3, eyeLookUpLeft: 0.3, eyeLookUpRight: 0.3 },
            sad: { mouthFrownLeft: 1, mouthFrownRight: 1, mouthShrugLower: 0.78, browInnerUp: 0.45, eyeSquintLeft: 0.72, eyeSquintRight: 0.75 },
            excited: { browInnerUp: 0.5, eyeWideLeft: 0.3, eyeWideRight: 0.3, mouthSmileLeft: 0.9, mouthSmileRight: 0.9 }
        };
        
        this.talkingInterval = null;
        this.isDragging = false;
        this.isResizing = false;
        this.dragStartX = 0;
        this.dragStartY = 0;
        this.avatarStartX = 0;
        this.avatarStartY = 0;
        this.resizeStartX = 0;
        this.resizeStartY = 0;
        this.initialSize = 0;
        this.minSize = 80;
        this.maxSize = 300;
        
        this.init();
    }

    init() {
        this.createAvatarContainer();
        this.createScene();
        this.createCamera();
        this.createRenderer();
        this.addLights();
        this.loadAvatar().then(() => {
            this.animate();
            this.setupInteractions();
            this.restoreSettings();
            
            // --- DEĞİŞİKLİK BAŞLANGICI: Sessize alma durumunu yükle ---
            this.loadMuteState();
            // --- DEĞİŞİKLİK SONU ---

            if (this.config.autoStart) {
                this.startWelcomeSequence();
            }
        });
    }

    createAvatarContainer() {
        this.avatarAssistant = document.createElement('div');
        this.avatarAssistant.className = 'guest-avatar-assistant';
        this.avatarAssistant.style.cssText = `
            position: fixed;
            ${this.config.position.bottom ? `bottom: ${this.config.position.bottom};` : ''}
            ${this.config.position.top ? `top: ${this.config.position.top};` : ''}
            ${this.config.position.right ? `right: ${this.config.position.right};` : ''}
            ${this.config.position.left ? `left: ${this.config.position.left};` : ''}
            width: ${this.config.initialSize}px;
            height: ${this.config.initialSize}px;
            border-radius: 50%;
            z-index: 1000;
            cursor: grab;
            transition: opacity 0.3s, transform 0.3s;
            transform: translateY(100px);
            opacity: 0;
            user-select: none;
            background: transparent;
        `;

        const pulseEffect = document.createElement('div');
        pulseEffect.className = 'avatar-floating-pulse';
        pulseEffect.style.cssText = `
            position: absolute;
            inset: -10px;
            border-radius: 50%;
            background: linear-gradient(135deg, rgba(236, 72, 153, 0.3), rgba(244, 63, 94, 0.3));
            animation: avatarPulse 3s ease-in-out infinite;
            z-index: -1;
        `;

        if (this.config.showTooltip) {
            const tooltip = document.createElement('div');
            tooltip.className = 'avatar-tooltip';
            tooltip.style.cssText = `
                position: absolute;
                bottom: 100%;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 8px 12px;
                border-radius: 8px;
                font-size: 12px;
                white-space: nowrap;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
                margin-bottom: 10px;
                backdrop-filter: blur(8px);
                z-index: 10;
            `;
            tooltip.textContent = this.config.messages.tooltip || 'AI Rehberiniz | Sürükleyebilirsiniz';
            
            tooltip.innerHTML += `
                <div style="
                    content: '';
                    position: absolute;
                    top: 100%;
                    left: 50%;
                    transform: translateX(-50%);
                    border: 5px solid transparent;
                    border-top-color: rgba(0, 0, 0, 0.8);
                "></div>
            `;
            this.avatarAssistant.appendChild(tooltip);
        }

        const avatarContainer = document.createElement('div');
        avatarContainer.id = this.containerId + 'Container';
        avatarContainer.style.cssText = `
            width: 100%;
            height: 100%;
            position: relative;
            overflow: hidden;
            border-radius: 50%;
            background: transparent;
        `;

        const loadingElement = document.createElement('div');
        loadingElement.className = 'avatar-loading-global';
        loadingElement.style.cssText = `
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #ec4899, #f43f5e);
            border-radius: 50%;
            transition: opacity 0.3s ease;
        `;
        loadingElement.innerHTML = `
            <div style="width: 20px; height: 20px; border: 2px solid rgba(255, 255, 255, 0.3); border-top: 2px solid #ffffff; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        `;

        this.resizeHandle = document.createElement('div');
        this.resizeHandle.className = 'avatar-resize-handle';
        this.resizeHandle.style.cssText = `
            position: absolute;
            bottom: -2px;
            right: -2px;
            width: 24px;
            height: 24px;
            background: rgba(255, 255, 255, 0.8);
            border: 2px solid #ec4899;
            border-radius: 50%;
            cursor: se-resize;
            z-index: 10;
            backdrop-filter: blur(4px);
            transition: transform 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        this.resizeHandle.innerHTML = `<svg width="8" height="8" viewBox="0 0 8 8" fill="none"><path d="M8 0L0 8M8 2L2 8M8 4L4 8M8 6L6 8" stroke="#ec4899" stroke-width="1"/></svg>`;

        // --- DEĞİŞİKLİK BAŞLANGICI: Sessize alma butonu oluşturuldu ---
        this.muteButton = document.createElement('div');
        this.muteButton.className = 'avatar-mute-button';
        this.muteButton.setAttribute('title', 'Sesi aç/kapat');
        this.muteButton.style.cssText = `
            position: absolute;
            top: -2px;
            left: -2px;
            width: 24px;
            height: 24px;
            background: rgba(255, 255, 255, 0.8);
            border: 2px solid #3b82f6;
            border-radius: 50%;
            cursor: pointer;
            z-index: 10;
            backdrop-filter: blur(4px);
            transition: transform 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        this.muteButton.innerHTML = `
            <svg class="sound-on-icon w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                <path d="M5 7a1 1 0 00-2 0v6a1 1 0 102 0V7zM10 4a1 1 0 00-2 0v12a1 1 0 102 0V4zM15 7a1 1 0 00-2 0v6a1 1 0 102 0V7z"/>
            </svg>
            <svg class="sound-off-icon w-4 h-4 text-red-600 hidden" fill="currentColor" viewBox="0 0 20 20">
                 <path fill-rule="evenodd" d="M9.383 3.076a1 1 0 011.09.217l3.707 3.707H16a1 1 0 011 1v4a1 1 0 01-1 1h-1.81l3.707 3.707a1 1 0 01-1.414 1.414L3.293 4.293A1 1 0 014.707 2.88L9.383 3.076zm1.414 9.193L12 11.08V8h1.81l2.5 2.5L13.793 13l-1.586-1.586a.5.5 0 00-.707 0zM10 5.172L7.707 7.464 10 9.757V5.172zM5.293 8H3a1 1 0 00-1 1v4a1 1 0 001 1h2.293l-2-2a.5.5 0 010-.707l2-2z" clip-rule="evenodd"/>
            </svg>
        `;
        // --- DEĞİŞİKLİK SONU ---

        avatarContainer.appendChild(loadingElement);
        this.avatarAssistant.appendChild(pulseEffect);
        this.avatarAssistant.appendChild(avatarContainer);
        this.avatarAssistant.appendChild(this.resizeHandle);
        this.avatarAssistant.appendChild(this.muteButton);

        document.body.appendChild(this.avatarAssistant);
        this.container = avatarContainer;
    }

    createScene() { this.scene = new THREE.Scene(); this.scene.background = null; }
    createCamera() { this.camera = new THREE.PerspectiveCamera(30, 1, 0.1, 1000); this.camera.position.set(0, 1.6, 1.8); this.camera.lookAt(0, 1.5, 0); }
    createRenderer() { this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true }); this.renderer.setSize(this.config.initialSize, this.config.initialSize); this.renderer.shadowMap.enabled = true; this.renderer.shadowMap.type = THREE.PCFSoftShadowMap; this.renderer.toneMapping = THREE.ACESFilmicToneMapping; this.renderer.toneMappingExposure = 1.2; this.container.appendChild(this.renderer.domElement); }
    addLights() { const a = new THREE.AmbientLight(0xffffff, 0.6); this.scene.add(a); const d = new THREE.DirectionalLight(0xffffff, 0.8); d.position.set(2, 4, 2); d.castShadow = true; this.scene.add(d); const f = new THREE.DirectionalLight(0xf3e8ff, 0.3); f.position.set(-2, 2, 1); this.scene.add(f); }

    async loadAvatar() { try { const dracoLoader = new THREE.DRACOLoader(); dracoLoader.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/libs/draco/'); const loader = new THREE.GLTFLoader(); loader.setDRACOLoader(dracoLoader); const modelPath = '/static/models/64f1a714fe61576b46f27ca2.glb'; const avatarGLTF = await new Promise((resolve, reject) => { loader.load(modelPath, resolve, undefined, reject); }); this.avatar = avatarGLTF.scene; this.avatar.position.set(0, 0, 0); this.avatar.scale.set(1, 1, 1); this.avatar.traverse((c) => { if (c.isMesh) { c.castShadow = true; c.receiveShadow = true; } }); this.scene.add(this.avatar); const animationsPath = '/static/models/animations/animations.glb'; const animationsGLTF = await new Promise((resolve, reject) => { loader.load(animationsPath, resolve, undefined, reject); }); this.mixer = new THREE.AnimationMixer(this.avatar); this.animations = {}; animationsGLTF.animations.forEach((clip) => { this.animations[clip.name] = this.mixer.clipAction(clip); }); this.playAnimation('Standing Idle'); this.setExpression('default'); this.isLoaded = true; this.onAvatarLoaded(); } catch (error) { console.error('Error loading guest avatar:', error); this.container.innerHTML = `<div style="width: 100%; height: 100%; background: linear-gradient(135deg, #ec4899, #f43f5e); border-radius: 50%; display: flex; align-items: center; justify-content: center;"><span style="color: white; font-size: 24px;">🤖</span></div>`; this.avatarAssistant.classList.add('loaded'); } }

    playAnimation(name) {
        const animationName = this.animations[name] ? name : 'Standing Idle';
        if (!this.animations[animationName]) return;
        if (this.currentAnimation) {
            this.currentAnimation.fadeOut(0.3);
        }
        this.currentAnimation = this.animations[animationName];
        this.currentAnimation.reset().fadeIn(0.3).play();
    }

    setExpression(expressionName) { if (!this.avatar || !this.facialExpressions[expressionName]) return; const expression = this.facialExpressions[expressionName]; this.avatar.traverse((child) => { if (child.isSkinnedMesh && child.morphTargetDictionary) { Object.keys(child.morphTargetDictionary).forEach((key) => { if (key !== 'eyeBlinkLeft' && key !== 'eyeBlinkRight') { const index = child.morphTargetDictionary[key]; if (index !== undefined) { child.morphTargetInfluences[index] = expression[key] || 0; } } }); } }); }

    speak(text, options = {}) {
        if (!this.isLoaded) return;
        if ('speechSynthesis' in window) {
            speechSynthesis.cancel();
        }
        
        const emotion = options.emotion || 'default';
        const animation = options.animation || 'Talking_0';
        
        this.setExpression(emotion);
        this.playAnimation(animation);

        // --- DEĞİŞİKLİK BAŞLANGICI: Sessize alınmışsa konuşma ---
        if (this.isMuted) {
            this.startTalking();
            setTimeout(() => {
                this.stopTalking();
                this.playAnimation('Standing Idle');
                this.setExpression('default');
                if (options.onComplete) options.onComplete();
            }, text.length * 120);
            return;
        }
        // --- DEĞİŞİKLİK SONU ---

        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'tr-TR';
            utterance.rate = options.rate || 1;
            utterance.pitch = options.pitch || 1.1;
            utterance.volume = options.volume || 1;
            
            utterance.onstart = () => { this.startTalking(); this.avatarAssistant.classList.add('speaking'); };
            utterance.onend = () => { this.stopTalking(); this.playAnimation('Standing Idle'); this.setExpression('default'); this.avatarAssistant.classList.remove('speaking'); if (options.onComplete) options.onComplete(); };
            
            speechSynthesis.speak(utterance);
        } else {
            this.startTalking();
            setTimeout(() => { this.stopTalking(); this.playAnimation('Standing Idle'); this.setExpression('default'); if (options.onComplete) options.onComplete(); }, text.length * 120);
        }
    }

    startTalking() { if (!this.avatar) return; this.stopTalking(); this.talkingInterval = setInterval(() => { const intensity = Math.random() * 0.4 + 0.1; if (this.avatar) { this.avatar.traverse((child) => { if (child.isSkinnedMesh && child.morphTargetDictionary) { const jawOpen = child.morphTargetDictionary['jawOpen']; const mouthFunnel = child.morphTargetDictionary['mouthFunnel']; if (jawOpen !== undefined) child.morphTargetInfluences[jawOpen] = intensity; if (mouthFunnel !== undefined) child.morphTargetInfluences[mouthFunnel] = intensity * 0.5; } }); } }, 120); }
    stopTalking() { if (this.talkingInterval) { clearInterval(this.talkingInterval); this.talkingInterval = null; } if (this.avatar) { this.avatar.traverse((child) => { if (child.isSkinnedMesh && child.morphTargetDictionary) { const jawOpen = child.morphTargetDictionary['jawOpen']; const mouthFunnel = child.morphTargetDictionary['mouthFunnel']; if (jawOpen !== undefined) child.morphTargetInfluences[jawOpen] = 0; if (mouthFunnel !== undefined) child.morphTargetInfluences[mouthFunnel] = 0; } }); } }

    setupInteractions() {
        this.avatarAssistant.addEventListener('mousedown', this.startDrag.bind(this));
        document.addEventListener('mousemove', this.drag.bind(this));
        document.addEventListener('mouseup', this.endDrag.bind(this));
        this.resizeHandle.addEventListener('mousedown', this.startResize.bind(this));
        
        // --- DEĞİŞİKLİK BAŞLANGICI: Sessize alma butonu için olay dinleyici ---
        this.muteButton.addEventListener('click', this.toggleMute.bind(this));
        // --- DEĞİŞİKLİK SONU ---
        
        this.avatarAssistant.addEventListener('mouseenter', () => { const tooltip = this.avatarAssistant.querySelector('.avatar-tooltip'); if (tooltip) { tooltip.style.opacity = '1'; tooltip.style.visibility = 'visible'; tooltip.style.transform = 'translateX(-50%) translateY(-5px)'; } });
        this.avatarAssistant.addEventListener('mouseleave', () => { const tooltip = this.avatarAssistant.querySelector('.avatar-tooltip'); if (tooltip) { tooltip.style.opacity = '0'; tooltip.style.visibility = 'hidden'; tooltip.style.transform = 'translateX(-50%) translateY(0)'; } });
    }

    startDrag(e) {
        // --- DEĞİŞİKLİK BAŞLANGICI: Butonlara basıldığında sürüklemeyi engelle ---
        if (e.target.closest('.avatar-resize-handle') || e.target.closest('.avatar-mute-button') || this.isResizing) return;
        // --- DEĞİŞİKLİK SONU ---
        this.isDragging = true; this.avatarAssistant.style.cursor = 'grabbing'; this.avatarAssistant.style.transform = 'scale(1.1)'; this.dragStartX = e.clientX; this.dragStartY = e.clientY; const rect = this.avatarAssistant.getBoundingClientRect(); this.avatarStartX = rect.left; this.avatarStartY = rect.top;
    }

    drag(e) { if (this.isDragging) { e.preventDefault(); const deltaX = e.clientX - this.dragStartX; const deltaY = e.clientY - this.dragStartY; let newX = this.avatarStartX + deltaX; let newY = this.avatarStartY + deltaY; const rect = this.avatarAssistant.getBoundingClientRect(); newX = Math.max(0, Math.min(newX, window.innerWidth - rect.width)); newY = Math.max(0, Math.min(newY, window.innerHeight - rect.height)); this.avatarAssistant.style.left = `${newX}px`; this.avatarAssistant.style.top = `${newY}px`; this.avatarAssistant.style.right = 'auto'; this.avatarAssistant.style.bottom = 'auto'; } else if (this.isResizing) { e.preventDefault(); const deltaX = e.clientX - this.resizeStartX; const deltaY = e.clientY - this.resizeStartY; const newSize = this.initialSize + Math.max(deltaX, deltaY); this.applySize(newSize); } }
    endDrag(e) { if (this.isDragging) { this.isDragging = false; this.avatarAssistant.style.cursor = 'grab'; this.avatarAssistant.style.transform = 'scale(1)'; const rect = this.avatarAssistant.getBoundingClientRect(); localStorage.setItem(`${this.containerId}Position`, JSON.stringify({ x: rect.left, y: rect.top })); } if (this.isResizing) { this.isResizing = false; const rect = this.avatarAssistant.getBoundingClientRect(); localStorage.setItem(`${this.containerId}Size`, rect.width); } }
    startResize(e) { e.preventDefault(); e.stopPropagation(); this.isResizing = true; this.resizeStartX = e.clientX; this.resizeStartY = e.clientY; this.initialSize = this.avatarAssistant.offsetWidth; }
    applySize(size) { const newSize = Math.max(this.minSize, Math.min(size, this.maxSize)); this.avatarAssistant.style.width = `${newSize}px`; this.avatarAssistant.style.height = `${newSize}px`; if (this.renderer) this.renderer.setSize(newSize, newSize); if (this.camera) { this.camera.aspect = 1; this.camera.updateProjectionMatrix(); } }
    restoreSettings() { const savedSize = localStorage.getItem(`${this.containerId}Size`); if (savedSize) { this.applySize(parseFloat(savedSize)); } const savedPosition = localStorage.getItem(`${this.containerId}Position`); if (savedPosition) { try { const { x, y } = JSON.parse(savedPosition); this.avatarAssistant.style.left = `${x}px`; this.avatarAssistant.style.top = `${y}px`; this.avatarAssistant.style.right = 'auto'; this.avatarAssistant.style.bottom = 'auto'; } catch (e) { console.error("Avatar position could not be restored."); } } }

    // --- DEĞİŞİKLİK BAŞLANGICI: Sessize alma için yeni metodlar ---
    loadMuteState() {
        const savedMuteState = localStorage.getItem(`${this.containerId}Muted`);
        this.setMute(savedMuteState === 'true', false);
    }
    
    toggleMute(e) {
        e.stopPropagation();
        this.setMute(!this.isMuted);
    }

    setMute(isMuted, save = true) {
        this.isMuted = isMuted;
        const tooltip = this.avatarAssistant.querySelector('.avatar-tooltip');

        if (this.isMuted) {
            if ('speechSynthesis' in window) {
                speechSynthesis.cancel();
            }
            this.muteButton.querySelector('.sound-on-icon').classList.add('hidden');
            this.muteButton.querySelector('.sound-off-icon').classList.remove('hidden');
            if(tooltip) tooltip.textContent = 'Ses kapalı. Açmak için tıklayın.';
        } else {
            this.muteButton.querySelector('.sound-on-icon').classList.remove('hidden');
            this.muteButton.querySelector('.sound-off-icon').classList.add('hidden');
            if(tooltip) tooltip.textContent = this.config.messages.tooltip || 'AI Rehberiniz | Sürükleyebilirsiniz';
        }
        
        if (save) {
            localStorage.setItem(`${this.containerId}Muted`, this.isMuted);
        }
    }
    // --- DEĞİŞİKLİK SONU ---
    
    onAvatarLoaded() { const loadingElement = this.container.querySelector('.avatar-loading-global'); if (loadingElement) { loadingElement.style.opacity = '0'; setTimeout(() => loadingElement.remove(), 300); } this.avatarAssistant.style.transform = 'translateY(0)'; this.avatarAssistant.style.opacity = '1'; }
    animate() { requestAnimationFrame(() => this.animate()); if (this.mixer) { this.mixer.update(0.016); } if (this.avatar && this.isLoaded) { this.avatar.position.y = Math.sin(Date.now() * 0.001) * 0.02; } if (this.renderer && this.scene && this.camera) { this.renderer.render(this.scene, this.camera); } }
    startWelcomeSequence() { if (!this.isLoaded) { setTimeout(() => this.startWelcomeSequence(), 1000); return; } setTimeout(() => { const welcomeMessage = this.config.messages.welcome || "Merhaba! Ben BinaryGirls AI asistanınızım. Size yardımcı olmak için buradayım!"; this.speak(welcomeMessage, { emotion: 'happy', animation: 'Talking_1' }); }, 1500); }
    showMessage(text, emotion = 'smile', animation = 'Talking_0') { this.speak(text, { emotion, animation }); }
    celebrateSuccess() { this.setExpression('excited'); this.playAnimation('Rumba Dancing'); this.speak("Harika! Tebrikler! 🎉", { emotion: 'excited' }); setTimeout(() => { this.playAnimation('Standing Idle'); this.setExpression('default'); }, 3000); }
    showThinking() { this.setExpression('thinking'); this.playAnimation('Standing Idle'); }
    destroy() { if (this.avatarAssistant) { this.avatarAssistant.remove(); } if (this.talkingInterval) { clearInterval(this.talkingInterval); } if ('speechSynthesis' in window) { speechSynthesis.cancel(); } }
}

// Add required CSS animations
const style = document.createElement('style');
style.textContent = `@keyframes avatarPulse { 0%, 100% { transform: scale(1); opacity: 0.7; } 50% { transform: scale(1.2); opacity: 0.3; } } @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } } .guest-avatar-assistant.speaking { animation: avatarGlow 2s ease-in-out infinite; } @keyframes avatarGlow { 0%, 100% { box-shadow: 0 10px 30px rgba(236, 72, 153, 0.2); } 50% { box-shadow: 0 20px 50px rgba(236, 72, 153, 0.4); } } .avatar-resize-handle:hover, .avatar-mute-button:hover { transform: scale(1.2); } @media (max-width: 768px) { .guest-avatar-assistant { width: 80px !important; height: 80px !important; } }`;
document.head.appendChild(style);