/**
 * Fichier principal de l'application
 * Initialise tous les composants et gère la navigation
 */

class App {
    constructor() {
        this.initialized = false;
        this.currentTab = 'chat';
    }

    /**
     * Initialise l'application
     */
    async init() {
        if (this.initialized) return;

        debugLog('Initialisation de l\'application...');

        // Gérer le disclaimer
        this.setupDisclaimer();

        // Vérifier la connexion backend
        await this.checkBackendConnection();

        // Initialiser la navigation des onglets
        this.setupTabNavigation();

        // Vérifier si l'utilisateur est déjà connecté
        if (apiClient.isAuthenticated()) {
            // Tenter de restaurer la session
            await this.attemptSessionRestore();
        }

        this.initialized = true;
        debugLog('Application initialisée');
    }

    /**
     * Gère l'affichage du disclaimer
     */
    setupDisclaimer() {
        const disclaimer = document.getElementById('legal-disclaimer');
        const acceptBtn = document.getElementById('accept-disclaimer');
        const appContainer = document.getElementById('app-container');

        if (acceptBtn && disclaimer && appContainer) {
            acceptBtn.addEventListener('click', () => {
                disclaimer.style.display = 'none';
                appContainer.style.display = 'block';
                sessionStorage.setItem('disclaimer_accepted', 'true');
            });

            // Vérifier si déjà accepté
            if (sessionStorage.getItem('disclaimer_accepted') === 'true') {
                disclaimer.style.display = 'none';
                appContainer.style.display = 'block';
            }
        }
    }

    /**
     * Vérifie la connexion au backend
     */
    async checkBackendConnection() {
        try {
            await apiClient.healthCheck();
            debugLog('Backend accessible');
        } catch (error) {
            errorLog('Backend inaccessible:', error);
            this.showBackendError();
        }
    }

    /**
     * Affiche une erreur si le backend est inaccessible
     */
    showBackendError() {
        const loginScreen = document.getElementById('login-screen');
        if (!loginScreen) return;

        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message show';
        errorDiv.style.marginBottom = '20px';
        errorDiv.innerHTML = `
            <strong>Erreur de connexion au serveur</strong><br>
            Le backend n'est pas accessible. Vérifiez que le serveur est démarré.<br>
            URL configurée: <code>${CONFIG.API_BASE_URL}</code>
        `;

        const card = loginScreen.querySelector('.card');
        if (card) {
            card.insertBefore(errorDiv, card.firstChild);
        }
    }

    /**
     * Tente de restaurer une session existante
     */
    async attemptSessionRestore() {
        try {
            // Tenter de récupérer les données pour vérifier la session
            await apiClient.healthCheck();
            
            // Si on arrive ici, la session est valide
            // Mais on n'a pas les infos utilisateur stockées côté client
            // Donc on laisse l'utilisateur se reconnecter
            debugLog('Session token trouvé mais infos utilisateur manquantes');
            apiClient.clearToken();
            
        } catch (error) {
            // Session invalide, nettoyer
            apiClient.clearToken();
        }
    }

    /**
     * Configure la navigation entre les onglets
     */
    setupTabNavigation() {
        const navButtons = document.querySelectorAll('.nav-btn');
        
        navButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const tabName = btn.dataset.tab;
                this.switchTab(tabName);
            });
        });
    }

    /**
     * Change d'onglet
     */
    switchTab(tabName) {
        // Mettre à jour les boutons de navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Mettre à jour les contenus
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `tab-${tabName}`);
        });

        this.currentTab = tabName;
        debugLog(`Onglet actif: ${tabName}`);

        // Charger les données si nécessaire
        this.loadTabData(tabName);
    }

    /**
     * Charge les données d'un onglet si nécessaire
     */
    async loadTabData(tabName) {
        if (!pronoteDataManager) return;

        const data = pronoteDataManager.getAllData();

        switch (tabName) {
            case 'homework':
                if (data.homework.length === 0) {
                    await pronoteDataManager.loadHomework();
                }
                break;
            case 'timetable':
                if (data.timetable.length === 0) {
                    await pronoteDataManager.loadTimetable();
                }
                break;
            case 'grades':
                if (data.grades.length === 0) {
                    await pronoteDataManager.loadGrades();
                }
                break;
        }
    }

    /**
     * Gère les erreurs globales
     */
    setupGlobalErrorHandling() {
        window.addEventListener('error', (event) => {
            errorLog('Erreur globale:', event.error);
        });

        window.addEventListener('unhandledrejection', (event) => {
            errorLog('Promise non gérée:', event.reason);
        });
    }

    /**
     * Configure le rafraîchissement automatique
     */
    setupAutoRefresh() {
        if (!CONFIG.AUTO_REFRESH_INTERVAL) return;

        setInterval(() => {
            if (authManager.isAuthenticated() && document.visibilityState === 'visible') {
                debugLog('Rafraîchissement automatique...');
                
                // Rafraîchir l'onglet actif
                switch (this.currentTab) {
                    case 'homework':
                        pronoteDataManager.loadHomework();
                        break;
                    case 'timetable':
                        pronoteDataManager.loadTimetable();
                        break;
                    case 'grades':
                        pronoteDataManager.loadGrades();
                        break;
                }
            }
        }, CONFIG.AUTO_REFRESH_INTERVAL);
    }

    /**
     * Gère la visibilité de la page (optimisation)
     */
    setupVisibilityHandling() {
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && authManager.isAuthenticated()) {
                debugLog('Page visible, vérification des données...');
                // Rafraîchir les données si la page était cachée longtemps
                const lastRefresh = sessionStorage.getItem('last_refresh');
                const now = Date.now();
                
                if (!lastRefresh || now - parseInt(lastRefresh) > 5 * 60 * 1000) {
                    this.loadTabData(this.currentTab);
                    sessionStorage.setItem('last_refresh', now.toString());
                }
            }
        });
    }
}

// ============================================================================
// INITIALISATION AU CHARGEMENT DE LA PAGE
// ============================================================================

// Attendre que le DOM soit chargé
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

function initApp() {
    debugLog('DOM chargé, initialisation...');
    
    // Créer et initialiser l'application
    const app = new App();
    app.init();
    app.setupGlobalErrorHandling();
    app.setupAutoRefresh();
    app.setupVisibilityHandling();
    
    // Exposer globalement pour debug
    window.app = app;
}

// ============================================================================
// UTILITAIRES GLOBAUX
// ============================================================================

/**
 * Formate une date en français
 */
function formatDate(dateString, options = {}) {
    const date = new Date(dateString);
    const defaultOptions = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        ...options
    };
    return date.toLocaleDateString('fr-FR', defaultOptions);
}

/**
 * Formate une heure en français
 */
function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Calcule le nombre de jours entre deux dates
 */
function daysBetween(date1, date2) {
    const oneDay = 24 * 60 * 60 * 1000;
    const d1 = new Date(date1);
    const d2 = new Date(date2);
    return Math.round(Math.abs((d1 - d2) / oneDay));
}

/**
 * Vérifie si une date est aujourd'hui
 */
function isToday(dateString) {
    const date = new Date(dateString);
    const today = new Date();
    return date.toDateString() === today.toDateString();
}

/**
 * Vérifie si une date est demain
 */
function isTomorrow(dateString) {
    const date = new Date(dateString);
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return date.toDateString() === tomorrow.toDateString();
}

// Exposer les utilitaires globalement
window.formatDate = formatDate;
window.formatTime = formatTime;
window.daysBetween = daysBetween;
window.isToday = isToday;
window.isTomorrow = isTomorrow;
