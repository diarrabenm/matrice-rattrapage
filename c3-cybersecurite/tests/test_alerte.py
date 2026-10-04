from pathlib import Path

from alerte.masquage import ligne_de_log, masquer
from alerte.regle_alerte import analyser

RACINE = Path(__file__).resolve().parent.parent


def alertes_du_fichier(chemin: str) -> list[dict]:
    return analyser((RACINE / chemin).read_text(encoding="utf-8").splitlines())


def regles(alertes: list[dict]) -> list[str]:
    return [a["regle"] for a in alertes]


# --- Règle A1 : rafale de signatures invalides ---------------------------

def test_a1_declenche_sur_les_3_rejets_de_partner_a():
    alertes = alertes_du_fichier("exemples/a1_declenche.log")
    assert regles(alertes) == ["A1_RAFALE_SIGNATURE_INVALIDE"]
    assert alertes[0]["source"] == "partner-A"
    assert alertes[0]["evenements"] == ["e41", "e42", "e43"]


def test_a1_ne_declenche_pas():
    # 3 rejets étalés sur plus de 60 s, sources différentes, autre motif de 401, succès.
    assert alertes_du_fichier("exemples/a1_ne_declenche_pas.log") == []


def test_a1_une_seule_alerte_pour_une_rafale_de_5():
    lignes = [f"10:00:0{i} component=webhook event=e{i} status=401 reason=bad_signature source=x" for i in range(5)]
    assert regles(analyser(lignes)) == ["A1_RAFALE_SIGNATURE_INVALIDE"]


# --- Règle A2 : synchronisation en échec ---------------------------------

def test_a2_declenche_sur_d9_en_quarantaine():
    alertes = alertes_du_fichier("exemples/a2_declenche.log")
    assert regles(alertes) == ["A2_SYNCHRONISATION_EN_ECHEC"]
    assert alertes[0]["livraison"] == "d9"
    assert alertes[0]["tentatives"] == "3"


def test_a2_ne_declenche_pas_si_la_livraison_finit_par_reussir():
    assert alertes_du_fichier("exemples/a2_ne_declenche_pas.log") == []


# --- Logs complets du sujet -----------------------------------------------

def test_logs_du_sujet_declenchent_a1_et_a2():
    alertes = alertes_du_fichier("donnees/logs_sujet.log")
    assert sorted(regles(alertes)) == ["A1_RAFALE_SIGNATURE_INVALIDE", "A2_SYNCHRONISATION_EN_ECHEC"]


def test_le_resultat_est_deterministe():
    assert alertes_du_fichier("donnees/logs_sujet.log") == alertes_du_fichier("donnees/logs_sujet.log")


# --- Logs sans secret -------------------------------------------------------

def test_masque_les_en_tetes_et_parametres_sensibles():
    brut = ("Authorization: Bearer eyJhbGciOi.secret Cookie: session=abc123 "
            "X-Signature: sha256=deadbeef password=hunter2 token=t0k3n "
            "postgresql://matrice:motdepasse@db:5432/matrice")
    propre = masquer(brut)
    for secret in ["eyJhbGciOi.secret", "abc123", "deadbeef", "hunter2", "t0k3n", "motdepasse"]:
        assert secret not in propre
    assert "Authorization: ***" in propre
    assert "postgresql://matrice:***@db:5432/matrice" in propre


def test_ne_modifie_pas_une_ligne_sans_secret():
    ligne = "component=delivery delivery=d10 attempt=1 status=200 latency_ms=160"
    assert masquer(ligne) == ligne


def test_liste_blanche_supprime_les_champs_non_autorises():
    ligne = ligne_de_log("10:00:00", {
        "component": "webhook", "event": "e41", "status": "401",
        "headers": "Authorization: Bearer abc", "body": "{...}",
    })
    assert ligne == "10:00:00 component=webhook event=e41 status=401"
