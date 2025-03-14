document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const chatMessages = document.getElementById('chatMessages');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendMessage');
    const clearChatButton = document.getElementById('clearChat');
    const generateTimetableButton = document.getElementById('generateTimetable');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    // State variables
    let databaseComplete = false;
    
    // Initialize the chat interface
    function initChat() {
        // Auto-resize message input
        messageInput.addEventListener('input', autoResizeTextarea);
        
        // Send message when button is clicked
        sendButton.addEventListener('click', sendMessage);
        
        // Send message when Enter is pressed (without Shift)
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Clear chat
        clearChatButton.addEventListener('click', clearChat);
        
        // Generate timetable
        generateTimetableButton.addEventListener('click', generateTimetable);
        
        // Focus on input
        messageInput.focus();
        
        // Scroll to bottom of chat
        scrollToBottom();
        
        // Setup markdown renderer
        setupMarkdown();
        fetchAcademicYears();
        
    }
    
    // Auto-resize textarea as user types
    function autoResizeTextarea() {
        messageInput.style.height = 'auto';
        messageInput.style.height = (messageInput.scrollHeight) + 'px';
    }
    
    // Send message to server
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessageToChat('user', message);
        
        // Clear input and resize
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        // Focus back on input
        messageInput.focus();
        
        // Show loading overlay
        loadingOverlay.classList.remove('hidden');
        
        try {
            const response = await fetch('/chatbot/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            
            if (data.error) {
                console.error('Error:', data.error);
                addMessageToChat('assistant', 'Sorry, an error occurred. Please try again.');
                return;
            }
            
            // Add assistant response to chat
            addMessageToChat('assistant', data.response);
            
            // Update database status
            if (data.database_complete) {
                databaseComplete = true;
                enableGenerateTimetableButton();
            }
        } catch (error) {
            console.error('Error:', error);
            addMessageToChat('assistant', 'Sorry, an error occurred. Please try again.');
        } finally {
            // Hide loading overlay
            loadingOverlay.classList.add('hidden');
            
            // Scroll to bottom of chat
            scrollToBottom();
        }
    }
    
    // Add message to chat
    function addMessageToChat(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        
        const icon = document.createElement('i');
        icon.className = role === 'user' ? 'fas fa-user' : 'fas fa-robot';
        avatarDiv.appendChild(icon);
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Convert markdown to HTML if it's assistant message
        if (role === 'assistant') {
            contentDiv.innerHTML = marked.parse(content);
            // Apply syntax highlighting
            contentDiv.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        } else {
            // For user messages, just use text with line breaks
            contentDiv.textContent = content;
        }
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // Scroll to bottom of chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Clear chat
    async function clearChat() {
        if (!confirm('Are you sure you want to clear the chat history?')) {
            return;
        }
        
        try {
            const response = await fetch('/chatbot/reset', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Clear chat messages except the system welcome message
                while (chatMessages.children.length > 1) {
                    chatMessages.removeChild(chatMessages.lastChild);
                }
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }
    
    // Generate timetable
    async function generateTimetable() {
        if (!databaseComplete) {
            alert('Please add all required information before generating the timetable.');
            return;
        }
        
        // Show loading overlay
        loadingOverlay.classList.remove('hidden');
        
        // Get selected academic year
        const yearSelect = document.getElementById('yearSelect');
        const yearId = yearSelect ? yearSelect.value : null;
        
        try {
            const response = await fetch('/chatbot/generate-timetable', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ year_id: yearId })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Redirect to calendar view
                window.location.href = data.redirect;
            } else {
                alert(data.message || 'Failed to generate timetable.');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while generating the timetable. Please try again.');
        } finally {
            // Hide loading overlay
            loadingOverlay.classList.add('hidden');
        }
    }

    // Enable generate timetable button
    function enableGenerateTimetableButton() {
        generateTimetableButton.disabled = false;
    }
    
    // Setup markdown renderer
    function setupMarkdown() {
        // Set marked options
        marked.setOptions({
            breaks: true,
            gfm: true,
            tables: true,
            sanitize: false,
            highlight: function(code, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                } else {
                    return hljs.highlightAuto(code).value;
                }
            }
        });
    }

    async function fetchAcademicYears() {
        try {
            console.log("Fetching academic years...");
            const response = await fetch('/chatbot/api/academic-years');  // Ensure this matches your Flask route
            const data = await response.json();
    
            console.log("Academic Years API response:", data);
    
            const yearSelect = document.getElementById('yearSelect'); // Ensure correct ID in chatbot.html
            if (yearSelect && data.academic_years && data.academic_years.length > 0) {
                // Clear existing options except the first one
                yearSelect.innerHTML = '<option value="">All Years (Not Recommended)</option>';
                
                // Add new options dynamically
                data.academic_years.forEach(year => {
                    const option = document.createElement('option');
                    option.value = year.id;  // Using "symbol" as id
                    option.textContent = year.name; // Using "symbol" as name
                    yearSelect.appendChild(option);
                });
    
                console.log(`Added ${data.academic_years.length} academic years to dropdown`);
            } else {
                console.warn("No academic years found or select element not available");
            }
        } catch (error) {
            console.error('Error fetching academic years:', error);
        }
    }
    
    


    // Initialize
    initChat();
});