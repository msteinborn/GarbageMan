const chatHistory = document.getElementById('chatHistory');
const userInput = document.getElementById('userInput');
const chatForm = document.getElementById('chatForm');
const resetBtn = document.getElementById('resetBtn');

let isLoading = false;

async function sendMessage(message) {
    if (!message.trim() || isLoading) return;
    
    // Add user message to UI
    addMessageToUI('user', message);
    userInput.value = '';
    
    // Add loading indicator
    isLoading = true;
    const loadingDiv = addMessageToUI('loading', 'Thinking...');
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: message })
        });
        
        const data = await response.json();
        
        // Remove loading indicator
        if (loadingDiv) loadingDiv.remove();
        
        if (data.error) {
            addMessageToUI('assistant error', `Error: ${data.error}`);
        } else {
            addMessageToUI('assistant', data.response);
        }
    } catch (error) {
        if (loadingDiv) loadingDiv.remove();
        addMessageToUI('assistant error', `Connection error: ${error.message}`);
    } finally {
        isLoading = false;
        userInput.focus();
    }
}

function addMessageToUI(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role === 'error' ? 'error' : role}`;
    
    // Simple markdown-like formatting
    let formattedContent = content;
    
    messageDiv.textContent = formattedContent;
    chatHistory.appendChild(messageDiv);
    
    // Auto-scroll to bottom immediately
    setTimeout(() => {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }, 0);
    
    return messageDiv;
}

async function resetConversation() {
    if (confirm('Reset conversation history?')) {
        chatHistory.innerHTML = '';
        userInput.value = '';
        await fetch('/api/reset', { method: 'POST' });
        addMessageToUI('assistant', 'Conversation reset. What can I help you with?');
    }
}

// Event listeners
chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const message = userInput.value.trim();
    if (message) {
        sendMessage(message);
    }
});

resetBtn.addEventListener('click', resetConversation);

// Initial greeting
window.addEventListener('load', () => {
    addMessageToUI('assistant', 'Hello! How can I assist you today?');
});
