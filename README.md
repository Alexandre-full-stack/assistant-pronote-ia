# Assistant Pronote IA

Application web complète permettant d'accéder à Pronote avec support CAS (ENT régionaux) et intégration d'un assistant IA conversationnel.

## Avertissement Important

**Cette application est un projet éducatif non officiel**

- Non affiliée à Index-Education (Pronote)
- Utilise des bibliothèques tierces (pronotepy)
- Usage personnel et éducatif uniquement
- Respect des CGU de Pronote requis

## Architecture

### Backend (Python FastAPI)
- Authentification Pronote (directe + CAS via pronotepy)
- API RESTful sécurisée avec JWT
- Sessions chiffrées avec Redis
- Rate limiting et protection CORS
- Support de 27+ ENTs régionaux français

### Frontend (HTML/CSS/JavaScript)
- Interface responsive moderne
- Chat IA avec OpenRouter (DeepSeek R1)
- Visualisation des devoirs, emploi du temps et notes
- Déployable sur GitHub Pages

## Prérequis

### Backend
- Python 3.11+
- Redis 7+
- Chrome/Chromium (pour CAS complexe via Selenium)

### Frontend
- Navigateur moderne (Chrome, Firefox, Safari, Edge)
- GitHub Pages ou serveur web statique

### Clés API
- Clé OpenRouter (gratuite avec DeepSeek R1)

## Installation Locale

### 1. Backend

```bash
cd backend

# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer dépendances
pip install -r requirements.txt

# Configurer variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs

# Lancer Redis
redis-server

# Démarrer le serveur
python server.py
```

Le backend sera accessible sur `http://localhost:8000`

### 2. Frontend

```bash
cd frontend

# Serveur de développement simple
python -m http.server 3000

# Ou avec Node.js
npx http-server -p 3000
```

Le frontend sera accessible sur `http://localhost:3000`

### 3. Configuration

Dans `frontend/js/config.js`, modifier :
```javascript
API_BASE_URL: 'http://localhost:8000'
```

## Déploiement Production

### Backend sur Railway

1. Créer compte sur [railway.app](https://railway.app)
2. Nouveau projet → Deploy from GitHub repo
3. Sélectionner le dossier `backend`
4. Ajouter Redis dans les services
5. Configurer les variables d'environnement :
   - `SECRET_KEY` (générer avec `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
   - `JWT_SECRET_KEY` (idem)
   - `ENCRYPTION_KEY` (idem)
   - `OPENROUTER_API_KEY` (votre clé)
   - `ALLOWED_ORIGINS` (URL GitHub Pages)
   - `REDIS_URL` (fournie automatiquement)

6. Railway génère une URL : `https://votre-app.railway.app`

### Frontend sur GitHub Pages

1. Créer repo GitHub : `assistant-pronote-ia`
2. Pousser le contenu du dossier `frontend`
3. Settings → Pages → Deploy from branch `main` / `/(root)`
4. Modifier `frontend/js/config.js` :
   ```javascript
   API_BASE_URL: 'https://votre-app.railway.app'
   ```
5. Site accessible sur `https://votre-username.github.io/assistant-pronote-ia`

## Configuration des ENTs

L'application supporte 27+ ENTs régionaux :

- **Île-de-France** : monlycee.net, Paris Classe Numérique, ENT77, ENT94
- **Grand Est** : Mon Bureau Numérique
- **Nouvelle-Aquitaine** : Lycée Connecté
- **Occitanie** : Néo
- **Bretagne** : Toutatice
- **Normandie** : L'Educ de Normandie
- **Hauts-de-France** : ENT HDF
- Et bien d'autres...

Liste complète disponible via l'endpoint `/api/ents`

## Utilisation

### 1. Connexion

**Authentification directe** :
- URL Pronote : `https://XXXXXXX.index-education.net/pronote/eleve.html`
- Identifiant et mot de passe Pronote

**Authentification CAS** :
- URL Pronote
- Sélectionner votre ENT/région
- Identifiant et mot de passe ENT

### 2. Navigation

- **Assistant IA** : Posez des questions sur vos devoirs, emploi du temps, notes
- **Devoirs** : Liste complète des devoirs à venir
- **Emploi du temps** : Visualisation de la semaine
- **Notes** : Consultation des notes et moyenne

### 3. Exemples de questions IA

- "Quels sont mes devoirs pour demain ?"
- "Mon emploi du temps de cette semaine"
- "Quelle est ma moyenne en mathématiques ?"
- "Résumé de ma semaine"

## Sécurité

### Chiffrement

- Credentials chiffrés avec AES-256-GCM côté backend
- Sessions stockées dans Redis avec expiration
- JWT pour authentification stateless
- HTTPS obligatoire en production

### Bonnes Pratiques

1. **Ne JAMAIS** committer de credentials dans Git
2. Utiliser des clés API avec restrictions
3. Activer HTTPS sur le backend
4. Limiter les CORS aux origines autorisées
5. Surveiller les logs d'accès

## Docker

### Développement

```bash
docker-compose up -d
```

Services disponibles :
- Backend : `http://localhost:8000`
- Frontend : `http://localhost:3000`
- Redis : `localhost:6379`
- Redis Commander (debug) : `http://localhost:8081`

### Production

```bash
docker build -t assistant-pronote-backend ./backend
docker run -p 8000:8000 --env-file .env assistant-pronote-backend
```

## API Documentation

Documentation Swagger disponible sur `http://localhost:8000/docs` en mode développement.

### Principaux Endpoints

#### Authentification
- `POST /api/auth/login/direct` - Connexion directe
- `POST /api/auth/login/cas` - Connexion CAS
- `POST /api/auth/logout` - Déconnexion

#### Pronote
- `POST /api/pronote/homework` - Récupérer devoirs
- `POST /api/pronote/timetable` - Récupérer emploi du temps
- `POST /api/pronote/grades` - Récupérer notes

#### IA
- `POST /api/ai/chat` - Chat avec l'assistant IA

## Développement

### Structure du Projet

```
assistant-pronote-ia/
├── backend/
│   ├── server.py           # Serveur FastAPI principal
│   ├── config.py           # Configuration
│   ├── auth.py             # Authentification et sessions
│   ├── pronote_client.py   # Client Pronote avec CAS
│   ├── requirements.txt    # Dépendances Python
│   ├── Dockerfile          # Image Docker
│   └── .env.example        # Variables d'environnement
├── frontend/
│   ├── index.html          # Page principale
│   ├── css/
│   │   ├── main.css        # Styles de base
│   │   ├── components.css  # Composants (chat, listes)
│   │   └── responsive.css  # Mobile/tablette
│   └── js/
│       ├── config.js       # Configuration frontend
│       ├── api-client.js   # Client API
│       ├── auth.js         # Gestion authentification
│       ├── chat.js         # Gestionnaire chat IA
│       ├── pronote-data.js # Gestion données Pronote
│       └── app.js          # Initialisation application
├── docker-compose.yml      # Orchestration Docker
├── railway.toml            # Configuration Railway
└── README.md               # Cette documentation
```

### Tests

```bash
# Backend
cd backend
pytest

# Frontend
# Ouvrir dans un navigateur et tester manuellement
```

## Dépannage

### Backend inaccessible

- Vérifier que Redis est démarré : `redis-cli ping`
- Vérifier les logs : `docker-compose logs backend`
- Tester la connexion : `curl http://localhost:8000/api/health`

### Erreur CORS

- Vérifier `ALLOWED_ORIGINS` dans `.env`
- S'assurer que l'URL frontend est correcte
- Vérifier les logs backend pour voir les requêtes rejetées

### Authentification CAS échoue

- Vérifier que l'ENT est supporté : `curl http://localhost:8000/api/ents`
- Tester les identifiants directement sur le site de l'ENT
- Consulter les logs pour voir l'erreur exacte

### Chat IA ne répond pas

- Vérifier la clé `OPENROUTER_API_KEY`
- Tester avec curl :
  ```bash
  curl https://openrouter.ai/api/v1/models \
    -H "Authorization: Bearer VOTRE_CLE"
  ```

## Limitations Connues

1. **pronotepy ne supporte pas tous les ENTs** : Certains ENTs régionaux peuvent ne pas fonctionner
2. **Pas de notifications push** : Pas de notifications en temps réel
3. **Pas de modification de données** : Lecture seule (pas de marquage de devoirs comme faits)
4. **Sessions Pronote** : pronotepy nécessite une réauthentification fréquente

## Ressources

- [pronotepy Documentation](https://github.com/bain3/pronotepy)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [Railway Documentation](https://docs.railway.app/)

## Licence

Projet éducatif - Voir conditions d'utilisation des bibliothèques tierces :
- pronotepy : MIT License
- FastAPI : MIT License

## Support

Pour toute question ou problème :
1. Consulter cette documentation
2. Vérifier les logs d'erreur
3. Tester la connexion au backend et à Pronote

## Contribuer

Ce projet est fourni à des fins éducatives. Contributions bienvenues via pull requests.

---

**Note** : Respectez les CGU de Pronote et d'Index-Education. Utilisez cette application de manière responsable et uniquement pour accéder à vos propres données.
