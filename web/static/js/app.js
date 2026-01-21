/**
 * DuilioCode Studio - Frontend Application v2.0
 * 
 * MAJOR UPDATE: Smart prompt detection, better user feedback, improved UX
 */

const API_BASE = '';

// === State ===
let currentTab = 'chat';
let uploadedImage = null;

// === Elements ===
const elements = {
    loading: document.getElementById('loading'),
    loadingText: document.getElementById('loading-text'),
    modelSelect: document.getElementById('model-select'),
    status: document.getElementById('status'),
    
    // Chat
    chatMessages: document.getElementById('chat-messages'),
    chatInput: document.getElementById('chat-input'),
    chatSend: document.getElementById('chat-send'),
    
    // Generate
    genPrompt: document.getElementById('gen-prompt'),
    genNegative: document.getElementById('gen-negative'),
    genWidth: document.getElementById('gen-width'),
    genHeight: document.getElementById('gen-height'),
    genSteps: document.getElementById('gen-steps'),
    genGuidance: document.getElementById('gen-guidance'),
    genSeed: document.getElementById('gen-seed'),
    genPreview: document.getElementById('gen-preview'),
    generateBtn: document.getElementById('generate-btn'),
    
    // Edit
    editFile: document.getElementById('edit-file'),
    uploadArea: document.getElementById('upload-area'),
    editPrompt: document.getElementById('edit-prompt'),
    editStrength: document.getElementById('edit-strength'),
    editOriginal: document.getElementById('edit-original'),
    editResult: document.getElementById('edit-result'),
    editBtn: document.getElementById('edit-btn'),
    editAlert: document.getElementById('edit-alert'),
    editAlertText: document.getElementById('edit-alert-text'),
    editSuggestions: document.getElementById('edit-suggestions'),
    editSuggestionsList: document.getElementById('edit-suggestions-list'),
    
    // Code
    codeLang: document.getElementById('code-lang'),
    codePrompt: document.getElementById('code-prompt'),
    codeOutput: document.getElementById('code-output'),
    codeBtn: document.getElementById('code-btn'),
    copyCode: document.getElementById('copy-code'),
};

// === Timer State ===
let loadingTimer = null;
let loadingStartTime = null;

// === Abort Controller for cancellation ===
let currentAbortController = null;

// === Prompt Analysis Patterns ===
const REMOVAL_PATTERNS = [
    /\bremov[ea]\b/i, /\bapag[ae]\b/i, /\bexclu[ií]\b/i, /\btir[ae]\b/i,
    /\bdelete\b/i, /\berase\b/i, /\bremove\b/i, /\btake out\b/i,
    /\belimin[ae]\b/i, /\bsem\s+\w+/i, /\bwithout\b/i,
];

// === Utility Functions ===

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    if (mins > 0) {
        return `${mins}m ${secs}s`;
    }
    return `${secs}s`;
}

function updateLoadingTimer() {
    if (!loadingStartTime) return;
    
    const elapsed = (Date.now() - loadingStartTime) / 1000;
    const timerEl = document.getElementById('loading-timer');
    if (timerEl) {
        timerEl.textContent = formatTime(elapsed);
        
        // Change color based on time
        if (elapsed > 120) {
            timerEl.style.color = 'var(--error)';
        } else if (elapsed > 60) {
            timerEl.style.color = 'var(--warning)';
        } else {
            timerEl.style.color = 'var(--success)';
        }
    }
}

function showLoading(text = 'Processing...') {
    elements.loadingText.textContent = text;
    elements.loading.classList.add('active');
    
    // Create new AbortController for this operation
    currentAbortController = new AbortController();
    
    // Start timer
    loadingStartTime = Date.now();
    const timerEl = document.getElementById('loading-timer');
    if (timerEl) {
        timerEl.textContent = '0s';
        timerEl.style.color = 'var(--success)';
    }
    
    // Update timer every second
    if (loadingTimer) clearInterval(loadingTimer);
    loadingTimer = setInterval(updateLoadingTimer, 1000);
}

function hideLoading() {
    elements.loading.classList.remove('active');
    
    // Stop timer and show final time
    if (loadingTimer) {
        clearInterval(loadingTimer);
        loadingTimer = null;
    }
    
    if (loadingStartTime) {
        const elapsed = (Date.now() - loadingStartTime) / 1000;
        console.log(`⏱️ Operation completed in ${formatTime(elapsed)}`);
        loadingStartTime = null;
    }
    
    // Clear abort controller
    currentAbortController = null;
}

function cancelOperation() {
    if (currentAbortController) {
        currentAbortController.abort();
        console.log('🚫 Operation cancelled by user');
        
        const elapsed = loadingStartTime ? (Date.now() - loadingStartTime) / 1000 : 0;
        setStatus(`Cancelled after ${formatTime(elapsed)}`, 'error');
    }
    hideLoading();
}

// Setup cancel button
document.addEventListener('DOMContentLoaded', () => {
    const cancelBtn = document.getElementById('cancel-operation');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', cancelOperation);
    }
    
    // Setup "Go to Inpaint" button
    const goToInpaint = document.getElementById('go-to-inpaint');
    if (goToInpaint) {
        goToInpaint.addEventListener('click', () => {
            // Switch to inpaint tab
            document.querySelector('[data-tab="inpaint"]').click();
            // Hide alert
            if (elements.editAlert) {
                elements.editAlert.style.display = 'none';
            }
        });
    }
    
    // Setup example prompt buttons
    document.querySelectorAll('.example-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const prompt = btn.dataset.prompt;
            if (elements.editPrompt) {
                elements.editPrompt.value = prompt;
                // Clear any warnings since this is a good prompt
                if (elements.editAlert) {
                    elements.editAlert.style.display = 'none';
                }
            }
        });
    });
});

function setStatus(text, type = 'ready') {
    const statusEl = elements.status;
    const dot = statusEl.querySelector('.status-dot');
    const span = statusEl.querySelector('span:last-child');
    
    span.textContent = text;
    dot.style.background = type === 'error' ? 'var(--error)' : 
                           type === 'busy' ? 'var(--warning)' : 'var(--success)';
}

async function apiRequest(endpoint, options = {}) {
    // Add abort signal if available
    const fetchOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        ...options,
    };
    
    // Include abort signal for cancellation support
    if (currentAbortController) {
        fetchOptions.signal = currentAbortController.signal;
    }
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, fetchOptions);
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Request failed' }));
            throw new Error(error.detail || 'Request failed');
        }
        
        return response.json();
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error('Operation cancelled by user');
        }
        throw error;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMessage(text) {
    // Simple markdown-like formatting
    return text
        .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
}

/**
 * Check if prompt suggests removal intent (should use inpaint instead of edit)
 */
function checkRemovalIntent(prompt) {
    return REMOVAL_PATTERNS.some(pattern => pattern.test(prompt));
}

/**
 * Show warning when user tries to use EDIT for removal
 */
function showEditWarning(message) {
    if (elements.editAlert && elements.editAlertText) {
        elements.editAlertText.textContent = message;
        elements.editAlert.style.display = 'flex';
    }
}

/**
 * Hide edit warning
 */
function hideEditWarning() {
    if (elements.editAlert) {
        elements.editAlert.style.display = 'none';
    }
}

/**
 * Show suggestions after edit
 */
function showEditSuggestions(suggestions) {
    if (elements.editSuggestions && elements.editSuggestionsList && suggestions.length > 0) {
        elements.editSuggestionsList.innerHTML = suggestions.map(s => `<li>${s}</li>`).join('');
        elements.editSuggestions.style.display = 'block';
    }
}

// === Tab Navigation ===

document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        
        // Update nav buttons
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update tab content
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        document.getElementById(`tab-${tab}`).classList.add('active');
        
        currentTab = tab;
    });
});

// === Chat ===

function addMessage(content, role = 'assistant') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.innerHTML = `
        <div class="message-content">
            ${formatMessage(content)}
        </div>
    `;
    elements.chatMessages.appendChild(messageDiv);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

async function sendChatMessage() {
    const message = elements.chatInput.value.trim();
    if (!message) return;
    
    // Add user message
    addMessage(escapeHtml(message), 'user');
    elements.chatInput.value = '';
    elements.chatInput.style.height = 'auto';
    
    setStatus('Thinking...', 'busy');
    
    try {
        const response = await apiRequest('/api/chat', {
            method: 'POST',
            body: JSON.stringify({
                message,
                model: elements.modelSelect.value,
            }),
        });
        
        addMessage(response.response, 'assistant');
        setStatus('Ready');
    } catch (error) {
        addMessage(`Error: ${error.message}`, 'assistant');
        setStatus('Error', 'error');
    }
}

elements.chatSend.addEventListener('click', sendChatMessage);

elements.chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
    }
});

// Auto-resize textarea
elements.chatInput.addEventListener('input', () => {
    elements.chatInput.style.height = 'auto';
    elements.chatInput.style.height = Math.min(elements.chatInput.scrollHeight, 200) + 'px';
});

// === Image Generation ===

// Update slider values
elements.genSteps.addEventListener('input', (e) => {
    document.getElementById('steps-val').textContent = e.target.value;
});

elements.genGuidance.addEventListener('input', (e) => {
    document.getElementById('guidance-val').textContent = e.target.value;
});

elements.editStrength.addEventListener('input', (e) => {
    document.getElementById('strength-val').textContent = e.target.value;
});

// Check prompt on input for edit tab
elements.editPrompt.addEventListener('input', (e) => {
    const prompt = e.target.value;
    if (checkRemovalIntent(prompt)) {
        showEditWarning(
            'It looks like you want to REMOVE something. The EDIT tab transforms the entire image. ' +
            'To remove specific objects, use the INPAINT tab.'
        );
    } else {
        hideEditWarning();
    }
});

elements.generateBtn.addEventListener('click', async () => {
    const prompt = elements.genPrompt.value.trim();
    if (!prompt) {
        alert('Please describe the image you want to generate');
        return;
    }
    
    showLoading('Generating image from scratch...');
    setStatus('Generating...', 'busy');
    
    try {
        const response = await apiRequest('/api/image/generate', {
            method: 'POST',
            body: JSON.stringify({
                prompt,
                negative_prompt: elements.genNegative.value || 'blurry, low quality, distorted, ugly, deformed',
                width: parseInt(elements.genWidth.value),
                height: parseInt(elements.genHeight.value),
                steps: parseInt(elements.genSteps.value),
                guidance_scale: parseFloat(elements.genGuidance.value),
                seed: elements.genSeed.value ? parseInt(elements.genSeed.value) : null,
            }),
        });
        
        // Display image
        elements.genPreview.innerHTML = `<img src="data:image/png;base64,${response.images[0]}" alt="Generated">`;
        setStatus('Ready');
    } catch (error) {
        alert(`Generation failed: ${error.message}`);
        setStatus('Error', 'error');
    } finally {
        hideLoading();
    }
});

// === Image Editing ===

// Upload area handlers
elements.uploadArea.addEventListener('click', () => {
    elements.editFile.click();
});

elements.uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.uploadArea.style.borderColor = 'var(--accent)';
});

elements.uploadArea.addEventListener('dragleave', () => {
    elements.uploadArea.style.borderColor = '';
});

elements.uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.uploadArea.style.borderColor = '';
    
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        handleImageUpload(file);
    }
});

elements.editFile.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        handleImageUpload(file);
    }
});

function handleImageUpload(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        uploadedImage = e.target.result.split(',')[1]; // Get base64 part
        elements.editOriginal.innerHTML = `<img src="${e.target.result}" alt="Original">`;
        elements.uploadArea.innerHTML = `
            <span class="upload-icon">✅</span>
            <p>Image loaded! Click to change</p>
        `;
    };
    reader.readAsDataURL(file);
}

elements.editBtn.addEventListener('click', async () => {
    if (!uploadedImage) {
        alert('Upload an image first');
        return;
    }
    
    const prompt = elements.editPrompt.value.trim();
    if (!prompt) {
        alert('Describe the transformation you want to apply');
        return;
    }
    
    // Warn if prompt looks like removal
    if (checkRemovalIntent(prompt)) {
        const proceed = confirm(
            '⚠️ Your prompt seems to request a REMOVAL.\n\n' +
            'The EDIT tab transforms the ENTIRE image, it does not remove specific objects.\n\n' +
            'To remove objects, use the INPAINT tab.\n\n' +
            'Do you want to continue with EDIT anyway?'
        );
        if (!proceed) {
            return;
        }
    }
    
    const isQuick = document.getElementById('edit-quick').checked;
    const mode = isQuick ? 'quick' : 'full';
    
    showLoading(`Transforming image (${mode} mode)...`);
    setStatus('Transforming...', 'busy');
    
    // Hide any previous suggestions
    if (elements.editSuggestions) {
        elements.editSuggestions.style.display = 'none';
    }
    
    try {
        const response = await apiRequest('/api/image/edit', {
            method: 'POST',
            body: JSON.stringify({
                image: uploadedImage,
                prompt,
                strength: parseFloat(elements.editStrength.value),
                steps: isQuick ? 15 : 25,
                quick: isQuick,
            }),
        });
        
        elements.editResult.innerHTML = `<img src="data:image/png;base64,${response.images[0]}" alt="Result">`;
        
        // Show warnings and suggestions if any
        if (response.warnings && response.warnings.length > 0) {
            response.warnings.forEach(w => console.warn(w));
        }
        
        if (response.suggestions && response.suggestions.length > 0) {
            showEditSuggestions(response.suggestions);
        }
        
        setStatus('Ready');
    } catch (error) {
        alert(`Edit error: ${error.message}`);
        setStatus('Error', 'error');
    } finally {
        hideLoading();
    }
});

// === Code Generation ===

elements.codeBtn.addEventListener('click', async () => {
    const prompt = elements.codePrompt.value.trim();
    if (!prompt) {
        alert('Describe the code you need');
        return;
    }
    
    showLoading('Generating code...');
    setStatus('Coding...', 'busy');
    
    try {
        const language = elements.codeLang.value;
        const fullPrompt = `Create ${language} code for: ${prompt}. Provide clean and well-commented code.`;
        
        const response = await apiRequest('/api/code', {
            method: 'POST',
            body: JSON.stringify({
                message: fullPrompt,
            }),
        });
        
        elements.codeOutput.innerHTML = `<code>${escapeHtml(response.code)}</code>`;
        setStatus('Ready');
    } catch (error) {
        elements.codeOutput.innerHTML = `<code>Error: ${escapeHtml(error.message)}</code>`;
        setStatus('Error', 'error');
    } finally {
        hideLoading();
    }
});

elements.copyCode.addEventListener('click', () => {
    const code = elements.codeOutput.textContent;
    navigator.clipboard.writeText(code).then(() => {
        elements.copyCode.textContent = '✓ Copied!';
        setTimeout(() => {
            elements.copyCode.textContent = '📋 Copy';
        }, 2000);
    });
});

// === Inpaint ===

const inpaint = {
    canvas: null,
    maskCanvas: null,
    cursorCanvas: null,
    ctx: null,
    maskCtx: null,
    cursorCtx: null,
    image: null,
    imageData: null,
    isDrawing: false,
    brushSize: 30,
    tool: 'brush', // 'brush' or 'eraser'
    lastX: 0,
    lastY: 0,
};

// Initialize Inpaint
function initInpaint() {
    inpaint.canvas = document.getElementById('inpaint-canvas');
    inpaint.maskCanvas = document.getElementById('mask-canvas');
    
    if (!inpaint.canvas || !inpaint.maskCanvas) return;
    
    inpaint.ctx = inpaint.canvas.getContext('2d');
    inpaint.maskCtx = inpaint.maskCanvas.getContext('2d');
    
    // Create cursor canvas for brush preview
    createCursorCanvas();
    
    // Mouse events
    inpaint.maskCanvas.addEventListener('mousedown', startDraw);
    inpaint.maskCanvas.addEventListener('mousemove', handleMouseMove);
    inpaint.maskCanvas.addEventListener('mouseup', stopDraw);
    inpaint.maskCanvas.addEventListener('mouseleave', handleMouseLeave);
    
    // Touch events
    inpaint.maskCanvas.addEventListener('touchstart', handleTouch);
    inpaint.maskCanvas.addEventListener('touchmove', handleTouch);
    inpaint.maskCanvas.addEventListener('touchend', stopDraw);
    
    // Upload
    const uploadArea = document.getElementById('inpaint-upload');
    const fileInput = document.getElementById('inpaint-file');
    
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--accent)';
    });
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '';
    });
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '';
        if (e.dataTransfer.files[0]) loadInpaintImage(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', (e) => {
        if (e.target.files[0]) loadInpaintImage(e.target.files[0]);
    });
    
    // Tools
    document.getElementById('tool-brush')?.addEventListener('click', () => setTool('brush'));
    document.getElementById('tool-eraser')?.addEventListener('click', () => setTool('eraser'));
    document.getElementById('tool-clear')?.addEventListener('click', clearMask);
    
    // Brush size
    const brushSlider = document.getElementById('brush-size');
    brushSlider?.addEventListener('input', (e) => {
        inpaint.brushSize = parseInt(e.target.value);
        document.getElementById('brush-size-val').textContent = inpaint.brushSize;
    });
    
    // Action change - show/hide prompt based on action
    const actionSelect = document.getElementById('inpaint-action');
    actionSelect?.addEventListener('change', (e) => {
        const promptGroup = document.getElementById('inpaint-prompt-group');
        const promptInput = document.getElementById('inpaint-prompt');
        
        if (e.target.value === 'remove') {
            promptGroup.style.display = 'none';
        } else {
            promptGroup.style.display = 'block';
            promptInput.placeholder = e.target.value === 'add' 
                ? 'Ex: dragon tattoo, sunglasses, gold earring...'
                : 'Ex: red shirt, blonde hair, beach background...';
        }
    });
    
    // Apply button
    document.getElementById('inpaint-btn')?.addEventListener('click', applyInpaint);
}

function loadInpaintImage(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            // Resize if too large
            let w = img.width;
            let h = img.height;
            const maxSize = 512;
            
            if (w > maxSize || h > maxSize) {
                const ratio = Math.min(maxSize / w, maxSize / h);
                w = Math.floor(w * ratio);
                h = Math.floor(h * ratio);
            }
            
            // Make multiple of 8
            w = Math.floor(w / 8) * 8;
            h = Math.floor(h / 8) * 8;
            
            // Setup canvases
            inpaint.canvas.width = w;
            inpaint.canvas.height = h;
            inpaint.maskCanvas.width = w;
            inpaint.maskCanvas.height = h;
            
            // Setup cursor canvas
            if (inpaint.cursorCanvas) {
                inpaint.cursorCanvas.width = w;
                inpaint.cursorCanvas.height = h;
            }
            
            // Draw image
            inpaint.ctx.drawImage(img, 0, 0, w, h);
            inpaint.image = img;
            inpaint.imageData = e.target.result;
            
            // Clear mask
            inpaint.maskCtx.fillStyle = 'rgba(0, 0, 0, 0)';
            inpaint.maskCtx.clearRect(0, 0, w, h);
            
            // Update UI
            document.getElementById('canvas-placeholder').classList.add('hidden');
            document.getElementById('inpaint-tools').style.display = 'block';
            document.getElementById('inpaint-btn').disabled = false;
            
            const uploadArea = document.getElementById('inpaint-upload');
            uploadArea.innerHTML = '<span class="upload-icon">✅</span><p>Image loaded! Click to change</p>';
            uploadArea.classList.add('loaded');
            
            // Hide cursor initially
            hideCursor();
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function createCursorCanvas() {
    // Create a canvas for the cursor preview
    const container = document.getElementById('canvas-container');
    if (!container) return;
    
    let cursorCanvas = document.getElementById('cursor-canvas');
    if (!cursorCanvas) {
        cursorCanvas = document.createElement('canvas');
        cursorCanvas.id = 'cursor-canvas';
        cursorCanvas.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            pointer-events: none;
            z-index: 3;
        `;
        container.appendChild(cursorCanvas);
    }
    inpaint.cursorCanvas = cursorCanvas;
    inpaint.cursorCtx = cursorCanvas.getContext('2d');
}

function updateCursorCanvas(x, y) {
    if (!inpaint.cursorCanvas || !inpaint.cursorCtx) return;
    
    const ctx = inpaint.cursorCtx;
    ctx.clearRect(0, 0, inpaint.cursorCanvas.width, inpaint.cursorCanvas.height);
    
    // Draw brush cursor
    ctx.beginPath();
    ctx.arc(x, y, inpaint.brushSize / 2, 0, Math.PI * 2);
    
    if (inpaint.tool === 'brush') {
        ctx.strokeStyle = 'rgba(99, 102, 241, 0.8)';
        ctx.fillStyle = 'rgba(99, 102, 241, 0.2)';
        ctx.setLineDash([]);
    } else {
        // Eraser - show red dashed circle
        ctx.strokeStyle = 'rgba(239, 68, 68, 0.8)';
        ctx.fillStyle = 'rgba(239, 68, 68, 0.2)';
        ctx.setLineDash([4, 4]);
    }
    
    ctx.lineWidth = 2;
    ctx.fill();
    ctx.stroke();
    ctx.setLineDash([]);
}

function hideCursor() {
    if (inpaint.cursorCtx && inpaint.cursorCanvas) {
        inpaint.cursorCtx.clearRect(0, 0, inpaint.cursorCanvas.width, inpaint.cursorCanvas.height);
    }
}

function setTool(tool) {
    inpaint.tool = tool;
    document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`tool-${tool}`).classList.add('active');
    
    // Update cursor style
    if (inpaint.maskCanvas) {
        inpaint.maskCanvas.style.cursor = 'none'; // Hide default cursor, we use custom
    }
    
    // Update tool indicator
    const indicator = document.getElementById('tool-indicator');
    if (indicator) {
        indicator.className = `tool-indicator ${tool}`;
        indicator.innerHTML = tool === 'brush' 
            ? '🖌️ Brush - Mark area' 
            : '🧹 Eraser - Unmark area';
    }
}

function startDraw(e) {
    inpaint.isDrawing = true;
    const rect = inpaint.maskCanvas.getBoundingClientRect();
    inpaint.lastX = e.clientX - rect.left;
    inpaint.lastY = e.clientY - rect.top;
    draw(e);
}

function handleMouseMove(e) {
    const rect = inpaint.maskCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Update cursor preview
    updateCursorCanvas(x, y);
    
    // Draw if mouse is down
    if (inpaint.isDrawing) {
        draw(e);
    }
}

function handleMouseLeave() {
    stopDraw();
    hideCursor();
}

function draw(e) {
    if (!inpaint.isDrawing) return;
    
    const rect = inpaint.maskCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Draw line from last position to current for smooth strokes
    inpaint.maskCtx.beginPath();
    inpaint.maskCtx.moveTo(inpaint.lastX, inpaint.lastY);
    inpaint.maskCtx.lineTo(x, y);
    inpaint.maskCtx.lineWidth = inpaint.brushSize;
    inpaint.maskCtx.lineCap = 'round';
    inpaint.maskCtx.lineJoin = 'round';
    
    if (inpaint.tool === 'brush') {
        inpaint.maskCtx.strokeStyle = 'rgba(99, 102, 241, 0.5)'; // Semi-transparent purple
        inpaint.maskCtx.stroke();
    } else {
        // Eraser
        inpaint.maskCtx.globalCompositeOperation = 'destination-out';
        inpaint.maskCtx.strokeStyle = 'rgba(255, 255, 255, 1)';
        inpaint.maskCtx.stroke();
        inpaint.maskCtx.globalCompositeOperation = 'source-over';
    }
    
    inpaint.lastX = x;
    inpaint.lastY = y;
}

function handleTouch(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent(e.type === 'touchstart' ? 'mousedown' : 'mousemove', {
        clientX: touch.clientX,
        clientY: touch.clientY
    });
    inpaint.maskCanvas.dispatchEvent(mouseEvent);
}

function stopDraw() {
    inpaint.isDrawing = false;
}

function clearMask() {
    if (inpaint.maskCtx) {
        inpaint.maskCtx.clearRect(0, 0, inpaint.maskCanvas.width, inpaint.maskCanvas.height);
    }
}

function getMaskAsBase64() {
    // Create a black and white mask
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = inpaint.maskCanvas.width;
    tempCanvas.height = inpaint.maskCanvas.height;
    const tempCtx = tempCanvas.getContext('2d');
    
    // Fill with black (keep)
    tempCtx.fillStyle = 'black';
    tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
    
    // Get mask data and draw white where painted
    const maskData = inpaint.maskCtx.getImageData(0, 0, inpaint.maskCanvas.width, inpaint.maskCanvas.height);
    const tempData = tempCtx.getImageData(0, 0, tempCanvas.width, tempCanvas.height);
    
    for (let i = 0; i < maskData.data.length; i += 4) {
        if (maskData.data[i + 3] > 0) { // If has any alpha
            tempData.data[i] = 255;     // R
            tempData.data[i + 1] = 255; // G
            tempData.data[i + 2] = 255; // B
            tempData.data[i + 3] = 255; // A
        }
    }
    
    tempCtx.putImageData(tempData, 0, 0);
    return tempCanvas.toDataURL('image/png').split(',')[1];
}

async function applyInpaint() {
    const action = document.getElementById('inpaint-action').value;
    const promptInput = document.getElementById('inpaint-prompt');
    const contextInput = document.getElementById('inpaint-context');
    const isQuick = document.getElementById('inpaint-quick').checked;
    
    let prompt = '';
    let context = contextInput ? contextInput.value.trim() : '';
    
    if (action === 'remove') {
        // For removal, we NEED context to fill properly
        // Without context, SD models just hallucinate random stuff
        if (!context) {
            // Ask user for context
            context = window.prompt(
                '⚠️ IMPORTANT for better results!\n\n' +
                'Describe what SHOULD appear in place of the removed object.\n\n' +
                'Example: "white brick wall", "office desk", "forest background"\n\n' +
                'Tip: Be specific! The model needs to know what to draw in its place.',
                'background, natural environment, seamless continuation'
            );
            
            if (!context) {
                // User cancelled, use generic but warn them
                context = 'background, natural environment, seamless continuation';
                console.warn('⚠️ Using generic context - result may not be ideal');
            }
        }
        
        prompt = `${context}, high quality, photorealistic, same lighting, seamless blend, no artifacts`;
    } else {
        prompt = promptInput.value.trim();
        if (!prompt) {
            alert('Describe what you want to do in the painted area');
            return;
        }
        // Add context if provided
        if (context) {
            prompt = `${prompt}, ${context}`;
        }
    }
    
    // Check if mask has any content
    const maskData = inpaint.maskCtx.getImageData(0, 0, inpaint.maskCanvas.width, inpaint.maskCanvas.height);
    let hasMask = false;
    for (let i = 3; i < maskData.data.length; i += 4) {
        if (maskData.data[i] > 0) {
            hasMask = true;
            break;
        }
    }
    
    if (!hasMask) {
        alert('⚠️ You need to paint the area you want to edit!\n\nUse the brush to mark the region of the image.');
        return;
    }
    
    // Get image as base64
    const imageBase64 = inpaint.canvas.toDataURL('image/png').split(',')[1];
    const maskBase64 = getMaskAsBase64();
    
    const actionText = action === 'remove' ? 'Removing' : action === 'add' ? 'Adding' : 'Replacing';
    showLoading(`${actionText} in selected area...`);
    setStatus('Processing...', 'busy');
    
    try {
        const response = await apiRequest('/api/image/inpaint', {
            method: 'POST',
            body: JSON.stringify({
                image: imageBase64,
                mask: maskBase64,
                prompt: prompt,
                steps: isQuick ? 15 : 25,
            }),
        });
        
        // Show result
        document.getElementById('inpaint-result-container').style.display = 'block';
        document.getElementById('inpaint-result').innerHTML = 
            `<img src="data:image/png;base64,${response.images[0]}" alt="Result">`;
        
        setStatus('Ready');
    } catch (error) {
        alert(`Inpaint error: ${error.message}`);
        setStatus('Error', 'error');
    } finally {
        hideLoading();
    }
}

// === Load Models on Start ===

async function loadModels() {
    try {
        const response = await apiRequest('/api/models');
        const models = response.models || [];
        
        if (models.length > 0) {
            elements.modelSelect.innerHTML = models.map(m => 
                `<option value="${m.name}">${m.name}</option>`
            ).join('');
        }
    } catch (error) {
        console.log('Could not load models, using defaults');
    }
}

// Initialize
loadModels();
initInpaint();
