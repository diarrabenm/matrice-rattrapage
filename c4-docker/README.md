# C4 · Docker & Compose

Micro-application FastAPI (`GET /health` → `200 {"status":"ok"}`) conteneurisée avec PostgreSQL 16.

## Fichiers

| Fichier | Rôle |
|---|---|
| `app/main.py` | Micro-application : `/health` (vivacité) et `/ready` (disponibilité de la base) |
| `Dockerfile` | Image de l'application : version figée, utilisateur non privilégié, healthcheck |
| `compose.yaml` | Deux services (`app`, `db`), réseau, volume, secret, healthchecks |
| `.env.example` | Environnement factice, à copier en `.env` (jamais versionné) |
| `.dockerignore` | Empêche `.env`, `.venv` et les tests d'entrer dans l'image |
| `seed/jeu_test.sql` | Jeu de test fictif (séances) |
| `scripts/scenarios.sh` | Rejoue les 4 scénarios et écrit les traces dans `../preuves/c4/` |
| `tests/test_app.py` | Tests unitaires de l'application |

## Commandes

Prérequis : Docker Engine 24+ avec Compose v2.23+ (pour les secrets de type `environment`). Toutes les commandes se lancent depuis `c4-docker/`.

```bash
# Préparation
cp .env.example .env                  # puis changer POSTGRES_PASSWORD

# Build
docker compose build

# Lancement
docker compose up -d                  # l'app attend que db soit "healthy"

# Inspection
docker compose ps                     # état et santé des conteneurs
docker compose logs -f app            # journaux de l'application
curl http://127.0.0.1:8000/health     # vivacité -> {"status":"ok"}
curl http://127.0.0.1:8000/ready      # disponibilité réelle de la base
docker inspect --format '{{json .State.Health}}' matrice-c4-db-1
docker compose exec app id            # uid=10001(appuser) : pas root
docker compose exec db pg_isready -U matrice -d matrice

# Arrêt
docker compose stop                   # arrête, garde les conteneurs
docker compose down                   # supprime conteneurs et réseau, GARDE le volume
docker compose down -v                # supprime aussi le volume : données perdues

# Scénarios de preuve (Linux, macOS ou Git Bash sous Windows)
bash scripts/scenarios.sh
```

Tests unitaires, sans Docker :

```bash
python -m venv .venv
source .venv/bin/activate             # Windows : .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest -v
```

## Explications

### Séparation application / base
Deux conteneurs, deux responsabilités. `app` est sans état : on peut le reconstruire ou le remplacer sans rien perdre. `db` porte les données. Chacun a son image, son cycle de vie et ses ressources, et une mise à jour de l'un n'impose pas de toucher l'autre.

### DNS de service
Compose crée le réseau `backend` et y enregistre chaque service sous son nom. L'application joint donc la base avec `DB_HOST=db`, sans adresse IP : celles des conteneurs changent à chaque recréation, le nom reste.

### Réseau et exposition
La base n'a **aucun** `ports:`. Elle n'est joignable que depuis le réseau `backend`, pas depuis l'hôte ni depuis Internet. L'application n'est publiée que sur `127.0.0.1`. C'est l'inverse de `database_ingress: 0.0.0.0/0` analysé dans le module C3.

### Volume
`db_data` est un volume nommé monté sur `/var/lib/postgresql/data`. Il vit en dehors du conteneur : `docker compose down` supprime le conteneur mais garde les données. Seul `down -v` les efface (voir le scénario 2).

### Versions
Les images sont figées (`python:3.12.8-slim`, `postgres:16.4-alpine`), tout comme les dépendances Python (`requirements.txt`). Avec `latest`, un build pourrait changer de version majeure de PostgreSQL du jour au lendemain, et le format des données sur le volume pourrait devenir incompatible.

### Utilisateur non privilégié
Le `Dockerfile` crée `appuser` (uid 10001) et l'active avec `USER`. Si l'application est compromise, l'attaquant n'est pas root dans le conteneur. L'image PostgreSQL officielle, elle, exécute déjà le serveur sous l'utilisateur `postgres`.

### Variables et secrets
- Les **variables** non sensibles (`POSTGRES_DB`, `POSTGRES_USER`, `DB_HOST`) passent par l'environnement.
- Le **mot de passe** est déclaré comme secret Compose. Il est lu dans `.env` au lancement, puis monté **en fichier** dans `/run/secrets/db_password`. PostgreSQL (`POSTGRES_PASSWORD_FILE`) et l'application le lisent dans ce fichier. Il n'apparaît donc pas dans `docker inspect` (voir le scénario 3).
- `.env` n'est jamais versionné et est exclu de l'image par `.dockerignore`. Seul `.env.example`, avec des valeurs factices, est versionné.

### Healthchecks
- `db` utilise `pg_isready`, qui vérifie que PostgreSQL accepte les connexions.
- `app` appelle `/health` depuis l'intérieur du conteneur (défini dans le `Dockerfile`).
- `depends_on: condition: service_healthy` fait attendre l'application jusqu'à ce que la base soit **saine**, pas seulement démarrée.

### Conteneur démarré ≠ service disponible
Un conteneur `Up` signifie seulement que son processus principal tourne. PostgreSQL peut être `Up` pendant plusieurs secondes tout en refusant encore les connexions (initialisation, état `health: starting`). C'est pourquoi on s'appuie sur les healthchecks, et non sur l'état `Up`.

### /health ne teste pas la base, et c'est assumé
`/health` répond `200` même si PostgreSQL est arrêté. C'est un test de **vivacité** : si la base tombe, redémarrer l'application ne réparerait rien. La disponibilité et la persistance de la base sont donc vérifiées **séparément** :
- `GET /ready` exécute `SELECT 1` et répond `503` si la base est injoignable ;
- `pg_isready` sert de healthcheck au service `db` ;
- le scénario 2 vérifie la persistance par une requête SQL avant et après redémarrage.

## Scénarios et preuves

| Scénario | Résultat observé | Trace |
|---|---|---|
| 1. Base non prête | Au démarrage, l'app attend que `db` soit `Healthy`. Base arrêtée : `/health` = 200, `/ready` = 503 | [scenario1](../preuves/c4/scenario1_base_non_prete.txt) |
| 2. Redémarrage préservant les données | 7 séances avant `down`/`up`, 7 après | [scenario2](../preuves/c4/scenario2_persistance.txt) |
| 3. Absence de secret dans l'image | 0 occurrence du mot de passe dans l'historique, le système de fichiers et les variables | [scenario3](../preuves/c4/scenario3_aucun_secret.txt) |
| 4. Restauration d'un jeu de test | 6 séances → suppression (0) → restauration `pg_dump` (6) | [scenario4](../preuves/c4/scenario4_restauration.txt) |
