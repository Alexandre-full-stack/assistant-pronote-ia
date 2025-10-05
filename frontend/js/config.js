/**
 * Configuration globale de l'application
 * IMPORTANT: Remplacez les valeurs par vos vraies URLs en production
 */

const CONFIG = {
    // URL de votre backend
    // Développement local: http://localhost:8000
    // Production Railway: https://votre-app.railway.app
    API_BASE_URL: 'http://localhost:8000',
    
    // Clé API OpenRouter (à remplacer par votre vraie clé)
    // ATTENTION: NE JAMAIS exposer votre vraie clé ici en production!
    // Utilisez plutôt le système d'authentification OAuth du backend
    OPENROUTER_API_KEY: 'XXXXXXXXXXXXXXXX',
    
    // Configuration du chat IA
    AI_CONFIG: {
        model: 'deepseek/deepseek-r1:free', // Modèle par défaut
        temperature: 0.7,
        max_tokens: 1000,
        system_prompt: `Tu es un assistant pédagogique intelligent. 
        Tu aides les élèves avec leurs devoirs, leur emploi du temps et leurs notes Pronote.
        Réponds de manière claire, concise et encourageante.`
    },
    
    // Timeouts
    TIMEOUTS: {
        request: 30000, // 30 secondes
        session: 24 * 60 * 60 * 1000 // 24 heures
    },
    
    // Nombre de messages à afficher dans le chat
    MAX_CHAT_MESSAGES: 100,
    
    // Intervalle de rafraîchissement automatique (ms)
    AUTO_REFRESH_INTERVAL: 5 * 60 * 1000, // 5 minutes
    
    // Activer le mode debug
    DEBUG: true
};

/**
 * Fonction utilitaire pour logger uniquement en mode debug
 */
function debugLog(...args) {
    if (CONFIG.DEBUG) {
        console.log('[DEBUG]', ...args);
    }
}

/**
 * Fonction utilitaire pour logger les erreurs
 */
function errorLog(...args) {
    console.error('[ERROR]', ...args);
}

// Exporter pour utilisation globale
window.CONFIG = CONFIG;
window.debugLog = debugLog;
window.errorLog = errorLog;
