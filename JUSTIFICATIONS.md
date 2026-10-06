# Justifications : choix techniques, alternatives, preuves et limites

## Module C4 · Docker & Compose

### Choix techniques et alternatives écartées

| Choix | Pourquoi | Alternative écartée et raison |
|---|---|---|
| **FastAPI** pour la micro-application | C'est le framework backend de MATRiCE indiqué dans le sujet. Une route tient en quelques lignes. | Flask ou Express : fonctionneraient aussi, mais s'éloignent de la pile MATRiCE. |
| **PostgreSQL 16** | C'est la base de MATRiCE indiquée dans le sujet. `pg_isready` fournit un healthcheck fiable. | MongoDB, autorisé par le sujet, mais hors pile MATRiCE. |
| Images **figées** (`python:3.12.8-slim`, `postgres:16.4-alpine`) | Build reproductible. Pas de changement de version majeure de PostgreSQL non voulu, ce qui pourrait rendre le volume illisible. | `latest` : pratique, mais le résultat change sans prévenir. |
| Image **slim** pour l'application | Image plus légère, donc moins de paquets et moins de surface d'attaque. | `python:3.12` complète (≈ 1 Go) ; `alpine` : compilation de dépendances parfois nécessaire. |
| **Utilisateur non privilégié** `appuser` (uid 10001) | Si l'application est compromise, l'attaquant n'est pas root dans le conteneur. | Root par défaut : plus simple, mais dangereux. |
| Mot de passe en **secret Compose** monté dans `/run/secrets/` | Le mot de passe n'est ni dans l'image ni dans les variables visibles avec `docker inspect` (scénario 3). | Variable `POSTGRES_PASSWORD` directe : visible avec `docker inspect`. Docker Swarm ou Vault : trop lourds pour ce périmètre. |
| Base **sans `ports:`**, application publiée sur **`127.0.0.1`** | La base n'est joignable que par le réseau interne `backend`. C'est l'inverse de `database_ingress: 0.0.0.0/0` analysé en C3. | Publier `5432` sur l'hôte : pratique pour déboguer, mais expose la base. |
| **Volume nommé** `db_data` | Géré par Docker et indépendant du conteneur : survit à `docker compose down`. | Montage d'un dossier de l'hôte : dépend des droits du système de fichiers, en particulier sous Windows. |
| `depends_on: condition: service_healthy` | L'application attend que la base soit **disponible**, pas seulement démarrée. | `depends_on` simple : attend seulement le démarrage du conteneur. |
| `/health` **sans** test de la base, plus `/ready` **avec** test | `/health` mesure la vivacité : un incident PostgreSQL ne doit pas faire redémarrer l'application, ce qui ne réparerait rien. `/ready` mesure la disponibilité réelle. | Un seul `/health` qui teste la base : il mélange vivacité et disponibilité. |
| Scénarios dans **un script bash** | Exécution reproductible : le correcteur relance tout avec une commande, et les traces sont régénérées. | Captures d'écran seules : le sujet précise qu'elles ne remplacent pas une exécution reproductible. |

### Preuves
- Tests unitaires de l'application : `c4-docker/tests/test_app.py` (4 tests).
- Scénarios exécutés, avec leurs traces dans `preuves/c4/` :

| Scénario | Résultat |
|---|---|
| Base non prête | L'application attend `db Healthy`. Base arrêtée : `/health`=200, `/ready`=503 |
| Redémarrage | 7 séances avant `down`/`up`, 7 après |
| Absence de secret dans l'image | 0 occurrence (historique, système de fichiers, variables) |
| Restauration d'un jeu de test | 6 → 0 → 6 séances |

### Limites
- Le mot de passe reste en clair dans le fichier `.env` local. En production, il faudrait un gestionnaire de secrets (Vault, ou celui du fournisseur cloud).
- La connexion application → base n'est pas chiffrée (pas de TLS). Le risque est limité car elle reste sur un réseau Docker privé.
- Sauvegarde et restauration sont manuelles (`pg_dump`/`psql`), sans planification ni stockage externe.
- Une seule instance de l'application, sans répartition de charge.
- Le script de scénarios est en bash : sous Windows, il nécessite Git Bash ou WSL.
- L'image n'a pas été passée dans un scanner de vulnérabilités (Trivy, Docker Scout).

---

## Module C3 · Cybersécurité / Monitoring IA

### Choix techniques et alternatives écartées

| Choix | Pourquoi | Alternative écartée et raison |
|---|---|---|
| Distinguer **observations / hypothèses / mesures** | Demandé par le sujet. Cela évite de présenter une supposition comme un fait (exemple : on ne sait pas si l'IA a obéi à e44). | Lister directement les risques : plus court, mais mélange faits et suppositions. |
| Notation **Impact × Vraisemblance** de 1 à 4 | Simple, explicable et suffisante pour classer 7 risques. | Méthodes complètes (EBIOS RM, CVSS) : trop lourdes pour 8 lignes de logs. |
| 7 risques au lieu de 5 | Les 6 thèmes imposés sont couverts. « Droits serveur » se décompose en deux problèmes distincts : rôle de base de données administrateur (R2) et autorisation seulement dans l'interface (R3). | Regrouper R2 et R3 : on perdrait la distinction base de données / API. |
| Règle d'alerte **en Python, sans dépendance** | Déterministe, testable avec pytest, lisible par le correcteur et exécutable sans infrastructure (« aucune infrastructure réelle » dans le sujet). | Règle Sigma, ou requête dans un SIEM (Elastic, Splunk) : nécessite une infrastructure. |
| Seuil A1 : **3 rejets en 60 s par source** | Un échec isolé est normal. 3 en une minute depuis la même source correspondent au signal observé (e41-e43) et méritent une enquête. | Seuil à 1 : trop de fausses alertes. Seuil à 10 : rate l'incident du sujet. |
| Logs sans secret : **liste blanche puis masquage** | La liste blanche empêche par construction d'écrire les en-têtes. Le masquage rattrape un secret glissé dans un champ autorisé. | Masquage seul : on ne peut pas prévoir tous les formats de secrets. |
| Schéma en **Mermaid** | Il s'affiche directement sur GitHub et reste versionné en texte. | Image dessinée à la main : impossible à relire dans un diff. |
| Dossier en Markdown **et** en PDF | Le Markdown se lit sur GitHub. Le PDF prouve la limite « 3 à 5 pages » (il en fait 5). | Un seul format : soit illisible sur GitHub, soit pagination invérifiable. |

### Preuves
- Exécution de la règle sur les logs du sujet et sur les exemples : `preuves/c3/execution_regle_alerte.txt`. Sur les logs du sujet, elle produit exactement 2 alertes : A1 (`partner-A`) et A2 (`d9`).
- 10 tests : `c3-cybersecurite/tests/test_alerte.py`. Ils couvrent les exemples qui déclenchent et ceux qui ne déclenchent pas, le déterminisme et le masquage.

### Limites
- L'analyse porte sur 8 lignes de logs : les hypothèses (H1 à H5) ne peuvent pas être confirmées sans accès à un système réel.
- Les mesures de la section 2 du dossier (HMAC des webhooks, rôles PostgreSQL, limite de débit, prompt durci) sont **décrites avec leur vérification**, mais **pas implémentées** : le sujet exclut toute infrastructure réelle.
- La règle analyse un fichier après coup, pas un flux en temps réel.
- Le masquage repose sur des motifs connus : un secret au format inhabituel pourrait passer. C'est pourquoi la liste blanche reste la protection principale.
- e44 (injection IA) n'a pas de règle d'alerte dédiée : il est traité par le tag `a_revoir` et la revue humaine (limite expliquée en section 4.3 du dossier).
