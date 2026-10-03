#!/usr/bin/env bash
# Rejoue les 4 scénarios demandés et enregistre les traces dans preuves/c4/.
# Usage (depuis c4-docker/) : bash scripts/scenarios.sh
set -u
export MSYS_NO_PATHCONV=1   # Git Bash (Windows) : ne pas réécrire les chemins /run/...

cd "$(dirname "$0")/.."
[ -f .env ] || { echo "Copier d'abord .env.example en .env"; exit 1; }
set -a; . ./.env; set +a

PREUVES=../preuves/c4
mkdir -p "$PREUVES" backups
APP=http://127.0.0.1:${APP_PORT:-8000}

titre() { echo; echo "===== $* ====="; }
http()  { echo "\$ curl $1"; curl -s -w "  -> HTTP %{http_code}\n" "$1"; }
psql_db() { docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$@"; }
attendre_sain() {   # attend que le service $1 soit "healthy"
  for _ in $(seq 1 60); do
    [ "$(docker inspect -f '{{.State.Health.Status}}' "$(docker compose ps -q "$1")" 2>/dev/null)" = healthy ] && return 0
    sleep 1
  done
  echo "Timeout : $1 n'est pas healthy"; return 1
}

# ---------------------------------------------------------------------------
scenario_1_base_non_prete() {
  titre "Scénario 1a : démarrage à froid, l'app attend que la base soit DISPONIBLE"
  docker compose down -v 2>&1
  echo "\$ docker compose up -d --build"
  docker compose up -d --build 2>&1 | grep -E "db-1|app-1"
  attendre_sain app

  titre "Scénario 1b : la base tombe pendant que l'app tourne"
  echo "\$ docker compose stop db"; docker compose stop db 2>&1
  http "$APP/health"
  http "$APP/ready"
  echo "\$ docker compose ps"; docker compose ps --format "table {{.Service}}\t{{.Status}}"
  echo "=> Conteneur app démarré et /health OK, mais service NON disponible (/ready = 503)."

  titre "Scénario 1c : la base revient"
  docker compose start db 2>&1; attendre_sain db
  http "$APP/ready"
}

# ---------------------------------------------------------------------------
scenario_2_persistance() {
  titre "Scénario 2 : un redémarrage complet préserve les données (volume db_data)"
  psql_db -q < seed/jeu_test.sql
  psql_db -c "INSERT INTO seance (date_seance, demi_journee, groupe, formateur, titre)
              VALUES ('2026-10-24', 'matin', 'B3D', 'Formateur E', 'Ligne ajoutée avant redémarrage');"
  psql_db -c "SELECT count(*) AS seances_avant FROM seance;"
  echo "\$ docker compose down   (sans -v : le volume est conservé)"
  docker compose down 2>&1
  echo "\$ docker volume ls"; docker volume ls --filter name=matrice-c4
  echo "\$ docker compose up -d"; docker compose up -d 2>&1 | grep -E "Started|Healthy"
  attendre_sain db
  psql_db -c "SELECT count(*) AS seances_apres FROM seance;"
  psql_db -c "SELECT titre FROM seance WHERE formateur = 'Formateur E';"
}

# ---------------------------------------------------------------------------
scenario_3_aucun_secret_dans_image() {
  titre "Scénario 3 : aucun secret dans l'image"
  IMAGE=matrice-c4-app:1.0.0
  echo "Recherche de la valeur de POSTGRES_PASSWORD (non affichée) dans l'image $IMAGE"

  echo "-- Variables d'environnement de l'image :"
  docker image inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$IMAGE"

  n=$(docker history --no-trunc "$IMAGE" | grep -c -- "$POSTGRES_PASSWORD")
  echo "-- Occurrences dans l'historique des couches (docker history) : $n"

  cid=$(docker create "$IMAGE")
  n=$(docker export "$cid" | tar -xOf - 2>/dev/null | grep -a -c -- "$POSTGRES_PASSWORD")
  docker rm "$cid" > /dev/null
  echo "-- Occurrences dans le système de fichiers de l'image (docker export) : $n"

  n=$(docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$(docker compose ps -q app)" | grep -c -- "$POSTGRES_PASSWORD")
  echo "-- Occurrences dans les variables du conteneur en cours (docker inspect) : $n"

  echo "-- Le secret n'existe qu'à l'exécution, monté en fichier :"
  docker compose exec -T app ls -l /run/secrets/
  echo "=> 0 occurrence attendue partout : le mot de passe n'est ni dans l'image ni dans les variables."
}

# ---------------------------------------------------------------------------
scenario_4_restauration() {
  titre "Scénario 4 : sauvegarde puis restauration du jeu de test"
  psql_db -q < seed/jeu_test.sql
  psql_db -c "SELECT count(*) AS seances_jeu_test FROM seance;"
  echo "\$ pg_dump --clean --if-exists > backups/jeu_test.sql"
  docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists > backups/jeu_test.sql
  echo "-- Incident simulé : suppression de toutes les séances"
  psql_db -c "DELETE FROM seance;"
  psql_db -c "SELECT count(*) AS seances_apres_incident FROM seance;"
  echo "\$ psql < backups/jeu_test.sql"
  psql_db -q < backups/jeu_test.sql
  psql_db -c "SELECT count(*) AS seances_restaurees FROM seance;"
  psql_db -c "SELECT date_seance, demi_journee, titre FROM seance ORDER BY id;"
}

scenario_1_base_non_prete            2>&1 | tee "$PREUVES/scenario1_base_non_prete.txt"
scenario_2_persistance               2>&1 | tee "$PREUVES/scenario2_persistance.txt"
scenario_3_aucun_secret_dans_image   2>&1 | tee "$PREUVES/scenario3_aucun_secret.txt"
scenario_4_restauration              2>&1 | tee "$PREUVES/scenario4_restauration.txt"
