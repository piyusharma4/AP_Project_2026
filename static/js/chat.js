/**
 * Acharya Prashant AI Chatbot - Chat Interface JavaScript
 * Handles chat functionality, API calls, and history management
 */

// ==================== STATE ====================
let currentChatId = null;
let isLoading = false;

// ==================== DOM ELEMENTS ====================
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const chatMessages = document.getElementById('chatMessages');
const chatHistory = document.getElementById('chatHistory');
const chatTitle = document.getElementById('chatTitle');
const chatWelcome = document.getElementById('chatWelcome');
const newChatBtn = document.getElementById('newChatBtn');
const sendBtn = document.getElementById('sendBtn');
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const chatSidebar = document.getElementById('chatSidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    loadChatHistory();
    setupEventListeners();
    console.log('✨ Acharya Prashant AI - Chat initialized');
});

// ==================== EVENT LISTENERS ====================
function setupEventListeners() {
    // Form submission
    chatForm.addEventListener('submit', handleSubmit);

    // New chat button
    newChatBtn.addEventListener('click', startNewChat);

    // Suggestion buttons
    document.querySelectorAll('.suggestion-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const question = btn.dataset.question;
            chatInput.value = question;
            handleSubmit(new Event('submit'));
        });
    });

    // Mobile menu toggle
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', toggleSidebar);
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', toggleSidebar);
    }

    // Input focus effect
    chatInput.addEventListener('focus', () => {
        chatInput.parentElement.style.boxShadow = 'var(--glow-gold)';
    });

    chatInput.addEventListener('blur', () => {
        chatInput.parentElement.style.boxShadow = 'none';
    });
}

// ==================== CHAT FUNCTIONS ====================
async function handleSubmit(e) {
    e.preventDefault();

    const message = chatInput.value.trim();
    if (!message || isLoading) return;

    // Hide welcome screen
    if (chatWelcome) {
        chatWelcome.style.display = 'none';
    }

    // Create new chat if needed
    if (!currentChatId) {
        await createNewChat();
    }

    // Add user message
    addMessage('user', message);
    chatInput.value = '';

    // Show typing indicator
    showTypingIndicator();
    isLoading = true;
    sendBtn.disabled = true;

    try {
        // Send to API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                chat_id: currentChatId
            })
        });

        const data = await response.json();

        // Remove typing indicator
        hideTypingIndicator();

        if (data.error) {
            addMessage('assistant', 'I apologize, but I encountered an error. Please try again.', []);
        } else {
            addMessage('assistant', data.answer, data.sources || []);
        }

        // Refresh chat history
        loadChatHistory();

    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        addMessage('assistant', 'I apologize, but I cannot connect to the server. Please ensure the backend is running.', []);
    } finally {
        isLoading = false;
        sendBtn.disabled = false;
    }
}

function addMessage(role, content, sources = []) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    // Parse markdown for assistant messages
    let formattedContent = content;
    if (role === 'assistant' && typeof marked !== 'undefined') {
        formattedContent = marked.parse(content);
    } else {
        formattedContent = escapeHtml(content);
    }

    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `
            <div class="message-sources">
                <strong>📚 References:</strong><br>
                ${sources.map(s => {
            const parts = s.split(': ');
            const title = parts[0];
            const url = parts[1] || '#';
            return `<a href="${url}" target="_blank">${title}</a>`;
        }).join('<br>')}
            </div>
        `;
    }

    messageDiv.innerHTML = `
        <div class="message-content">
            ${formattedContent}
            ${sourcesHtml}
        </div>
    `;

    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = '<span></span><span></span><span></span>';
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
    const typing = document.getElementById('typingIndicator');
    if (typing) {
        typing.remove();
    }
}

// ==================== CHAT HISTORY FUNCTIONS ====================
async function loadChatHistory() {
    try {
        const response = await fetch('/api/chats');
        const chats = await response.json();

        chatHistory.innerHTML = '';

        if (chats.length === 0) {
            chatHistory.innerHTML = `
                <div style="padding: 1rem; text-align: center; color: var(--text-muted); font-size: 0.9rem;">
                    No conversations yet.<br>Start a new chat!
                </div>
            `;
            return;
        }

        chats.forEach(chat => {
            const item = document.createElement('div');
            item.className = `chat-history-item ${chat.id === currentChatId ? 'active' : ''}`;
            item.innerHTML = `
                <span class="chat-history-title">${escapeHtml(chat.title)}</span>
                <button class="chat-delete-btn" data-id="${chat.id}" title="Delete chat">
                    <i class="fas fa-trash"></i>
                </button>
            `;

            // Click to load chat
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.chat-delete-btn')) {
                    loadChat(chat.id);
                }
            });

            // Delete button
            const deleteBtn = item.querySelector('.chat-delete-btn');
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                deleteChat(chat.id);
            });

            chatHistory.appendChild(item);
        });
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}

async function loadChat(chatId) {
    try {
        const response = await fetch(`/api/chats/${chatId}`);
        const chat = await response.json();

        if (chat.error) {
            console.error('Error loading chat:', chat.error);
            return;
        }

        currentChatId = chatId;
        chatTitle.textContent = chat.title;

        // Clear messages
        chatMessages.innerHTML = '';

        // Hide welcome screen
        if (chatWelcome) {
            chatWelcome.style.display = 'none';
        }

        // Add messages
        chat.messages.forEach(msg => {
            addMessage(msg.role, msg.content, msg.sources);
        });

        // Update active state in sidebar
        document.querySelectorAll('.chat-history-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`.chat-history-item[data-id="${chatId}"]`)?.classList.add('active');

        // Close mobile sidebar
        if (window.innerWidth <= 768) {
            toggleSidebar();
        }

        // Refresh history to update active state
        loadChatHistory();

    } catch (error) {
        console.error('Error loading chat:', error);
    }
}

async function createNewChat() {
    try {
        const response = await fetch('/api/chats', {
            method: 'POST'
        });
        const chat = await response.json();
        currentChatId = chat.id;
        chatTitle.textContent = chat.title;
        loadChatHistory();
    } catch (error) {
        console.error('Error creating chat:', error);
    }
}

function startNewChat() {
    currentChatId = null;
    chatTitle.textContent = 'New Conversation';
    chatMessages.innerHTML = '';

    // Show welcome screen
    if (chatWelcome) {
        chatWelcome.style.display = 'flex';
        chatMessages.appendChild(chatWelcome);
    }

    // Update sidebar
    document.querySelectorAll('.chat-history-item').forEach(item => {
        item.classList.remove('active');
    });

    // Close mobile sidebar
    if (window.innerWidth <= 768) {
        toggleSidebar();
    }

    chatInput.focus();
}

async function deleteChat(chatId) {
    if (!confirm('Are you sure you want to delete this conversation?')) return;

    try {
        await fetch(`/api/chats/${chatId}`, {
            method: 'DELETE'
        });

        // If deleting current chat, start new one
        if (chatId === currentChatId) {
            startNewChat();
        }

        loadChatHistory();
    } catch (error) {
        console.error('Error deleting chat:', error);
    }
}

// ==================== UI FUNCTIONS ====================
function toggleSidebar() {
    chatSidebar.classList.toggle('active');
    sidebarOverlay.style.display = chatSidebar.classList.contains('active') ? 'block' : 'none';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== KEYBOARD SHORTCUTS ====================
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + N for new chat
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        startNewChat();
    }

    // Escape to close mobile menu
    if (e.key === 'Escape' && chatSidebar.classList.contains('active')) {
        toggleSidebar();
    }
});
