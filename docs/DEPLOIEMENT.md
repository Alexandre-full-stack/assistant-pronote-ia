# Guide de Déploiement Détaillé

Ce guide vous accompagne pas à pas pour déployer l'Assistant Pronote IA en production.

## Prérequis

- Compte GitHub
- Compte Railway.app (gratuit)
- Compte OpenRouter (gratuit avec DeepSeek R1)
- Git installé
- Python 3.11+ pour tester localement (optionnel)

## Étape 1 : Obtenir une clé OpenRouter

1. Aller sur https://openrouter.ai/
2. Créer un compte (gratuit)
3. Aller dans Settings → Keys
4. Créer une nouvelle clé API
5. **Sauvegarder la clé** (elle ne sera affichée qu'une fois)
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

Les modèles gratuits disponibles :
- `deepseek/deepseek-r1:free` (recommandé)
- `google/gemma-2-9b-it:free`
MOI J'AI PRIS : `deepseek/deepseek-chat-v3.1:free`

## Étape 2 : Créer le projet sur GitHub

### 2.1 Créer le repository

```bash
# Créer un dossier local
mkdir assistant-pronote-ia
cd assistant-pronote-ia

# Initialiser Git
git init

# Copier tous les fichiers fournis dans ce dossier

# Premier commit
git add .
git commit -m "Initial commit: Assistant Pronote IA complet"

# Créer le repo sur GitHub (via interface web)
# Puis lier le repo local
git remote add origin https://github.com/VOTRE_USERNAME/assistant-pronote-ia.git
git branch -M main
git push -u origin main
```

### 2.2 Vérifier le contenu

Votre repo doit contenir :
```
assistant-pronote-ia/
├── backend/
├── frontend/
├── docker-compose.yml
├── railway.toml
├── .gitignore
└── README.md
```

## Étape 3 : Déployer le Backend sur Railway

### 3.1 Créer un compte Railway

1. Aller sur https://railway.app/
2. S'inscrire avec GitHub (recommandé)
3. Vérifier votre email

### 3.2 Créer un nouveau projet

1. Dashboard Railway → "New Project"
2. Sélectionner "Deploy from GitHub repo"
3. Autoriser Railway à accéder à vos repos
4. Sélectionner `assistant-pronote-ia`

### 3.3 Configurer le service Backend

Railway détectera automatiquement le Dockerfile.

1. Settings du service → Root Directory : `/backend`
2. Start Command : `python -m uvicorn server:app --host 0.0.0.0 --port $PORT`

### 3.4 Ajouter Redis

1. Dans votre projet → "+ New" → "Database" → "Redis"
2. Railway créera automatiquement la variable `REDIS_URL`

### 3.5 Configurer les variables d'environnement

Dans le service backend → Variables :

**Générer des clés secrètes** :
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Exécuter 3 fois pour générer 3 clés différentes.

**Variables à ajouter** :
```
PORT=8000
HOST=0.0.0.0
ENV=production
DEBUG=False

SECRET_KEY=[votre_cle_1]
JWT_SECRET_KEY=[votre_cle_2]
ENCRYPTION_KEY=[votre_cle_3]

OPENROUTER_API_KEY=[votre_cle_openrouter]

REDIS_URL=${{Redis.REDIS_URL}}  # Automatique si Redis ajouté

ALLOWED_ORIGINS=https://VOTRE_USERNAME.github.io

REDIS_PASSWORD=
SESSION_EXPIRATION_SECONDS=86400
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

SELENIUM_HEADLESS=True
SELENIUM_TIMEOUT_SECONDS=30

LOG_LEVEL=INFO
PRONOTE_DEFAULT_ACCOUNT_TYPE=3
PRONOTE_REQUEST_TIMEOUT=30
```

**Important** : Remplacez `VOTRE_USERNAME` par votre vrai username GitHub.

### 3.6 Déployer

1. Railway détectera automatiquement les changements
2. Le déploiement prendra 5-10 minutes
3. Votre backend sera accessible sur `https://votre-projet-xxxx.up.railway.app`

**Copier cette URL** pour l'étape suivante.

### 3.7 Tester le backend

```bash
# Tester le health check
curl https://votre-projet-xxxx.up.railway.app/api/health

# Devrait retourner:
# {"status":"healthy","redis":"ok","timestamp":"..."}
```

## Étape 4 : Déployer le Frontend sur GitHub Pages

### 4.1 Configurer l'URL du backend

Éditer `frontend/js/config.js` :

```javascript
const CONFIG = {
    API_BASE_URL: 'https://votre-projet-xxxx.up.railway.app',  // ← Modifier ici
    // ...
};
```

### 4.2 Commiter et pousser

```bash
git add frontend/js/config.js
git commit -m "Configure backend URL for production"
git push
```

### 4.3 Activer GitHub Pages

1. Aller sur votre repo GitHub
2. Settings → Pages (menu gauche)
3. Source : "Deploy from a branch"
4. Branch : `main`
5. Folder : `/(root)`
6. Save

### 4.4 Attendre le déploiement

1. Attendre 1-2 minutes
2. Une URL apparaîtra : `https://VOTRE_USERNAME.github.io/assistant-pronote-ia`
3. Tester l'accès

### 4.5 Mettre à jour les CORS du backend

1. Retour sur Railway
2. Variables du service backend
3. Modifier `ALLOWED_ORIGINS` :
   ```
   ALLOWED_ORIGINS=https://VOTRE_USERNAME.github.io
   ```
4. Le backend redémarrera automatiquement

## Étape 5 : Vérifications Finales

### 5.1 Tester la connexion

1. Ouvrir `https://VOTRE_USERNAME.github.io/assistant-pronote-ia`
2. Accepter le disclaimer
3. Tester l'authentification avec vos identifiants Pronote

### 5.2 Vérifier les logs

**Backend (Railway)** :
1. Dashboard Railway → Service backend
2. Onglet "Deployments" → Dernier déploiement
3. Cliquer sur "View Logs"
4. Vérifier qu'il n'y a pas d'erreurs

**Frontend (Browser)** :
1. Ouvrir les DevTools (F12)
2. Console : vérifier qu'il n'y a pas d'erreurs rouges
3. Network : vérifier que les requêtes API passent

### 5.3 Checklist de fonctionnement

- [ ] Disclaimer s'affiche et peut être accepté
- [ ] Formulaires de connexion sont visibles
- [ ] Liste des ENTs se charge dans le formulaire CAS
- [ ] Connexion directe fonctionne
- [ ] Dashboard s'affiche après connexion
- [ ] Devoirs se chargent
- [ ] Emploi du temps s'affiche
- [ ] Notes s'affichent
- [ ] Chat IA répond aux questions
- [ ] Déconnexion fonctionne

## Dépannage

### Erreur "Backend inaccessible"

**Symptôme** : Message rouge dans l'écran de connexion

**Solutions** :
1. Vérifier que le backend est déployé (Railway → Service backend → Status : "Active")
2. Tester l'URL directement : `https://votre-backend.railway.app/api/health`
3. Vérifier les logs Railway pour voir les erreurs
4. S'assurer que `API_BASE_URL` dans `config.js` est correct

### Erreur CORS

**Symptôme** : Erreur dans la console "has been blocked by CORS policy"

**Solutions** :
1. Vérifier `ALLOWED_ORIGINS` dans Railway
2. S'assurer que l'URL GitHub Pages est exacte (avec ou sans `/` final)
3. Vérifier que le backend a redémarré après modification
4. Vider le cache du navigateur (Ctrl+Shift+R)

### Authentification échoue

**Symptôme** : "Échec d'authentification" après avoir soumis le formulaire

**Solutions CAS** :
1. Vérifier que votre ENT est dans la liste supportée : `/api/ents`
2. Tester vos identifiants directement sur le site de l'ENT
3. Consulter les logs Railway pour voir l'erreur exacte
4. Certains ENTs peuvent ne pas fonctionner avec pronotepy

**Solutions connexion directe** :
1. Vérifier que l'URL Pronote est correcte
2. Tester la connexion directement sur le site Pronote
3. S'assurer que l'établissement ne force pas CAS

### Chat IA ne répond pas

**Symptôme** : Message "Une erreur est survenue" après avoir envoyé un message

**Solutions** :
1. Vérifier que `OPENROUTER_API_KEY` est configuré dans Railway
2. Tester la clé :
   ```bash
   curl https://openrouter.ai/api/v1/models \
     -H "Authorization: Bearer VOTRE_CLE"
   ```
3. Vérifier que vous n'avez pas dépassé les quotas gratuits
4. Consulter les logs Railway

### Redis inaccessible

**Symptôme** : "redis":"error" dans `/api/health`

**Solutions** :
1. Vérifier que Redis est bien ajouté dans Railway
2. Vérifier que `REDIS_URL` contient `${{Redis.REDIS_URL}}`
3. Redémarrer le service backend

## Optimisations Post-Déploiement

### 1. Domaine personnalisé

**Backend (Railway)** :
1. Settings → Networking
2. Custom Domain
3. Ajouter votre domaine (ex: api.votre-domaine.com)

**Frontend (GitHub Pages)** :
1. Settings → Pages → Custom domain
2. Ajouter votre domaine (ex: pronote.votre-domaine.com)
3. Activer "Enforce HTTPS"

### 2. Monitoring

**Railway** :
- Activer les alertes dans Settings
- Configurer Sentry (optionnel) :
  ```
  SENTRY_DSN=https://...@sentry.io/...
  ```

**Frontend** :
- Utiliser Google Analytics (optionnel)
- Monitorer les erreurs JavaScript

### 3. Sécurité renforcée

1. **Rate limiting plus strict** :
   ```
   RATE_LIMIT_PER_MINUTE=30
   RATE_LIMIT_PER_HOUR=500
   ```

2. **Session plus courte** :
   ```
   SESSION_EXPIRATION_SECONDS=43200  # 12 heures
   JWT_EXPIRATION_HOURS=12
   ```

3. **HTTPS uniquement** :
   - Railway force HTTPS automatiquement
   - GitHub Pages aussi si domaine custom configuré

## Mises à Jour

### Mettre à jour le code

```bash
# Modifier le code
git add .
git commit -m "Description des modifications"
git push

# Railway redéploiera automatiquement le backend
# GitHub Pages mettra à jour le frontend (1-2 minutes)
```

### Mettre à jour les dépendances

**Backend** :
```bash
cd backend
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
git commit -am "Update Python dependencies"
git push
```

## Coûts

### Railway (Backend + Redis)

**Plan gratuit** :
- 500h d'exécution/mois (≈20 jours)
- 500 MB RAM
- 1 GB stockage Redis

**Si dépassement** :
- Passer au plan Developer : $5/mois
- Ou utiliser Render.com (750h/mois gratuit)

### GitHub Pages (Frontend)

- **100% gratuit**
- Bande passante illimitée
- Pas de limite de visiteurs

### OpenRouter (IA)

**Modèles gratuits** :
- DeepSeek R1 : gratuit
- Quotas généreux

**Si besoin de modèles payants** :
- Claude : ~$0.50/million tokens
- GPT-4 : ~$5/million tokens

## Support

Si problème persistant :

1. Vérifier cette documentation complète
2. Consulter les logs (Railway + Browser Console)
3. Tester chaque composant individuellement
4. Vérifier les URLs et clés API

## Conclusion

Votre Assistant Pronote IA est maintenant en production !

**URLs importantes à sauvegarder** :
- Backend : `https://votre-projet.railway.app`
- Frontend : `https://VOTRE_USERNAME.github.io/assistant-pronote-ia`
- Logs Railway : Dashboard Railway → Service backend → View Logs

**Prochaines étapes** :
1. Tester avec plusieurs utilisateurs
2. Monitorer les erreurs
3. Améliorer l'IA avec des prompts personnalisés
4. Ajouter de nouvelles fonctionnalités
