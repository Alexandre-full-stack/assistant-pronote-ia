/**
 * Gestionnaire du chat avec l'IA
 * Gère l'interface de conversation et l'interaction avec l'API IA
 */

class ChatManager {
    constructor() {
        this.messages = [];
        this.isTyping = false;
        this.initEventListeners();
    }

    /**
     * Initialise les event listeners
     */
    initEventListeners() {
        const sendBtn = document.getElementById('send-btn');
        const chatInput = document.getElementById('chat-input');

        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }

        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        // Boutons de suggestions
        document.querySelectorAll('.suggestion-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const question = e.target.dataset.question;
                if (question) {
                    document.getElementById('chat-input').value = question;
                    this.sendMessage();
                }
            });
        });
    }

    /**
     * Envoie un message
     */
    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();

        if (!message || this.isTyping) return;

        // Ajouter le message de l'utilisateur
        this.addMessage('user', message);
        input.value = '';

        // Afficher l'indicateur de typing
        this.showTypingIndicator();
        this.isTyping = true;

        try {
            // Préparer le contexte avec les données Pronote
            const context = this.buildContext(message);

            // Envoyer au backend
            const response = await apiClient.sendChatMessage(message, context);

            if (response.success && response.response) {
                this.addMessage('assistant', response.response);
            } else {
                this.addMessage('assistant', 'Désolé, je n\'ai pas pu traiter votre demande.');
            }
        } catch (error) {
            errorLog('Erreur chat:', error);
            this.addMessage('assistant', 'Une erreur est survenue. Veuillez réessayer.');
        } finally {
            this.hideTypingIndicator();
            this.isTyping = false;
        }
    }

    /**
     * Construit le contexte à partir des données Pronote
     */
    buildContext(message) {
        if (!window.pronoteDataManager) return null;

        const data = window.pronoteDataManager.getAllData();
        const messageLower = message.toLowerCase();

        let context = {
            student: authManager.getCurrentUser()
        };

        // Inclure les devoirs si la question concerne les devoirs
        if (messageLower.includes('devoir') || 
            messageLower.includes('dm') || 
            messageLower.includes('exercice') ||
            messageLower.includes('travail') ||
            messageLower.includes('demain') ||
            messageLower.includes('semaine')) {
            
            context.homework = data.homework.slice(0, 10).map(hw => ({
                subject: hw.subject,
                description: hw.description,
                date: hw.date,
                done: hw.done
            }));
        }

        // Inclure l'emploi du temps si la question concerne les cours
        if (messageLower.includes('emploi') || 
            messageLower.includes('cours') || 
            messageLower.includes('horaire') ||
            messageLower.includes('quand') ||
            messageLower.includes('prochain')) {
            
            context.timetable = data.timetable.slice(0, 15).map(lesson => ({
                subject: lesson.subject,
                teacher: lesson.teacher,
                start: lesson.start,
                end: lesson.end,
                room: lesson.classroom
            }));
        }

        // Inclure les notes si la question concerne les notes
        if (messageLower.includes('note') || 
            messageLower.includes('moyenne') || 
            messageLower.includes('résultat')) {
            
            context.grades = data.grades.slice(0, 20).map(grade => ({
                subject: grade.subject,
                grade: grade.grade,
                out_of: grade.out_of,
                date: grade.date
            }));
        }

        // Pour les questions générales, inclure un résumé
        if (!context.homework && !context.timetable && !context.grades) {
            context.summary = {
                homework_count: data.homework.length,
                timetable_count: data.timetable.length,
                grades_count: data.grades.length
            };
        }

        return context;
    }

    /**
     * Ajoute un message dans le chat
     */
    addMessage(role, content) {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit'
        });

        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);
        chatContainer.appendChild(messageDiv);

        // Scroller vers le bas
        chatContainer.scrollTop = chatContainer.scrollHeight;

        // Stocker le message
        this.messages.push({
            role,
            content,
            timestamp: new Date()
        });

        // Limiter le nombre de messages
        if (this.messages.length > CONFIG.MAX_CHAT_MESSAGES) {
            this.messages = this.messages.slice(-CONFIG.MAX_CHAT_MESSAGES);
            // Supprimer les anciens messages du DOM
            const messagesToRemove = chatContainer.children.length - CONFIG.MAX_CHAT_MESSAGES;
            for (let i = 0; i < messagesToRemove; i++) {
                chatContainer.removeChild(chatContainer.firstChild);
            }
        }
    }

    /**
     * Affiche l'indicateur de typing
     */
    showTypingIndicator() {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;

        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant';
        typingDiv.id = 'typing-indicator';

        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;

        typingDiv.appendChild(indicator);
        chatContainer.appendChild(typingDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    /**
     * Cache l'indicateur de typing
     */
    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    /**
     * Ajoute un message de bienvenue
     */
    addWelcomeMessage() {
        const user = authManager.getCurrentUser();
        if (user) {
            const welcomeText = `Bonjour ${user.student_name} ! Je suis ton assistant IA. 
Je peux t'aider à organiser tes devoirs, consulter ton emploi du temps et suivre tes notes. 
N'hésite pas à me poser des questions !`;
            
            this.addMessage('assistant', welcomeText);
        }
    }

    /**
     * Efface tous les messages
     */
    clearMessages() {
        const chatContainer = document.getElementById('chat-messages');
        if (chatContainer) {
            chatContainer.innerHTML = `
                <div class="message assistant">
                    <div class="message-content">
                        Bonjour ! Je suis votre assistant IA personnel. Posez-moi des questions sur vos devoirs, votre emploi du temps ou vos notes.
                    </div>
                    <div class="message-time"></div>
                </div>
            `;
        }
        this.messages = [];
    }

    /**
     * Récupère l'historique des messages
     */
    getMessages() {
        return this.messages;
    }
}

// Instance globale
window.chatManager = new ChatManager();
