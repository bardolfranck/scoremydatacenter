# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Un site MIS HORS SERVICE : sa note est une archive datée, et il sort du parc en activité.

🔴 CE QUI S'EST PASSÉ LE 2026-11-07. Huit fiches servies portaient « (closed) » ou
« ** INACTIVE ** » dans leur NOM, une note, et `identity.project_status: "operational"` —
nous affirmions donc, dans la balise que Google montre, que huit sites fermés étaient en
exploitation. Trouvé en cherchant un marqueur dans les titres du site construit, pas dans le
code. La contre-épreuve inverse (un statut qui dit fermé sans que le nom le dise) rendait 0,
pour une raison simple : AUCUNE valeur de fermeture n'existait dans l'énumération. On ne
pouvait pas dire « fermé ».

DÉCISION DE FRANCK, le jour même : on ne retire pas la page. « Fermé mais a existé, donc on
garde la note. Par contre on annonce "site fermé" dans la fiche et dans le statut du site. »

CE QUE CES TESTS FIGENT, et chacun garde une chose différente :
· le VOCABULAIRE : `decommissioned` est servi, mais ce n'est ni un stade du pipeline (il ne
  mène à rien) ni `unknown` (on sait, justement) ;
· la DATE : une note d'archive sans millésime se lit comme une note d'aujourd'hui. Le gate
  refuse `decommissioned` sans `vintage.decommissioned_year` ;
· l'EXCLUSION du parc en activité — vitrine et médiane — qu'on croit acquise « parce que ces
  calculs exigent operational ». Une garantie qu'on croit acquise sans l'avoir testée est un
  fantôme [[figer-par-test-revele-les-fantomes]] : ici elle existe, et maintenant elle est
  tenue, y compris si quelqu'un élargit un filtre demain.
"""

import json
from pathlib import Path

from engine.showcase import build_showcase
from engine.core import datacenter_paths, load_json
from engine.validate import (DETTE_NOM_CONTREDIT_STATUT, hors_service_gate,
                             nom_et_statut_gate)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA = REPO_ROOT / "data" / "schema" / "datacenter.schema.json"
STATUTS_TS = REPO_ROOT / "site" / "src" / "content" / "statuts.ts"
FICHE_TS = REPO_ROOT / "site" / "src" / "content" / "fiche.ts"
PORTRAIT_TS = REPO_ROOT / "site" / "src" / "content" / "portrait.ts"
DC_FICHE = REPO_ROOT / "site" / "src" / "components" / "DcFiche.astro"
PORTRAIT = REPO_ROOT / "site" / "src" / "components" / "SitePortrait.astro"
BANDEAU = REPO_ROOT / "site" / "src" / "components" / "BandeauHorsService.astro"

CHAINES = ("horsServiceTitre", "horsServiceAnnee", "horsServiceSansAnnee",
           "horsServiceNote", "horsServiceDossier")


def _dc(dc_id, status="operational", annee=None, lat=48.0, lon=2.0):
    identity = {"name": dc_id, "country": "FR", "project_status": status,
                "coordinates": {"lat": lat, "lon": lon}}
    if annee is not None:
        identity["vintage"] = {"decommissioned_year": annee}
    return {"id": dc_id, "identity": identity, "indicators": [],
            "publication": {}, "contestation": None, "score_history": []}


def _result(score, grade="C"):
    pillars = {f"p{i}": {"grade": grade} for i in range(4)}
    pillars["p4"] = {"grade": "insufficient_data"}
    return {"grades": {"site": {"grade": grade, "score": score}}, "pillars": pillars}


def _ecris(tmp_path: Path, dcs: list[dict]) -> Path:
    d = tmp_path / "datacenters"
    d.mkdir(parents=True)
    for dc in dcs:
        (d / f"{dc['id']}.json").write_text(json.dumps(dc), encoding="utf-8")
    return tmp_path


# ─── le vocabulaire ────────────────────────────────────────────────────────────────────────

def test_le_schema_accepte_la_fermeture_et_son_annee():
    s = json.loads(SCHEMA.read_text(encoding="utf-8"))
    ident = s["properties"]["identity"]["properties"]
    assert "decommissioned" in ident["project_status"]["enum"], (
        "sans valeur de fermeture dans l'énumération, une fiche ne peut PAS dire qu'elle est "
        "fermée — c'est ce qui a produit huit fiches « operational » au nom explicite"
    )
    annee = ident["vintage"]["properties"]["decommissioned_year"]
    assert annee["type"] == "integer" and annee["minimum"] >= 1990


def test_hors_service_nest_ni_un_projet_ni_un_statut_inconnu():
    source = STATUTS_TS.read_text(encoding="utf-8")
    pipeline = source.split("export const PIPELINE =", 1)[1].split("\n", 1)[0]
    statuts = source.split("export const STATUTS =", 1)[1].split("\n", 1)[0]
    assert "decommissioned" not in pipeline, (
        "`decommissioned` dans PIPELINE ferait parler un site fermé comme un chantier — "
        "c'est exactement la confusion « pas operational = est un projet » déjà payée"
    )
    assert "decommissioned" in statuts, "le statut doit être dans le vocabulaire SERVI"
    assert "export function horsService" in source


def test_les_trois_langues_disent_la_fermeture():
    """Chaque chaîne est dans CHACUN des trois blocs — pas trois fois dans le même.

    🔴 Compter les occurrences ne prouve rien : trois déclarations peuvent tenir dans le seul
    bloc français, et la page néerlandaise servirait alors `undefined`. On découpe donc les
    blocs sur leur table de statut (qui est, elle, gardée par le test de parité) et on exige
    la chaîne DANS chaque tranche. C'est la troisième langue qui révèle ce genre de binaire
    [[troisieme-langue-revele-les-binaires]].
    """
    for fichier in (FICHE_TS, PORTRAIT_TS):
        source = fichier.read_text(encoding="utf-8")
        # Les trois blocs commencent chacun à leur table de statut, dans l'ordre fr, en, nl.
        debuts = [i for i, l in enumerate(source.splitlines())
                  if "status: {" in l and "decommissioned:" in l]
        assert len(debuts) == 3, (
            f"{fichier.name} : {len(debuts)} table(s) de statut trouvée(s) au lieu de 3 — "
            "le découpage par langue ne tient plus, le test mentirait"
        )
        lignes = source.splitlines()
        bornes = debuts + [len(lignes)]
        for n, (i, j) in enumerate(zip(bornes, bornes[1:])):
            tranche = "\n".join(lignes[i:j])
            langue = ("fr", "en", "nl")[n]
            for clef in CHAINES:
                assert f"{clef}:" in tranche, (
                    f"{fichier.name} : {clef} manque au bloc « {langue} » — cette page "
                    "servirait une valeur vide à la place du fait de fermeture"
                )


def test_le_bandeau_est_declare_une_fois_et_servi_par_les_deux_surfaces():
    """Deux surfaces, un seul fait : la fiche technique ET le portrait, un seul composant.

    🔴 Franck, 2026-11-07 : « à poser sur site portrait et fiche tech, tout en haut en mode
    impossible de ne pas voir ». Deux blocs copiés auraient divergé au premier changement de
    formulation [[liste-a-deux-endroits-ment]] ; et un bandeau posé dans la colonne latérale
    de la fiche n'est pas « tout en haut ». Le composant est donc monté AVANT la grille.
    """
    bandeau = BANDEAU.read_text(encoding="utf-8")
    assert "horsService(statut)" in bandeau, "le bandeau décide depuis le vocabulaire commun"

    for fichier, ancre in ((DC_FICHE, '<article class="fiche">'),
                           (PORTRAIT, '<header class="pt-head">')):
        source = fichier.read_text(encoding="utf-8")
        assert "<BandeauHorsService" in source, f"{fichier.name} ne monte pas le bandeau"
        assert source.index("<BandeauHorsService") < source.index(ancre), (
            f"{fichier.name} : le bandeau doit précéder {ancre} — « tout en haut », "
            "pas au milieu de la page"
        )
        assert 'project_status === "decommissioned"' not in source, (
            f"{fichier.name} compare le code en dur : la table repasse à deux endroits"
        )


def test_le_dossier_de_fermeture_est_un_lien_verifiable():
    """Le lien vers le dossier administratif est servi — et seulement s'il existe.

    « Ce qui serait top serait un lien url vers le dossier administratif qui prouve sa
    fermeture […] si tu as pas ça c'est pas bloquant » (Franck, 2026-11-07). Donc : servi
    quand il existe, jamais inventé, et son absence ne fait pas disparaître la fermeture.
    """
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    champ = schema["properties"]["identity"]["properties"]["vintage"]["properties"]
    assert champ["decommissioned_source"]["$ref"] == "#/$defs/source", (
        "le dossier doit être un objet source complet (titre, url, date d'accès), "
        "pas une phrase : son url est servie"
    )
    bandeau = BANDEAU.read_text(encoding="utf-8")
    assert "decommissioned_source" in bandeau
    assert 'target="_blank"' in bandeau and 'rel="noopener"' in bandeau
    # Le repli sur l'archive existe (lien mort), et le lien reste facultatif.
    assert "archived_url" in bandeau
    assert "{lien && (" in bandeau, (
        "sans adresse, le bandeau doit dire le fait et se taire sur la preuve — "
        "ni lien inventé, ni fermeture masquée"
    )


# ─── la date de l'archive ──────────────────────────────────────────────────────────────────

def test_le_gate_refuse_une_archive_sans_millesime(tmp_path):
    racine = _ecris(tmp_path, [_dc("fr-ferme", status="decommissioned")])
    problemes = hors_service_gate(racine)
    assert problemes, "une note d'archive sans année se lit comme une note d'aujourd'hui"
    assert "fr-ferme" in problemes[0] and "decommissioned_year" in problemes[0]


def test_le_gate_accepte_une_archive_datee(tmp_path):
    racine = _ecris(tmp_path, [_dc("fr-ferme", status="decommissioned", annee=2021)])
    assert hors_service_gate(racine) == []


def test_le_gate_ne_juge_que_les_fiches_fermees(tmp_path):
    """Un site en service n'a pas d'année de fermeture : le gate n'a rien à lui dire."""
    racine = _ecris(tmp_path, [_dc("fr-en-service"), _dc("fr-annonce", status="announced")])
    assert hors_service_gate(racine) == []


# ─── l'exclusion du parc en activité ───────────────────────────────────────────────────────

def test_un_site_hors_service_nest_jamais_la_vitrine():
    """La page d'accueil montre le site MÉDIAN du parc en activité, pas une archive."""
    dcs = {f"fr-{i:02d}": _dc(f"fr-{i:02d}") for i in range(5)}
    results = {f"fr-{i:02d}": _result(s)
               for i, s in enumerate([10.0, 30.0, 60.0, 85.0, 95.0])}
    # Le site fermé est placé PILE sur la médiane : s'il n'était pas exclu, il gagnerait.
    dcs["fr-ferme"] = _dc("fr-ferme", status="decommissioned", annee=2019, lat=48.1)
    results["fr-ferme"] = _result(60.0)
    out = build_showcase(dcs, results)
    assert "fr-ferme" not in [c["id"] for c in out["demo_candidates"]], (
        "un site mis hors service n'a plus d'acceptabilité à montrer : il a une histoire"
    )


def test_la_mediane_est_celle_du_parc_en_activite():
    """L'étalon du « site le plus ordinaire » ne mélange pas hier et aujourd'hui.

    Ce test a trouvé un vrai fantôme : l'exclusion de la DÉMO existait, celle de l'ÉTALON
    non. Deux archives basses tiraient la médiane vers le bas, donc désignaient un autre
    site comme « le plus ordinaire » du parc en activité.
    """
    dcs = {f"fr-{i:02d}": _dc(f"fr-{i:02d}") for i in range(3)}
    results = {f"fr-{i:02d}": _result(s) for i, s in enumerate([40.0, 50.0, 60.0])}
    sans_archives = build_showcase(dcs, results)["median_site_score"]
    for j, bas in enumerate([5.0, 7.0]):
        did = f"fr-arch{j}"
        dcs[did] = _dc(did, status="decommissioned", annee=2018, lat=48.5 + j)
        results[did] = _result(bas)
    avec_archives = build_showcase(dcs, results)["median_site_score"]
    assert avec_archives == sans_archives == 50.0, (
        f"la médiane a bougé de {sans_archives} à {avec_archives} : des notes d'archive "
        "pèsent sur l'étalon du parc en activité"
    )


def test_le_mur_montre_le_corpus_archives_comprises():
    """Asymétrie VOULUE, et nommée : la règle déclarée du mur est « montrer le corpus ».

    Le mur n'élit personne — il dit l'ampleur de ce qu'on a mesuré, et un site fermé en fait
    partie. On ne rétrécit pas une règle de Franck en passant. Si cela doit changer, ce sera
    une décision, pas un effet de bord de celle du 2026-11-07.
    """
    dcs = {"fr-00": _dc("fr-00"),
           "fr-ferme": _dc("fr-ferme", status="decommissioned", annee=2019)}
    results = {"fr-00": _result(50.0), "fr-ferme": _result(60.0)}
    out = build_showcase(dcs, results)
    assert "fr-ferme" in out["wall_candidates"]

# ─── le nom ne peut pas affirmer ce que le statut refuse ────────────────────────────────────

def _dc_nomme(dc_id, nom, status="unknown"):
    return {"id": dc_id, "identity": {"name": nom, "country": "FR",
                                      "project_status": status,
                                      "coordinates": {"lat": 48.0, "lon": 2.0}},
            "indicators": [], "publication": {}, "contestation": None, "score_history": []}


def test_un_nom_qui_dit_ferme_sur_un_statut_qui_ne_le_dit_pas_est_refuse(tmp_path):
    """Le titre affirme « inactive », le champ dit « stade non établi » : l'un des deux est faux."""
    racine = _ecris(tmp_path, [_dc_nomme("fr-x", "ACME DATA CENTER ** INACTIVE **")])
    problemes = nom_et_statut_gate(racine)
    assert problemes and "fr-x" in problemes[0]
    # Et le message dit les DEUX issues honnêtes, jamais « mets une année ».
    assert "nettoyer le nom" in problemes[0] and "inventée" in problemes[0]


def test_le_gate_se_tait_quand_les_deux_surfaces_concordent(tmp_path):
    """`decommissioned` + un nom qui dit la fermeture : rien à redire."""
    racine = _ecris(tmp_path, [
        _dc_nomme("fr-ok", "ACME DC (closed)", status="decommissioned"),
        _dc_nomme("fr-propre", "ACME DC", status="unknown"),
        _dc_nomme("fr-vivant", "ACME DC", status="operational"),
    ])
    assert nom_et_statut_gate(racine) == []


def test_la_dette_nommee_est_reelle_et_dans_cet_etat():
    """Une dette qui ne correspond plus à rien désarme le gate en silence.

    🔴 Cinq fiches sont exemptées par leur nom (2026-11-07) : noms de registre US/DE qui
    affirment « inactive » alors qu'aucune source ne date la fermeture. Si l'une est nettoyée
    ou sourcée, elle doit SORTIR de la liste — sinon la liste protège un cas qui n'existe plus
    et le prochain défaut passera sous son couvert.
    """
    CAL = REPO_ROOT.parent / "smdc-newsroom" / "calibration"
    if not CAL.is_dir():
        return  # dépôt privé absent : ce test ne peut rien dire, il se tait au lieu de mentir
    par_id = {p.stem: p for p in datacenter_paths(CAL)}
    assert len(par_id) > 1000, f"corpus de {len(par_id)} fiches : trop petit pour conclure"
    perimes, corriges = [], []
    for dc_id in sorted(DETTE_NOM_CONTREDIT_STATUT):
        path = par_id.get(dc_id)
        if path is None:
            perimes.append(dc_id)
            continue
        ident = load_json(path)["identity"]
        nom = (ident.get("name") or "").lower()
        dit_ferme = any(m in nom for m in ("inactive", "closed", "decommission"))
        if not dit_ferme or ident.get("project_status") == "decommissioned":
            corriges.append(dc_id)
    assert not perimes, f"dette périmée, ces fiches n'existent plus : {perimes}"
    assert not corriges, (
        "ces fiches sont réglées — retirez-les de DETTE_NOM_CONTREDIT_STATUT, sinon la liste "
        f"couvre le vide : {corriges}"
    )
