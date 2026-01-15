# REDDIT_project

Projet de collecte et d'analyse de données Reddit utilisant Python, PRAW et MongoDB.

## Description

Ce projet est un système de collecte automatisé de posts et commentaires Reddit provenant de subreddits liés à l'intelligence artificielle et au machine learning. Les données sont stockées dans une base de données MongoDB Atlas pour des analyses ultérieures.

Le système collecte des données à partir de plusieurs catégories de subreddits: 
- FAST:  DeepSeek, ChatGPT, Claude, Copilot
- CORE: artificial, MachineLearning, deeplearning  
- CREATOR: LocalLLaMA, StableDiffusion, generativeAI

## Architecture du Projet

### Structure des Dossiers

```
REDDIT_project/
├── src/
│   └── reddit_ai/
│       ├── config.py                  # Configuration centralisée
│       ├── collectors/
│       │   ├── posts.py              # Collection des posts Reddit
│       │   ├── comments.py           # Collection des commentaires
│       │   └── reddit_client.py      # Client PRAW
│       ├── db/
│       │   ├── mongo.py              # Connexion MongoDB avec cache
│       │   ├── indexes.py            # Définition des index
│       │   └── repositories/
│       │       ├── posts_repo.py     # Opérations CRUD pour posts
│       │       └── comments_repo.py  # Opérations CRUD pour commentaires
│       └── utils/
│           ├── common.py             # Fonctions utilitaires
│           └── logging_setup.py      # Configuration des logs
├── scripts/
│   ├── new.py                        # Collecte des posts récents
│   ├── hot.py                        # Collecte des posts populaires
│   ├── top_day.py                    # Collecte des meilleurs posts
│   ├── c_hot.py                      # Collecte des commentaires hot
│   └── c_top.py                      # Collecte des commentaires top
├── . env.example                      # Template des variables d'environnement
├── . gitignore                        # Fichiers à ignorer
└── Requirements.txt                  # Dépendances Python
```

## Fonctionnalités Principales

### Collecte des Posts

Le module `collectors/posts.py` permet de récupérer des posts selon différents critères: 

- Types de listing: new, hot, top
- Filtrage temporel configurable (window_days)
- Filtres de qualité: 
  - Détection de langue anglaise
  - Exclusion des bots
  - Exclusion du contenu NSFW
  - Exclusion des posts supprimés

### Collecte des Commentaires

Le module `collectors/comments.py` récupère les commentaires avec:

- Plusieurs modes de tri:  top, new, hot, confidence
- Option pour commentaires de premier niveau uniquement
- Limite configurable du nombre de commentaires
- Mêmes filtres de qualité que les posts

### Gestion de la Base de Données

#### Connexion MongoDB
- Utilisation de `lru_cache` pour singleton de connexion
- Support de MongoDB Atlas avec authentification
- Retry automatique des écritures
- Ping de vérification au démarrage

#### Opérations en Masse
Les repositories utilisent `bulk_write` avec `UpdateOne` pour:
- Insertion efficace par lots (batch_size configurable)
- Upsert:  mise à jour si existant, insertion sinon
- Tracking des métriques (score_max, num_comments_max)
- Retry automatique en cas d'échec

#### Index
Création automatique d'index pour optimiser les requêtes: 
- Posts: (subreddit, created_utc)
- Comments: (post_id, created_utc)

## Installation

### Prérequis
- Python 3.8 ou supérieur
- MongoDB Atlas (ou instance MongoDB locale)
- Compte développeur Reddit (pour API credentials)

### Étapes d'Installation

1. Cloner le repository
```bash
git clone https://github.com/Houssam-Ibnchakroune/REDDIT_project.git
cd REDDIT_project
```

2. Installer les dépendances
```bash
pip install -r Requirements.txt
```

3. Configurer les variables d'environnement

Copier le fichier `.env.example` vers `.env` et remplir les valeurs:

```bash
cp .env.example .env
```

Variables requises:
```
MONGO_HOST=your-cluster. mongodb.net
MONGO_USER=your-username
MONGO_PASS=your-password
MONGO_DB=your-database-name

REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
REDDIT_USER_AGENT=Social_Network_Analysis by u/your-username
```

### Obtenir les Credentials Reddit

1. Aller sur https://www.reddit.com/prefs/apps
2. Créer une application (script type)
3. Noter le client_id et client_secret

## Utilisation

### Scripts de Collection

#### Collecter les Posts Récents
```bash
python scripts/new.py
```
Collecte jusqu'à 250 posts récents par subreddit FAST, 200 pour CORE et CREATOR.

#### Collecter les Posts Populaires
```bash
python scripts/hot.py
```
Collecte les posts actuellement populaires (80/60/60 par catégorie).

#### Collecter les Meilleurs Posts
```bash
python scripts/top_day.py
```
Collecte les meilleurs posts de tous les temps (150/120/120 par catégorie).

#### Collecter les Commentaires
```bash
python scripts/c_hot.py      # Commentaires des posts hot
python scripts/c_top.py      # Commentaires des posts top
```

### Logs

Les logs sont automatiquement créés dans le dossier `logs/`:
- Console: niveau INFO
- Fichier `logs/app.log`: niveau DEBUG
- Rotation automatique (2 MB max, 3 backups)

## Détails Techniques

### Filtrage de Langue

La fonction `is_englishish()` dans `utils/common.py` utilise une heuristique simple:
- Minimum 10 caractères
- Au moins 60% de caractères ASCII alphabétiques

### Gestion des Données

#### Structure d'un Post
```python
{
    "_id": "post_id",
    "post_id": "abc123",
    "subreddit": "MachineLearning",
    "title": ".. .",
    "selftext": "...",
    "author": "username",
    "score": 150,
    "score_max": 150,
    "upvote_ratio": 0.95,
    "num_comments":  42,
    "num_comments_max": 42,
    "created_utc": 1234567890,
    "permalink": "/r/.. .",
    "listing":  "hot",
    "seen_in":  ["hot", "new"],
    "time_filter":  "day",
    "first_seen_at": datetime,
    "last_seen_at": datetime,
    "ingested_at": datetime
}
```

#### Structure d'un Commentaire
```python
{
    "_id": "comment_id",
    "comment_id": "xyz789",
    "post_id": "abc123",
    "subreddit": "MachineLearning",
    "author": "username",
    "body": "...",
    "score": 25,
    "score_max":  25,
    "created_utc": 1234567890,
    "parent_id": "t3_abc123",
    "permalink": "/r/. ../comment/...",
    "is_top_level": true,
    "sort":  "top",
    "first_seen_at": datetime,
    "last_seen_at":  datetime,
    "ingested_at": datetime
}
```

### Optimisations

1.  Connexion MongoDB en cache (singleton via lru_cache)
2. Bulk writes pour insertions massives
3. Upsert pour éviter les doublons
4. Index sur les champs fréquemment requêtés
5. Retry automatique des opérations échouées

## Dépendances

- praw 7.8.1 - Python Reddit API Wrapper
- pymongo 4.15.1 - Driver MongoDB
- python-dotenv 1.1.1 - Gestion des variables d'environnement
- requests 2.32.5 - Requêtes HTTP
- certifi 2025.8.3 - Certificats SSL
- dnspython 2.8.0 - Résolution DNS pour MongoDB

## Configuration Avancée

### Personnaliser les Subreddits

Modifier les listes dans les scripts de collection: 

```python
FAST = ["DeepSeek", "ChatGPT", "claude", "Copilot"]
CORE = ["artificial", "MachineLearning", "deeplearning"]
CREATOR = ["LocalLLaMA", "StableDiffusion", "generativeAI"]
```

### Ajuster les Limites

Modifier le dictionnaire LIMITS: 

```python
LIMITS = {
    "FAST": 250,
    "CORE": 200,
    "CREATOR": 200,
}
```

### Fenêtre Temporelle

Dans les appels à `fetch_posts_details()`:
```python
window_days=14  # Ne garder que les posts des 14 derniers jours
```

## Scripts Utilitaires

- `scripts/tttt.py` - Affiche les subreddits stockés et quelques documents
- `scripts/tes_atlas.py` - Teste la connexion MongoDB Atlas
- `scripts/oooo.py` - Exemple simple de récupération de commentaires
- `scripts/demo_cached. py` - Démontre la connexion avec cache
- `scripts/demo_naive.py` - Démontre la connexion sans cache

## Résolution de Problèmes

### Erreur de Connexion MongoDB
Vérifier:
- Les credentials dans .env sont corrects
- Le cluster MongoDB Atlas est accessible
- L'IP est whitelistée dans MongoDB Atlas

### Aucun Post Collecté
Vérifier: 
- Les credentials Reddit sont valides
- Les noms de subreddits sont corrects
- La fenêtre temporelle n'est pas trop restrictive

### Erreurs de Rate Limit
Reddit impose des limites d'API:
- Ajouter des pauses entre les requêtes
- Réduire les limites de collecte
- Vérifier le user_agent

## Contribuer

Les contributions sont les bienvenues.  Pour contribuer:

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commit vos changements
4. Push vers la branche
5. Ouvrir une Pull Request

## Licence

Ce projet est à usage éducatif et de recherche. 

## Auteur

Houssam Ibnchakroune & Adam Fartout

## Notes Importantes

- Respecter les Terms of Service de Reddit
- Ne pas abuser de l'API Reddit
- Les données collectées doivent être utilisées de manière éthique
- Protéger les credentials dans le fichier .env