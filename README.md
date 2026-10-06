# MATRiCE · Rattrapage individuel

Étudiant : Ben Moriba DIARRA. Modules attribués : **C3** (Cybersécurité / Monitoring IA) et **C4** (Docker & Compose).

Chaque module est autonome et se vérifie sans l'autre.

## Structure

```
.
├── c3-cybersecurite/
│   ├── DOSSIER_C3.md / .pdf  # Dossier de 5 pages : risques, frontières de confiance, alerte, runbook
│   ├── donnees/              # Logs et configuration fournis par le sujet
│   ├── alerte/               # Règle d'alerte déterministe + masquage des secrets
│   ├── exemples/             # Logs déclenchant / ne déclenchant pas l'alerte
│   └── tests/                # 10 tests pytest
├── c4-docker/
│   ├── app/                  # Micro-application FastAPI (/health, /ready)
│   ├── Dockerfile, compose.yaml, .env.example
│   ├── seed/jeu_test.sql     # Jeu de test fictif
│   ├── scripts/scenarios.sh  # Rejoue les 4 scénarios demandés
│   ├── tests/                # 4 tests pytest
│   └── README.md             # Explications détaillées du module C4
├── preuves/
│   ├── c3/                   # Exécution de la règle d'alerte
│   └── c4/                   # Traces des 4 scénarios Docker
├── JUSTIFICATIONS.md         # Choix techniques, alternatives, preuves, limites
└── SOURCES_IA.md             # Déclaration des usages de l'IA
```

## Prérequis

| Outil | Version testée | Utilisé pour |
|---|---|---|
| Git | 2.47 | Cloner le dépôt |
| Python | 3.12 | Tests C3 et C4 |
| Docker Engine + Compose | Docker 29, Compose v2.23 ou plus | Module C4 |
| bash | Linux, macOS, ou Git Bash / WSL sous Windows | Script des scénarios C4 |

```bash
git clone https://github.com/diarrabenm/matrice-rattrapage.git
cd matrice-rattrapage
```

Sous Windows (PowerShell), remplacer `source .venv/bin/activate` par `.venv\Scripts\activate` et `cp` par `copy`.

## Module C3 · Cybersécurité / Monitoring IA

À lire : [c3-cybersecurite/DOSSIER_C3.md](c3-cybersecurite/DOSSIER_C3.md) (ou la [version PDF](c3-cybersecurite/DOSSIER_C3.pdf), 5 pages).

```bash
cd c3-cybersecurite

# Installation
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Lancement de la règle d'alerte sur les logs du sujet (2 alertes attendues : A1 partner-A, A2 d9)
python -m alerte.regle_alerte donnees/logs_sujet.log

# Exemples déclenchant / ne déclenchant pas
python -m alerte.regle_alerte exemples/a1_declenche.log
python -m alerte.regle_alerte exemples/a1_ne_declenche_pas.log

# Tests (10 tests)
python -m pytest -v
```

## Module C4 · Docker & Compose

Explications détaillées : [c4-docker/README.md](c4-docker/README.md).

```bash
cd c4-docker

# Installation : environnement factice
cp .env.example .env

# Build et lancement
docker compose up -d --build

# Inspection
docker compose ps                       # les deux services doivent être "healthy"
curl http://127.0.0.1:8000/health       # {"status":"ok"}
curl http://127.0.0.1:8000/ready        # {"status":"ok","database":"up"}

# Scénarios (base non prête, persistance, absence de secret, restauration)
bash scripts/scenarios.sh               # traces réécrites dans ../preuves/c4/

# Arrêt
docker compose down                     # garde les données
docker compose down -v                  # supprime aussi le volume

# Tests unitaires (sans Docker)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -v
```

## Sécurité du dépôt

Aucun secret n'est versionné : `.env` est ignoré par Git, seul `.env.example` (valeurs factices) est présent. Les données du jeu de test sont fictives.
