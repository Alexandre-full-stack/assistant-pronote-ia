/**
 * Gestion de l'authentification côté frontend
 * Gère les formulaires de connexion et la session utilisateur
 */

class AuthManager {
    constructor() {
        this.currentUser = null;
        this.initEventListeners();
        this.loadENTs();
    }

    /**
     * Initialise les event listeners pour les formulaires
     */
    initEventListeners() {
        // Boutons de sélection du type d'authentification
        document.querySelectorAll('.auth-type-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchAuthType(e.target.dataset.auth));
        });

        // Formulaire connexion directe
        const directForm = document.getElementById('login-form-direct');
        if (directForm) {
            directForm.addEventListener('submit', (e) => this.handleDirectLogin(e));
        }

        // Formulaire connexion CAS
        const casForm = document.getElementById('login-form-cas');
        if (casForm) {
            casForm.addEventListener('submit', (e) => this.handleCASLogin(e));
        }

        // Bouton déconnexion
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }
    }

    /**
     * Change le type d'authentification (direct/CAS)
     */
    switchAuthType(type) {
        // Mettre à jour les boutons
        document.querySelectorAll('.auth-type-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.auth === type);
        });

        // Afficher le bon formulaire
        document.getElementById('login-form-direct').classList.toggle('active', type === 'direct');
        document.getElementById('login-form-cas').classList.toggle('active', type === 'cas');

        // Effacer les erreurs
        this.clearError();
    }

    /**
     * Charge la liste des ENTs depuis l'API
     */
    async loadENTs() {
        try {
            const response = await apiClient.getENTs();
            const selector = document.getElementById('ent-selector');
            
            if (selector && response.ents) {
                response.ents.forEach(ent => {
                    const option = document.createElement('option');
                    option.value = ent.id;
                    option.textContent = ent.name;
                    selector.appendChild(option);
                });
            }
        } catch (error) {
            errorLog('Erreur chargement ENTs:', error);
        }
    }

    /**
     * Gère la connexion directe
     */
    async handleDirectLogin(event) {
        event.preventDefault();
        
        const pronoteUrl = document.getElementById('pronote-url-direct').value.trim();
        const username = document.getElementById('username-direct').value.trim();
        const password = document.getElementById('password-direct').value;
        const accountType = parseInt(document.getElementById('account-type').value);

        if (!pronoteUrl || !username || !password) {
            this.showError('Veuillez remplir tous les champs');
            return;
        }

        this.setLoading(true, 'Connexion en cours...');

        try {
            const response = await apiClient.loginDirect(
                pronoteUrl,
                username,
                password,
                accountType
            );

            if (response.success) {
                this.currentUser = response.student;
                this.onLoginSuccess();
            } else {
                this.showError('Échec de l\'authentification');
            }
        } catch (error) {
            this.showError(error.message || 'Erreur de connexion');
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Gère la connexion CAS
     */
    async handleCASLogin(event) {
        event.preventDefault();
        
        const pronoteUrl = document.getElementById('pronote-url-cas').value.trim();
        const username = document.getElementById('username-cas').value.trim();
        const password = document.getElementById('password-cas').value;
        const entName = document.getElementById('ent-selector').value;

        if (!pronoteUrl || !username || !password || !entName) {
            this.showError('Veuillez remplir tous les champs');
            return;
        }

        this.setLoading(true, 'Authentification CAS en cours...');

        try {
            const response = await apiClient.loginCAS(
                pronoteUrl,
                username,
                password,
                entName
            );

            if (response.success) {
                this.currentUser = response.student;
                this.onLoginSuccess();
            } else {
                this.showError('Échec de l\'authentification CAS');
            }
        } catch (error) {
            this.showError(error.message || 'Erreur d\'authentification CAS');
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Gère la déconnexion
     */
    async handleLogout() {
        try {
            this.setLoading(true, 'Déconnexion...');
            await apiClient.logout();
        } catch (error) {
            errorLog('Erreur déconnexion:', error);
        } finally {
            this.onLogoutSuccess();
            this.setLoading(false);
        }
    }

    /**
     * Callback appelé après une connexion réussie
     */
    onLoginSuccess() {
        debugLog('Connexion réussie:', this.currentUser);
        
        // Afficher les infos utilisateur
        document.getElementById('student-name').textContent = this.currentUser.student_name;
        document.getElementById('student-class').textContent = this.currentUser.class_name || 'Classe non disponible';

        // Passer à l'écran dashboard
        document.getElementById('login-screen').classList.remove('active');
        document.getElementById('dashboard-screen').classList.add('active');

        // Charger les données initiales
        if (window.pronoteDataManager) {
            window.pronoteDataManager.loadAllData();
        }

        // Initialiser le chat
        if (window.chatManager) {
            window.chatManager.addWelcomeMessage();
        }
    }

    /**
     * Callback appelé après une déconnexion
     */
    onLogoutSuccess() {
        debugLog('Déconnexion réussie');
        
        this.currentUser = null;

        // Retour à l'écran de connexion
        document.getElementById('dashboard-screen').classList.remove('active');
        document.getElementById('login-screen').classList.add('active');

        // Réinitialiser les formulaires
        document.getElementById('login-form-direct').reset();
        document.getElementById('login-form-cas').reset();

        // Vider le chat et les données
        if (window.chatManager) {
            window.chatManager.clearMessages();
        }
        
        if (window.pronoteDataManager) {
            window.pronoteDataManager.clearAllData();
        }
    }

    /**
     * Affiche un message d'erreur
     */
    showError(message) {
        const errorDiv = document.getElementById('login-error');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.classList.add('show');
            
            setTimeout(() => {
                errorDiv.classList.remove('show');
            }, 5000);
        }
    }

    /**
     * Efface les messages d'erreur
     */
    clearError() {
        const errorDiv = document.getElementById('login-error');
        if (errorDiv) {
            errorDiv.classList.remove('show');
            errorDiv.textContent = '';
        }
    }

    /**
     * Active/désactive le mode loading
     */
    setLoading(isLoading, message = 'Chargement...') {
        const overlay = document.getElementById('loading-overlay');
        const loadingText = document.getElementById('loading-text');
        
        if (overlay) {
            if (isLoading) {
                overlay.classList.add('show');
                if (loadingText) loadingText.textContent = message;
            } else {
                overlay.classList.remove('show');
            }
        }

        // Désactiver les boutons pendant le chargement
        document.querySelectorAll('button[type="submit"]').forEach(btn => {
            btn.disabled = isLoading;
        });
    }

    /**
     * Vérifie si l'utilisateur est connecté
     */
    isAuthenticated() {
        return apiClient.isAuthenticated() && this.currentUser !== null;
    }

    /**
     * Récupère l'utilisateur actuel
     */
    getCurrentUser() {
        return this.currentUser;
    }
}

// Instance globale
window.authManager = new AuthManager();
