/**
 * Gestionnaire des données Pronote
 * Charge et affiche les devoirs, l'emploi du temps et les notes
 */

class PronoteDataManager {
    constructor() {
        this.data = {
            homework: [],
            timetable: [],
            grades: []
        };
        this.initEventListeners();
    }

    /**
     * Initialise les event listeners
     */
    initEventListeners() {
        // Boutons de rafraîchissement
        document.getElementById('refresh-homework')?.addEventListener('click', () => this.loadHomework());
        document.getElementById('refresh-timetable')?.addEventListener('click', () => this.loadTimetable());
        document.getElementById('refresh-grades')?.addEventListener('click', () => this.loadGrades());
    }

    /**
     * Charge toutes les données
     */
    async loadAllData() {
        await Promise.all([
            this.loadHomework(),
            this.loadTimetable(),
            this.loadGrades()
        ]);
    }

    /**
     * Charge les devoirs
     */
    async loadHomework() {
        const container = document.getElementById('homework-list');
        if (!container) return;

        this.showLoading(container);

        try {
            // Dates: aujourd'hui à +14 jours
            const dateFrom = new Date().toISOString();
            const dateTo = new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString();

            const response = await apiClient.getHomework(dateFrom, dateTo);

            if (response.success && response.homework) {
                this.data.homework = response.homework;
                this.displayHomework(response.homework);
            } else {
                this.showEmpty(container, 'Aucun devoir à venir');
            }
        } catch (error) {
            errorLog('Erreur chargement devoirs:', error);
            this.showError(container, 'Erreur lors du chargement des devoirs');
        }
    }

    /**
     * Charge l'emploi du temps
     */
    async loadTimetable() {
        const container = document.getElementById('timetable-list');
        if (!container) return;

        this.showLoading(container);

        try {
            // Dates: lundi de cette semaine à dimanche
            const today = new Date();
            const monday = new Date(today);
            monday.setDate(today.getDate() - today.getDay() + 1);
            const sunday = new Date(monday);
            sunday.setDate(monday.getDate() + 6);

            const response = await apiClient.getTimetable(
                monday.toISOString(),
                sunday.toISOString()
            );

            if (response.success && response.timetable) {
                this.data.timetable = response.timetable;
                this.displayTimetable(response.timetable);
            } else {
                this.showEmpty(container, 'Aucun cours cette semaine');
            }
        } catch (error) {
            errorLog('Erreur chargement emploi du temps:', error);
            this.showError(container, 'Erreur lors du chargement de l\'emploi du temps');
        }
    }

    /**
     * Charge les notes
     */
    async loadGrades() {
        const container = document.getElementById('grades-list');
        if (!container) return;

        this.showLoading(container);

        try {
            const response = await apiClient.getGrades();

            if (response.success && response.grades) {
                this.data.grades = response.grades;
                this.displayGrades(response.grades);
            } else {
                this.showEmpty(container, 'Aucune note disponible');
            }
        } catch (error) {
            errorLog('Erreur chargement notes:', error);
            this.showError(container, 'Erreur lors du chargement des notes');
        }
    }

    /**
     * Affiche les devoirs
     */
    displayHomework(homework) {
        const container = document.getElementById('homework-list');
        if (!container) return;

        if (homework.length === 0) {
            this.showEmpty(container, 'Aucun devoir à venir');
            return;
        }

        container.innerHTML = '';

        homework.forEach(hw => {
            const item = document.createElement('div');
            item.className = 'data-item';

            const date = new Date(hw.date);
            const dateStr = date.toLocaleDateString('fr-FR', {
                weekday: 'long',
                day: 'numeric',
                month: 'long'
            });

            item.innerHTML = `
                <div class="data-item-header">
                    <div class="data-item-title">${this.escapeHtml(hw.subject)}</div>
                    <span class="data-item-badge ${hw.done ? 'badge-done' : 'badge-todo'}">
                        ${hw.done ? 'Fait' : 'À faire'}
                    </span>
                </div>
                <div class="data-item-description">
                    ${this.escapeHtml(hw.description)}
                </div>
                <div class="data-item-meta">
                    <span>📅 Pour le ${dateStr}</span>
                </div>
                ${hw.files && hw.files.length > 0 ? `
                    <div class="data-item-files">
                        ${hw.files.map(file => `
                            <a href="${file.url}" class="file-link" target="_blank" rel="noopener">
                                📎 ${this.escapeHtml(file.name)}
                            </a>
                        `).join('')}
                    </div>
                ` : ''}
            `;

            container.appendChild(item);
        });
    }

    /**
     * Affiche l'emploi du temps
     */
    displayTimetable(timetable) {
        const container = document.getElementById('timetable-list');
        if (!container) return;

        if (timetable.length === 0) {
            this.showEmpty(container, 'Aucun cours cette semaine');
            return;
        }

        container.innerHTML = '';

        // Grouper par jour
        const byDay = {};
        timetable.forEach(lesson => {
            const date = new Date(lesson.start);
            const dayKey = date.toLocaleDateString('fr-FR', {
                weekday: 'long',
                day: 'numeric',
                month: 'long'
            });

            if (!byDay[dayKey]) byDay[dayKey] = [];
            byDay[dayKey].push(lesson);
        });

        // Afficher par jour
        Object.entries(byDay).forEach(([day, lessons]) => {
            const dayGroup = document.createElement('div');
            dayGroup.className = 'timetable-day-group';

            const dayHeader = document.createElement('div');
            dayHeader.className = 'timetable-day-header';
            dayHeader.textContent = day;
            dayGroup.appendChild(dayHeader);

            lessons.sort((a, b) => new Date(a.start) - new Date(b.start));

            lessons.forEach(lesson => {
                const start = new Date(lesson.start);
                const end = new Date(lesson.end);

                const item = document.createElement('div');
                item.className = `timetable-item ${lesson.canceled ? 'canceled' : ''}`;

                item.innerHTML = `
                    <div class="timetable-time">
                        <div class="timetable-time-start">
                            ${start.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                        </div>
                        <div class="timetable-time-end">
                            ${end.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                        </div>
                    </div>
                    <div class="timetable-details">
                        <div class="timetable-subject">${this.escapeHtml(lesson.subject)}</div>
                        ${lesson.teacher ? `<div class="timetable-teacher">${this.escapeHtml(lesson.teacher)}</div>` : ''}
                    </div>
                    ${lesson.classroom ? `<div class="timetable-room">${this.escapeHtml(lesson.classroom)}</div>` : ''}
                `;

                dayGroup.appendChild(item);
            });

            container.appendChild(dayGroup);
        });
    }

    /**
     * Affiche les notes
     */
    displayGrades(grades) {
        const container = document.getElementById('grades-list');
        if (!container) return;

        if (grades.length === 0) {
            this.showEmpty(container, 'Aucune note disponible');
            return;
        }

        container.innerHTML = '';

        // Calculer la moyenne générale
        const validGrades = grades.filter(g => g.grade && g.out_of);
        if (validGrades.length > 0) {
            const average = validGrades.reduce((sum, g) => {
                return sum + (parseFloat(g.grade) / parseFloat(g.out_of)) * 20;
            }, 0) / validGrades.length;

            const summary = document.createElement('div');
            summary.className = 'grades-summary';
            summary.innerHTML = `
                <div class="grades-summary-item">
                    <h4>Moyenne générale</h4>
                    <div class="value">${average.toFixed(2)}/20</div>
                </div>
                <div class="grades-summary-item">
                    <h4>Nombre de notes</h4>
                    <div class="value">${validGrades.length}</div>
                </div>
            `;
            container.appendChild(summary);
        }

        // Afficher les notes
        grades.forEach(grade => {
            if (!grade.grade) return;

            const item = document.createElement('div');
            item.className = 'data-item grade-item';

            const date = grade.date ? new Date(grade.date).toLocaleDateString('fr-FR') : 'Date inconnue';

            item.innerHTML = `
                <div class="grade-info">
                    <h4>${this.escapeHtml(grade.subject)}</h4>
                    <div class="grade-meta">
                        📅 ${date} • Coefficient: ${grade.coefficient || 1}
                    </div>
                </div>
                <div class="grade-value">
                    <div class="grade-number">${grade.grade}</div>
                    <div class="grade-out-of">/${grade.out_of || 20}</div>
                </div>
                ${grade.comment ? `
                    <div class="grade-comment">
                        ${this.escapeHtml(grade.comment)}
                    </div>
                ` : ''}
            `;

            container.appendChild(item);
        });
    }

    /**
     * Affiche un état de chargement
     */
    showLoading(container) {
        container.innerHTML = '<div class="loading">Chargement...</div>';
    }

    /**
     * Affiche un état vide
     */
    showEmpty(container, message) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <h3>Rien à afficher</h3>
                <p>${message}</p>
            </div>
        `;
    }

    /**
     * Affiche une erreur
     */
    showError(container, message) {
        container.innerHTML = `
            <div class="error-message show">
                ${message}
            </div>
        `;
    }

    /**
     * Échappe le HTML pour éviter les injections XSS
     */
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }

    /**
     * Efface toutes les données
     */
    clearAllData() {
        this.data = {
            homework: [],
            timetable: [],
            grades: []
        };

        ['homework-list', 'timetable-list', 'grades-list'].forEach(id => {
            const container = document.getElementById(id);
            if (container) {
                this.showEmpty(container, 'Connectez-vous pour voir vos données');
            }
        });
    }

    /**
     * Récupère toutes les données
     */
    getAllData() {
        return this.data;
    }
}

// Instance globale
window.pronoteDataManager = new PronoteDataManager();
