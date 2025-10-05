# 🚀 Instructions de Déploiement - Assistant Pronote IA

## ✅ État Actuel

Votre projet est **prêt à être poussé sur GitHub** ! Tous les fichiers sont configurés :

- ✅ Configuration Git avec le compte `Alexandre-full-stack` (botdubot1@gmail.com)
- ✅ `.gitignore` créé pour protéger les fichiers sensibles
- ✅ `backend/.env.example` créé comme template
- ✅ `CLAUDE.md` créé avec toute la documentation technique
- ✅ Commit créé avec tous les fichiers
- ✅ Remote GitHub configuré : `https://github.com/Alexandre-full-stack/assistant-pronote-ia.git`

## 📋 Étapes à Suivre

### 1️⃣ Créer le Repository sur GitHub

**Option A : Via l'interface GitHub (Recommandé)**

1. Allez sur [github.com](https://github.com)
2. Connectez-vous avec le compte **Alexandre-full-stack** (botdubot1@gmail.com)
3. Cliquez sur le bouton **"New"** (ou "+" → "New repository")
4. Remplissez les informations :
   - **Repository name** : `assistant-pronote-ia`
   - **Description** : `Application web pour accéder à Pronote avec support CAS et assistant IA`
   - **Visibility** : Public ✅ (pour GitHub Pages gratuit)
   - **NE PAS** cocher "Initialize this repository with:"
     - ❌ README
     - ❌ .gitignore
     - ❌ license
5. Cliquez sur **"Create repository"**

**Option B : Via GitHub CLI (si installé)**

```bash
gh repo create assistant-pronote-ia --public --description "Application web pour accéder à Pronote avec support CAS et assistant IA"
```

### 2️⃣ Pousser le Code vers GitHub

Une fois le repository créé sur GitHub, exécutez :

```bash
git push -u origin main
```

**Authentification :**
- Si demandé, entrez vos identifiants GitHub
- Ou utilisez un **Personal Access Token** (recommandé) :
  1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  2. Generate new token (classic)
  3. Cocher : `repo`, `workflow`
  4. Utiliser le token comme mot de passe lors du push

### 3️⃣ Activer GitHub Pages

1. Allez sur votre repository : `https://github.com/Alexandre-full-stack/assistant-pronote-ia`
2. Cliquez sur **Settings** (onglet en haut)
3. Dans le menu de gauche, cliquez sur **Pages**
4. Sous "Source" :
   - Branch : `main`
   - Folder : `/(root)`
5. Cliquez sur **Save**
6. Attendez 1-2 minutes
7. Votre site sera accessible sur : `https://alexandre-full-stack.github.io/assistant-pronote-ia`

### 4️⃣ Déployer le Backend sur Railway

#### A. Créer un compte Railway

1. Allez sur [railway.app](https://railway.app)
2. Connectez-vous avec GitHub (utilisez Alexandre-full-stack)
3. Autorisez Railway à accéder à vos repositories

#### B. Créer le projet

1. Dashboard Railway → **"New Project"**
2. Sélectionnez **"Deploy from GitHub repo"**
3. Sélectionnez `assistant-pronote-ia`
4. Railway détectera automatiquement le Dockerfile

#### C. Ajouter Redis

1. Dans votre projet Railway → **"+ New"**
2. **"Database"** → **"Redis"**
3. Railway créera automatiquement la variable `REDIS_URL`

#### D. Configurer les variables d'environnement

Dans le service backend → **Variables** → **Raw Editor**, copiez-collez :

**Générez d'abord 3 clés secrètes :**

```bash
# Exécutez 3 fois pour générer 3 clés différentes
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Variables à ajouter :**

```env
PORT=8000
HOST=0.0.0.0
ENV=production
DEBUG=False

SECRET_KEY=VOTRE_CLE_1_ICI
JWT_SECRET_KEY=VOTRE_CLE_2_ICI
ENCRYPTION_KEY=VOTRE_CLE_3_ICI

OPENROUTER_API_KEY=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

REDIS_URL=${{Redis.REDIS_URL}}

ALLOWED_ORIGINS=https://alexandre-full-stack.github.io

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

**⚠️ IMPORTANT :** Remplacez `OPENROUTER_API_KEY` par votre vraie clé si la clé ci-dessus ne fonctionne plus.

#### E. Vérifier le déploiement

1. Attendez 5-10 minutes que Railway build et déploie
2. Railway vous donnera une URL : `https://votre-projet-xxxx.up.railway.app`
3. Testez : `https://votre-projet-xxxx.up.railway.app/api/health`

### 5️⃣ Connecter Frontend et Backend

#### A. Modifier la configuration du frontend

1. Ouvrez `frontend/js/config.js` dans votre éditeur
2. Modifiez la ligne :
   ```javascript
   API_BASE_URL: 'https://votre-projet-xxxx.up.railway.app',  // ← Remplacez par votre vraie URL Railway
   ```
3. Modifiez aussi :
   ```javascript
   DEBUG: false  // Désactiver le debug en production
   ```

#### B. Pousser les modifications

```bash
git add frontend/js/config.js
git commit -m "Configure production backend URL"
git push
```

#### C. Mettre à jour les CORS sur Railway

1. Retournez sur Railway → Variables
2. Vérifiez que `ALLOWED_ORIGINS` contient :
   ```
   ALLOWED_ORIGINS=https://alexandre-full-stack.github.io
   ```
3. Le backend redémarrera automatiquement

### 6️⃣ Tester l'Application

1. Ouvrez `https://alexandre-full-stack.github.io/assistant-pronote-ia`
2. Acceptez le disclaimer
3. Testez la connexion :
   - **Connexion directe** : Entrez votre URL Pronote + identifiants
   - **Connexion CAS** : Sélectionnez votre ENT + identifiants
4. Vérifiez que :
   - ✅ Dashboard s'affiche
   - ✅ Devoirs se chargent
   - ✅ Emploi du temps s'affiche
   - ✅ Notes s'affichent
   - ✅ Chat IA répond

## 🔧 Dépannage

### "Backend inaccessible"

```bash
# Vérifiez que le backend fonctionne
curl https://votre-projet.railway.app/api/health

# Devrait retourner : {"status":"healthy","redis":"ok",...}
```

**Solutions :**
- Vérifiez les logs Railway
- Vérifiez que `REDIS_URL` est configuré
- Vérifiez que toutes les variables sont définies

### Erreur CORS

**Console du navigateur :** "has been blocked by CORS policy"

**Solutions :**
1. Vérifiez `ALLOWED_ORIGINS` dans Railway
2. Vérifiez `API_BASE_URL` dans `frontend/js/config.js`
3. Videz le cache du navigateur (Ctrl+Shift+R)

### Authentification échoue

**Solutions :**
1. Vérifiez que votre ENT est supporté : `/api/ents`
2. Testez vos identifiants sur le vrai site Pronote/ENT
3. Consultez les logs Railway pour voir l'erreur

### Chat IA ne répond pas

**Solutions :**
1. Vérifiez la clé OpenRouter dans Railway
2. Testez la clé :
   ```bash
   curl https://openrouter.ai/api/v1/models \
     -H "Authorization: Bearer VOTRE_CLE"
   ```

## 📚 Ressources

- **Repository GitHub** : `https://github.com/Alexandre-full-stack/assistant-pronote-ia`
- **Frontend (GitHub Pages)** : `https://alexandre-full-stack.github.io/assistant-pronote-ia`
- **Backend (Railway)** : `https://votre-projet-xxxx.up.railway.app`
- **Documentation technique** : Voir [CLAUDE.md](CLAUDE.md)
- **Guide de déploiement détaillé** : Voir [docs/DEPLOIEMENT.md](docs/DEPLOIEMENT.md)

## 🎯 Commandes Utiles

```bash
# Vérifier le statut Git
git status

# Voir les derniers commits
git log --oneline -5

# Pousser les changements
git add .
git commit -m "Description des modifications"
git push

# Tester le backend localement
cd backend
python server.py

# Tester le frontend localement
cd frontend
python -m http.server 3000
```

## 🔐 Sécurité

**NE JAMAIS committer :**
- ❌ `.env` avec de vraies clés
- ❌ Mots de passe
- ❌ Clés API privées

**Toujours utiliser :**
- ✅ `.env.example` pour les templates
- ✅ Variables d'environnement sur Railway
- ✅ `.gitignore` pour protéger les fichiers sensibles

## ✨ Prochaines Étapes

Une fois le déploiement réussi :

1. **Tester avec de vrais utilisateurs**
2. **Monitorer les logs Railway** pour détecter les erreurs
3. **Améliorer l'IA** avec des prompts personnalisés
4. **Ajouter des fonctionnalités** (notifications, statistiques, etc.)
5. **Configurer un domaine personnalisé** (optionnel)

---

**Besoin d'aide ?** Consultez les logs Railway et la console du navigateur pour identifier les erreurs précises.

**Bon déploiement ! 🚀**
