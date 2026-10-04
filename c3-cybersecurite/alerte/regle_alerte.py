"""Règles d'alerte DÉTERMINISTES sur les logs MATRiCE.

Déterministe = mêmes logs en entrée, toujours les mêmes alertes en sortie :
seuils fixes, aucune IA, aucun hasard. Une alerte peut donc être expliquée
et rejouée par un correcteur.

Usage (depuis c3-cybersecurite/) :
    python -m alerte.regle_alerte donnees/logs_sujet.log
"""
import shlex
import sys
from collections import defaultdict
from datetime import datetime

# --- Règle A1 : rafale de signatures webhook invalides --------------------
# Déclenche si UNE MÊME source envoie AU MOINS 3 webhooks rejetés pour
# signature invalide (status=401 reason=bad_signature) en 60 secondes ou moins.
# Pourquoi 3 en 60 s : 1 échec isolé peut être une erreur ponctuelle ; une rafale
# indique une rotation de secret ratée ou une tentative de falsification/rejeu.
A1_SEUIL = 3
A1_FENETRE_S = 60

# --- Règle A2 : synchronisation en échec ----------------------------------
# Déclenche dès qu'une livraison passe en state=quarantine : toutes les
# tentatives ont échoué et plus rien ne sera retenté automatiquement.


def lire_ligne(ligne: str) -> dict | None:
    """Transforme 'HH:MM:SS cle=valeur cle="valeur avec espaces"' en dictionnaire."""
    try:
        morceaux = shlex.split(ligne)      # shlex gère les valeurs entre guillemets
    except ValueError:                     # guillemet non fermé : découpage simple plutôt que perdre la ligne
        morceaux = ligne.split()
    if not morceaux or "=" not in ligne:
        return None                        # ligne vide ou ligne de configuration
    try:
        heure = datetime.strptime(morceaux[0], "%H:%M:%S")
    except ValueError:
        return None
    champs = dict(m.split("=", 1) for m in morceaux[1:] if "=" in m)
    champs["_heure"] = heure
    return champs


def regle_a1_rafale_signature(evenements: list[dict]) -> list[dict]:
    alertes = []
    rejets_par_source = defaultdict(list)
    for ev in evenements:
        if (ev.get("component") == "webhook" and ev.get("status") == "401"
                and ev.get("reason") == "bad_signature"):
            rejets = rejets_par_source[ev.get("source", "inconnue")]
            rejets.append(ev)
            # On ne garde que les rejets des 60 dernières secondes.
            while (ev["_heure"] - rejets[0]["_heure"]).total_seconds() > A1_FENETRE_S:
                rejets.pop(0)
            if len(rejets) == A1_SEUIL:    # == : une seule alerte par rafale
                alertes.append({
                    "regle": "A1_RAFALE_SIGNATURE_INVALIDE",
                    "gravite": "haute",
                    "source": ev.get("source"),
                    "evenements": [r.get("event") for r in rejets],
                    "message": f"{A1_SEUIL} signatures invalides en <= {A1_FENETRE_S}s depuis {ev.get('source')} : à investiguer",
                })
    return alertes


def regle_a2_synchro_en_echec(evenements: list[dict]) -> list[dict]:
    return [
        {
            "regle": "A2_SYNCHRONISATION_EN_ECHEC",
            "gravite": "moyenne",
            "livraison": ev.get("delivery"),
            "tentatives": ev.get("attempt"),
            "message": f"Livraison {ev.get('delivery')} en quarantaine après {ev.get('attempt')} tentatives (dernier statut {ev.get('status')})",
        }
        for ev in evenements
        if ev.get("component") == "delivery" and ev.get("state") == "quarantine"
    ]


def analyser(lignes: list[str]) -> list[dict]:
    evenements = [ev for ev in (lire_ligne(l) for l in lignes) if ev]
    return regle_a1_rafale_signature(evenements) + regle_a2_synchro_en_echec(evenements)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage : python -m alerte.regle_alerte <fichier.log>")
        return 2
    with open(sys.argv[1], encoding="utf-8") as f:
        alertes = analyser(f.readlines())
    for a in alertes:
        print(f"[ALERTE {a['gravite'].upper()}] {a['regle']} : {a['message']}")
    if not alertes:
        print("Aucune alerte.")
    return 1 if alertes else 0             # code de sortie != 0 : utilisable en CI ou cron


if __name__ == "__main__":
    sys.exit(main())
