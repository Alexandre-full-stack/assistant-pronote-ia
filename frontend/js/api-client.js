/**
 * Client API pour communiquer avec le backend Python
 * Gère toutes les requêtes HTTP et l'authentification
 */

class APIClient {
    constructor() {
        this.baseURL = CONFIG.API_BASE_URL;
        this.accessToken = this.loadToken();
        this.requestQueue = [];
        this.isProcessing = false;
    }

    /**
     * Sauvegarde le token dans le sessionStorage
     */
    saveToken(token) {
        sessionStorage.setItem('access_token', token);
        this.accessToken = token;
        debugLog('Token sauvegardé');
    }

    /**
     * Charge le token depuis le sessionStorage
     */
    loadToken() {
        return sessionStorage.getItem('access_token');
    }

    /**
     * Supprime le token
     */
    clearToken() {
        sessionStorage.removeItem('access_token');
        this.accessToken = null;
        debugLog('Token supprimé');
    }

    /**
     * Vérifie si l'utilisateur est authentifié
     */
    isAuthenticated() {
        return !!this.accessToken;
    }

    /**
     * Effectue une requête HTTP
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const defaultHeaders = {
            'Content-Type': 'application/json',
        };

        // Ajouter le token d'authentification si disponible
        if (this.accessToken) {
            defaultHeaders['Authorization'] = `Bearer ${this.accessToken}`;
        }

        const config = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
        };

        debugLog(`Request: ${options.method || 'GET'} ${url}`);

        try {
            const response = await fetch(url, config);
            
            // Vérifier le statut de la réponse
            if (response.status === 401) {
                // Token expiré ou invalide
                this.clearToken();
                throw new Error('Session expirée. Veuillez vous reconnecter.');
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || errorData.error || `Erreur HTTP ${response.status}`);
            }

            const data = await response.json();
            debugLog('Response:', data);
            return data;

        } catch (error) {
            errorLog('Request error:', error);
            throw error;
        }
    }

    /**
     * GET request
     */
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    /**
     * POST request
     */
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    /**
     * DELETE request
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // ========================================================================
    // ENDPOINTS D'AUTHENTIFICATION
    // ========================================================================

    /**
     * Connexion directe (sans CAS)
     */
    async loginDirect(pronoteUrl, username, password, accountType = 3) {
        const response = await this.post('/api/auth/login/direct', {
            pronote_url: pronoteUrl,
            username: username,
            password: password,
            account_type: accountType
        });

        if (response.success && response.access_token) {
            this.saveToken(response.access_token);
        }

        return response;
    }

    /**
     * Connexion CAS (ENT)
     */
    async loginCAS(pronoteUrl, username, password, entName) {
        const response = await this.post('/api/auth/login/cas', {
            pronote_url: pronoteUrl,
            username: username,
            password: password,
            ent_name: entName
        });

        if (response.success && response.access_token) {
            this.saveToken(response.access_token);
        }

        return response;
    }

    /**
     * Déconnexion
     */
    async logout() {
        try {
            await this.post('/api/auth/logout');
        } finally {
            this.clearToken();
        }
    }

    // ========================================================================
    // ENDPOINTS PRONOTE
    // ========================================================================

    /**
     * Récupère les devoirs
     */
    async getHomework(dateFrom = null, dateTo = null) {
        return this.post('/api/pronote/homework', {
            date_from: dateFrom,
            date_to: dateTo
        });
    }

    /**
     * Récupère l'emploi du temps
     */
    async getTimetable(dateFrom = null, dateTo = null) {
        return this.post('/api/pronote/timetable', {
            date_from: dateFrom,
            date_to: dateTo
        });
    }

    /**
     * Récupère les notes
     */
    async getGrades(periodName = null) {
        const params = periodName ? `?period_name=${encodeURIComponent(periodName)}` : '';
        return this.post(`/api/pronote/grades${params}`);
    }

    // ========================================================================
    // ENDPOINTS IA
    // ========================================================================

    /**
     * Envoie un message au chat IA
     */
    async sendChatMessage(message, context = null) {
        return this.post('/api/ai/chat', {
            message: message,
            context: context,
            model: CONFIG.AI_CONFIG.model
        });
    }

    // ========================================================================
    // UTILITAIRES
    // ========================================================================

    /**
     * Récupère la liste des ENTs supportés
     */
    async getENTs() {
        return this.get('/api/ents');
    }

    /**
     * Health check
     */
    async healthCheck() {
        return this.get('/api/health');
    }
}

// Instance globale
window.apiClient = new APIClient();
