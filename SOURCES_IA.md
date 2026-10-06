# Sources et usages de l'IA

## Usage de l'IA

J'ai piloté ce projet de bout en bout et j'ai utilisé l'IA, puisque le sujet l'autorise.

## Requêtes représentatives

* « Respecte les consignes et fais exactement ce qui est demandé dans le cahier des charges. »
* « Lance l'application dans mon navigateur. »
* « Fais la démonstration dans le terminal » (arrêt de la base, puis `/health` et `/ready`).

### Adaptations et corrections apportées en cours de route

| Problème constaté                                                                                                         | Correction                                                                                |
| ------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| La règle `*.log` du `.gitignore` excluait les logs du sujet et les exemples : les tests C3 échouaient sur un clone propre | Exceptions ajoutées dans `.gitignore` afin de conserver les fichiers nécessaires au sujet |
| Le dossier C3 faisait 6 pages, alors que le sujet impose 3 à 5                                                            | Rédaction resserrée sans retirer d'exigence du sujet : 5 pages                            |
| Le schéma des frontières de confiance présentait la validation de la réponse dans le mauvais sens                         | Flèche corrigée afin de respecter le fonctionnement attendu                               |
| Une ligne de log avec un guillemet non fermé aurait été perdue par l'analyseur                                            | Repli sur un découpage simple plutôt que d'ignorer la ligne                               |
| Les scripts risquaient d'avoir des fins de ligne Windows, ce qui casse bash                                               | Ajout de `.gitattributes` afin d'imposer les fins de ligne LF                             |
| `/health` devait rester tel que demandé par le sujet sans tester la base                                                  | Ajout d'une route séparée `/ready`, comme prévu pour effectuer la vérification séparément |

## Vérifications effectuées

* **Tests automatisés** : 4 tests (C4) et 10 tests (C3), tous réussis.
* **Exécution réelle** des 4 scénarios Docker. Les traces dans `preuves/c4/` correspondent à la sortie brute des commandes.
* **Démonstration en direct** de la différence entre conteneur démarré et service disponible : avec la base arrêtée, `/health` renvoie `200` tandis que `/ready` renvoie `503`.
* **Clone propre** du dépôt depuis GitHub, puis relance des tests et scénarios afin de vérifier que le projet peut être exécuté sans fichier manquant.
* **Recherche du mot de passe** dans l'image Docker : 0 occurrence.
* **Comptage des pages** du dossier C3 sur le PDF généré : 5 pages.
* **Contrôle du dépôt** : aucun `.env`, `.venv`, `node_modules` ni secret versionné.

## Autres sources

Aucun code n'a été copié depuis une autre source.

Documentations de référence utilisées pour vérifier les notions employées :

* Docker : documentation de Compose (`depends_on`, `healthcheck`, `secrets`) et bonnes pratiques Dockerfile ;
* Image officielle PostgreSQL sur Docker Hub (`POSTGRES_PASSWORD_FILE`, `pg_isready`) ;
* FastAPI : documentation officielle.
