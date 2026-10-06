# Sources et usages de l'IA

## Usage de l'IA

J'ai piloté ce projet de bout en bout et je me suis appuyé sur un assistant IA (**Claude Code**, d'Anthropic, utilisé dans VS Code), comme le sujet l'autorise.

**Mon rôle :** analyse du sujet avec l'assistant et validation de la liste des exigences ; choix de la pile (FastAPI, PostgreSQL) et de l'organisation du travail en plusieurs séances ; contrôle du périmètre (aucun ajout hors cahier des charges) ; décisions sur le dépôt (structure, nom, fichiers gardés hors dépôt) ; relecture ; vérification des résultats et démonstrations en direct.

**Rôle de l'assistant :** rédaction du code (micro-application, Docker, règle d'alerte, tests), des documents (dossier C3, explications C4) et exécution des scénarios, sous ma direction.

## Usages, par fichier

| Fichiers | Ce que l'IA a fait | Ma part |
|---|---|---|
| Tous | Lecture du sujet PDF et liste des consignes à respecter | Fourniture du sujet, validation du plan et du découpage en séances |
| `c4-docker/app/main.py`, `tests/test_app.py` | Rédaction de la micro-application et des tests | Choix de la pile FastAPI + PostgreSQL proposée ; lecture et questions sur le code |
| `c4-docker/Dockerfile`, `compose.yaml`, `.env.example`, `.dockerignore` | Rédaction de la configuration commentée | Relecture ; démonstration en direct de `/health` et `/ready` avec la base arrêtée |
| `c4-docker/scripts/scenarios.sh`, `seed/jeu_test.sql` | Rédaction du script des 4 scénarios et du jeu de test fictif, puis exécution | Observation des résultats dans le navigateur et le terminal |
| `c4-docker/README.md` | Rédaction des explications (réseau, DNS, volume, secrets, healthchecks) | Révision à partir d'une fiche de questions-réponses |
| `c3-cybersecurite/DOSSIER_C3.md` et `.pdf` | Analyse des logs, rédaction des risques, du schéma et du runbook, mise en page PDF | Relecture ; exigence de ne rien ajouter hors cahier des charges |
| `c3-cybersecurite/alerte/*.py`, `tests/`, `exemples/` | Rédaction de la règle d'alerte, du masquage, des exemples et des tests | Relecture et questions sur les seuils |
| `README.md`, `JUSTIFICATIONS.md`, `.gitignore`, `.gitattributes` | Rédaction | Relecture |
| `preuves/` | Traces générées par l'exécution réelle des scripts (pas écrites à la main) | — |

## Requêtes représentatives

Requêtes adressées à l'assistant, reformulées sans les fautes de frappe :

- « Je vais te donner le sujet : respecte les consignes et fais exactement ce qui est demandé dans le cahier des charges. »
- « Rassure-moi : tu fais seulement ce qui est demandé dans le cahier des charges, tu n'ajoutes rien d'autre ? »
- « Je ne veux pas que tu finisses tout le projet aujourd'hui. »- « Lance l'application dans mon navigateur. »
- « Fais toi-même la démonstration dans le terminal » (arrêt de la base, puis `/health` et `/ready`).
- « Fais-moi un résumé de l'avancement du projet. »

## Adaptations et corrections apportées en cours de route

| Problème constaté | Correction |
|---|---|
| La règle `*.log` du `.gitignore` excluait les logs du sujet et les exemples : les tests C3 échouaient sur un clone propre | Exceptions ajoutées dans `.gitignore` (commit « versionne les fichiers de logs du sujet ») |
| Le dossier C3 faisait 6 pages, alors que le sujet impose 3 à 5 | Rédaction resserrée sans retirer d'exigence du sujet : 5 pages |
| Le schéma des frontières de confiance montrait la validation de la réponse de l'IA dans le mauvais sens | Flèche corrigée (réponse de l'IA → validation) |
| Une ligne de log avec un guillemet non fermé aurait été perdue par l'analyseur | Repli sur un découpage simple plutôt que d'ignorer la ligne |
| Les scripts risquaient d'avoir des fins de ligne Windows, ce qui casse bash | Ajout de `.gitattributes` (fins de ligne LF) |
| `/health` devait rester tel que demandé par le sujet sans tester la base | Ajout d'une route séparée `/ready`, comme le sujet le prévoit (« vérifier séparément ») |

## Vérifications effectuées

- **Tests automatisés** : 4 tests (C4) et 10 tests (C3), tous réussis.
- **Exécution réelle** des 4 scénarios Docker. Les traces dans `preuves/c4/` sont la sortie brute des commandes.
- **Démonstration en direct** de la différence entre conteneur démarré et service disponible (base arrêtée : `/health` = 200, `/ready` = 503).
- **Clone propre** du dépôt depuis GitHub, puis relance des tests, pour vérifier que le correcteur peut tout exécuter sans fichier manquant.
- **Recherche du mot de passe** dans l'image Docker : 0 occurrence (scénario 3).
- **Comptage des pages** du dossier C3 sur le PDF généré : 5 pages.
- **Contrôle du dépôt** : aucun `.env`, `.venv`, `node_modules` ni secret versionné.

## Autres sources

Aucun code n'a été copié depuis une autre source. Documentations de référence pour vérifier les notions utilisées :
- Docker : documentation de Compose (`depends_on`, `healthcheck`, `secrets`) et bonnes pratiques Dockerfile ;
- image officielle PostgreSQL sur Docker Hub (`POSTGRES_PASSWORD_FILE`, `pg_isready`) ;
- FastAPI : documentation officielle ;
- OWASP : Top 10 for LLM Applications (injection de prompt) et Logging Cheat Sheet (logs sans secret).
