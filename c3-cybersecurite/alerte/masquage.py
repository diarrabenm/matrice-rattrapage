"""Logs sans secret : masque les valeurs sensibles AVANT l'écriture d'une ligne de log.

Deux protections complémentaires :
1. liste blanche : seuls les champs utiles au diagnostic sont conservés ;
2. masquage : tout motif qui ressemble à un secret est remplacé par "***",
   au cas où un secret se glisserait dans un champ autorisé.
"""
import re

# Champs autorisés dans un log (tout le reste est supprimé).
CHAMPS_AUTORISES = {
    "component", "event", "delivery", "attempt", "status", "reason",
    "source", "state", "latency_ms", "tag", "method", "path",
}

# Motifs de secrets courants. Chaque motif garde le nom du champ (groupe 1)
# et remplace uniquement la valeur.
MOTIFS_SECRETS = [
    re.compile(r"(authorization\s*[:=]\s*)(?:bearer\s+|basic\s+)?\S+", re.IGNORECASE),
    re.compile(r"(cookie\s*[:=]\s*)\S+", re.IGNORECASE),
    re.compile(r"(x-signature\s*[:=]\s*)\S+", re.IGNORECASE),
    re.compile(r"((?:password|passwd|secret|token|api_key|apikey)\s*[:=]\s*)\S+", re.IGNORECASE),
    re.compile(r"(postgres(?:ql)?://[^:/\s]+:)[^@\s]+"),  # mot de passe dans une URL de connexion
]


def masquer(texte: str) -> str:
    """Remplace la valeur de chaque secret détecté par ***."""
    for motif in MOTIFS_SECRETS:
        texte = motif.sub(r"\1***", texte)
    return texte


def filtrer_champs(champs: dict) -> dict:
    """Ne garde que les champs de la liste blanche, puis masque leurs valeurs."""
    return {cle: masquer(str(valeur)) for cle, valeur in champs.items() if cle in CHAMPS_AUTORISES}


def ligne_de_log(heure: str, champs: dict) -> str:
    """Construit une ligne au format du sujet : 'HH:MM:SS cle=valeur ...'."""
    propres = filtrer_champs(champs)
    return heure + " " + " ".join(f"{cle}={valeur}" for cle, valeur in propres.items())
