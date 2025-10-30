// Add to the top of popup.js
const API_URL = 'http://localhost:8000/agent-chat';
const SUMMARIZE_URL = 'http://localhost:8000/summarize';



// State
let messages = [];
let isLoading = false;
let loadingMessageElement = null;

// DOM Elements
const chatContainer = document.getElementById('chatContainer');
const chatForm = document.getElementById('chatForm');
const promptInput = document.getElementById('promptInput');
const sendButton = document.getElementById('sendButton');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadMessages();
    renderMessages();
    chatForm.addEventListener('submit', handleSubmit);
    summarizeBtn.addEventListener('click', handleSummarize); // ADD THIS
});

const summarizeBtn = document.getElementById('summarizeBtn');

async function handleSummarize() {
    if (isLoading) return;
    
    console.log('[DEBUG] Summarize clicked');
    
    try {
        setLoading(true);
        
        // Get active tab
        const tabs = await browser.tabs.query({ active: true, currentWindow: true });
        const activeTab = tabs[0];
        
        if (!activeTab) {
            throw new Error('No active tab found');
        }
        
        console.log('[DEBUG] Active tab:', activeTab.url);
        
        // Check if it's a restricted page
        if (activeTab.url.startsWith('about:') || 
            activeTab.url.startsWith('moz-extension:') ||
            activeTab.url.startsWith('chrome:')) {
            throw new Error('Cannot summarize browser internal pages. Please try on a regular webpage.');
        }
        
        showLoading('Extracting page content...');
        
        // Send message to content script with timeout
        let response;
        try {
            response = await browser.tabs.sendMessage(activeTab.id, {
                action: 'getPageContent'
            });
        } catch (e) {
            throw new Error('Could not connect to page. Please reload the page and try again.');
        }
        
        if (!response || !response.content) {
            throw new Error('Could not extract page content');
        }
        
        console.log('[DEBUG] Got content, length:', response.content.length);
        
        // Add user message
        messages.push({ 
            content: `📄 Summarize: ${response.title || response.url}`, 
            isUser: true 
        });
        appendMessage(`📄 Summarizing: ${response.title || response.url}`, true);
        
        // Create assistant message
        const assistantMessage = { content: '', isUser: false };
        messages.push(assistantMessage);
        
        updateLoadingStatus('Generating summary...');
        
        // Stream summary
        await streamSummary(response, assistantMessage);
        
        await saveMessages();
        
    } catch (error) {
        console.error('[DEBUG] Summarization error:', error);
        
        const errorMsg = `Error: ${error.message}`;
        messages.push({ content: errorMsg, isUser: false });
        hideLoading();
        appendMessage(errorMsg, false);
        
        await saveMessages();
    } finally {
        setLoading(false);
    }
}

// ADD THIS FUNCTION
async function streamSummary(pageData, assistantMessage) {
    console.log('[DEBUG] Streaming summary for:', pageData.url);
    
    const response = await fetch(SUMMARIZE_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            content: pageData.content,
            url: pageData.url,
            title: pageData.title
        }),
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    hideLoading();
    let messageElement = appendMessage('', false);
    let textElement = messageElement.querySelector('.text');
    
    let buffer = '';
    
    while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
            console.log('[DEBUG] Summary stream complete');
            break;
        }
        
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
            if (!line.trim() || !line.startsWith('data: ')) continue;
            
            const jsonData = line.substring(6);
            
            try {
                const event = JSON.parse(jsonData);
                
                if (event.type === 'token') {
                    assistantMessage.content += event.content || '';
                    textElement.textContent = assistantMessage.content;
                    scrollToBottom();
                } else if (event.type === 'error') {
                    throw new Error(event.content);
                }
            } catch (e) {
                console.error('[DEBUG] Error parsing summary event:', e);
            }
        }
    }
}

// Load messages from storage
async function loadMessages() {
    try {
        const result = await chrome.storage.local.get(['chatMessages']);
        if (result.chatMessages) {
            messages = result.chatMessages;
        }
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

// Save messages to storage
async function saveMessages() {
    try {
        await chrome.storage.local.set({ chatMessages: messages });
    } catch (error) {
        console.error('Error saving messages:', error);
    }
}

// Render all messages
function renderMessages() {
    chatContainer.innerHTML = '';
    
    if (messages.length === 0) {
        chatContainer.innerHTML = '<div class="empty-state">👋 Start a conversation!</div>';
        return;
    }
    
    messages.forEach(message => {
        appendMessage(message.content, message.isUser, false);
    });
    
    scrollToBottom();
}

// Append a single message
function appendMessage(content, isUser, animate = true) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
    
    const iconDiv = document.createElement('div');
    iconDiv.className = 'icon';
    iconDiv.textContent = isUser ? 'You' : '🤖';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'text';
    textDiv.textContent = content;
    
    messageDiv.appendChild(iconDiv);
    messageDiv.appendChild(textDiv);
    
    chatContainer.appendChild(messageDiv);
    
    if (animate) {
        scrollToBottom();
    }
    
    return messageDiv;
}

// Show loading indicator
function showLoading(status = 'Thinking...') {
    if (loadingMessageElement) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant loading';
    
    const iconDiv = document.createElement('div');
    iconDiv.className = 'icon';
    iconDiv.textContent = '🤖';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'text';
    textDiv.textContent = status;
    
    messageDiv.appendChild(iconDiv);
    messageDiv.appendChild(textDiv);
    
    chatContainer.appendChild(messageDiv);
    loadingMessageElement = textDiv;
    
    scrollToBottom();
}

// Update loading status
function updateLoadingStatus(status) {
    if (loadingMessageElement) {
        loadingMessageElement.textContent = status;
    }
}

// Hide loading indicator
function hideLoading() {
    if (loadingMessageElement) {
        loadingMessageElement.parentElement.remove();
        loadingMessageElement = null;
    }
}

// Scroll to bottom
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Handle form submission
async function handleSubmit(e) {
    e.preventDefault();
    
    const prompt = promptInput.value.trim();
    if (!prompt || isLoading) return;
    
    // Add user message
    messages.push({ content: prompt, isUser: true });
    appendMessage(prompt, true);
    
    // Clear input and disable
    promptInput.value = '';
    setLoading(true);
    
    // Save messages
    await saveMessages();
    
    // Create assistant message
    const assistantMessage = { content: '', isUser: false };
    messages.push(assistantMessage);
    
    // Show loading
    showLoading('Thinking...');
    
    try {
        await streamResponse(prompt, assistantMessage);
    } catch (error) {
        console.error('Error:', error);
        assistantMessage.content = `Error: ${error.message}`;
        hideLoading();
        appendMessage(assistantMessage.content, false);
    } finally {
        setLoading(false);
        await saveMessages();
    }
}

// Stream response from API
// Stream response from API
async function streamResponse(prompt, assistantMessage) {
    console.log('[DEBUG] Starting streamResponse for:', prompt);
    
    const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ input: prompt }),
    });
    
    console.log('[DEBUG] Response status:', response.status);
    console.log('[DEBUG] Response headers:', [...response.headers.entries()]);
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    console.log('[DEBUG] Got reader, starting to read...');
    
    hideLoading();
    let messageElement = appendMessage('', false);
    let textElement = messageElement.querySelector('.text');
    
    let buffer = '';
    let chunkCount = 0;
    
    while (true) {
        const { done, value } = await reader.read();
        chunkCount++;
        
        console.log(`[DEBUG] Chunk ${chunkCount}, done: ${done}, bytes:`, value?.length);
        
        if (done) {
            console.log('[DEBUG] Stream complete');
            break;
        }
        
        const chunk = decoder.decode(value, { stream: true });
        console.log('[DEBUG] Decoded chunk:', chunk);
        
        buffer += chunk;
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer
        
        for (const line of lines) {
            console.log('[DEBUG] Processing line:', line);
            
            if (!line.trim() || !line.startsWith('data: ')) continue;
            
            const jsonData = line.substring(6);
            console.log('[DEBUG] JSON data:', jsonData);
            
            try {
                const agentEvent = JSON.parse(jsonData);
                console.log('[DEBUG] Parsed event:', agentEvent);
                
                switch (agentEvent.type) {
                    case 'token':
                        assistantMessage.content += agentEvent.content || '';
                        textElement.textContent = assistantMessage.content;
                        scrollToBottom();
                        break;
                    case 'tool_start':
                        console.log('[DEBUG] Tool start:', agentEvent.name);
                        showLoading(`🛠️ Calling tool: ${agentEvent.name}...`);
                        break;
                    case 'tool_end':
                        console.log('[DEBUG] Tool end:', agentEvent.name);
                        hideLoading();
                        break;
                    case 'error':
                        console.error('[DEBUG] Error event:', agentEvent.content);
                        assistantMessage.content = `Error: ${agentEvent.content}`;
                        textElement.textContent = assistantMessage.content;
                        break;
                }
            } catch (e) {
                console.error('[DEBUG] Error parsing JSON:', e, 'Raw:', jsonData);
            }
        }
    }
    
    hideLoading();
    console.log('[DEBUG] Final message:', assistantMessage.content);
}
// Set loading state
function setLoading(loading) {
    isLoading = loading;
    promptInput.disabled = loading;
    sendButton.disabled = loading;
}

// Add clear chat functionality (optional)
function clearChat() {
    messages = [];
    saveMessages();
    renderMessages();
}

// Expose clear function to console for debugging
window.clearChat = clearChat;