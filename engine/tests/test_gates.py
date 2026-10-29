# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Every gate must actually block: each test breaks the data one way and
asserts the right gate fires with an explicit message."""

import json
import re
from datetime import date

from engine.core import DATA_DIR, REPO_ROOT, load_methodology, load_datacenters
from engine.scoring import history_entry_fields, score_datacenter
from engine.score import _changed
from engine.validate import STALE_METHODOLOGY_REMEDY, run_gates

TODAY = date(2026, 7, 5)

ALPHA = "datacenters/zz-test-alpha.json"
BETA = "datacenters/zz-test-beta.json"
# LE NOM DE LA MÉTHODO ACTIVE NE S'ÉCRIT PAS EN DUR. GATE 5 garantit qu'il n'y en a qu'une
# dans data/methodology/ : on la DÉDUIT. Codé en dur, chaque version coupait la moitié des
# tests de gate en FileNotFoundError — donc au moment précis où le gel d'une méthodo demande
# le plus de garanties, les gates se taisaient (constaté au passage en v0.3.0, 2026-10-06).
METH = f"methodology/{sorted(p.name for p in (DATA_DIR / 'methodology').glob('v*.json'))[0]}"


def _ind(doc, indicator_id):
    return next(e for e in doc["indicators"] if e["id"] == indicator_id)


def test_repository_data_passes_all_gates():
    assert run_gates() == []


def test_gate1_missing_source(data_copy):
    root, edit = data_copy
    edit(ALPHA, lambda d: _ind(d, "E1").pop("source"))
    assert any("GATE 1" in p and "source" in p for p in run_gates(root, TODAY))


def test_gate1_verdict_on_t1(data_copy):
    root, edit = data_copy
    edit(ALPHA, lambda d: _ind(d, "T1").update(value="poor consultation"))
    assert any("GATE 1" in p for p in run_gates(root, TODAY))


def test_gate1_undeclared_missing_indicator(data_copy):
    root, edit = data_copy
    edit(ALPHA, lambda d: d["indicators"].remove(_ind(d, "E5")))
    assert any("status: missing" in p for p in run_gates(root, TODAY))


def test_gate2_declarative_measured_without_verification(data_copy):
    root, edit = data_copy
    edit(ALPHA, lambda d: _ind(d, "E4").update(status="measured"))
    problems = run_gates(root, TODAY)
    # caught structurally by the schema (gate 1) and semantically by gate 2
    assert any("verification_source" in p for p in problems)


def test_gate3_broken_weights(data_copy):
    root, edit = data_copy
    edit(METH, lambda m: m["pillars"][0].update(weight=0.5))
    assert any("GATE 3" in p and "sum" in p for p in run_gates(root, TODAY))


def test_gate3_ethical_lock_rejects_vulnerability_scoring_higher(data_copy):
    root, edit = data_copy

    def reward_vulnerability(m):
        l1 = next(i for i in m["indicators"] if i["id"] == "L1")
        l1["normalization"]["categories"]["sensitive"] = 95  # fragile municipality scores best

    edit(METH, reward_vulnerability)
    assert any("GATE 3" in p and "ethical lock" in p for p in run_gates(root, TODAY))


def test_gate3_vulnerability_order_must_cover_categories(data_copy):
    root, edit = data_copy

    def broken_order(m):
        l1 = next(i for i in m["indicators"] if i["id"] == "L1")
        l1["vulnerability_order"] = ["strong_fit", "sensitive"]

    edit(METH, broken_order)
    assert any("GATE 3" in p and "vulnerability_order" in p for p in run_gates(root, TODAY))


# Gate 4 (prior-notice hold) was removed on 2026-07-15 (legal review): grades publish
# directly and the permanent response space replaced the pre-publication window.


def test_gate5_real_dc_against_draft_methodology(data_copy):
    root, edit = data_copy
    edit(ALPHA, lambda d: d.update(id="fr-test-alpha"))
    (root / "datacenters" / "zz-test-alpha.json").rename(root / "datacenters" / "fr-test-alpha.json")
    assert any("GATE 5" in p and "draft" in p for p in run_gates(root, TODAY))


def test_gate5_stale_methodology_version(data_copy):
    # La TÊTE du journal (l'état servi), pas l'entrée [0] : voir le test ci-dessous.
    root, edit = data_copy
    edit(ALPHA, lambda d: d["score_history"][-1].update(methodology_version="0.0.9"))
    assert any("GATE 5" in p and "methodology_change" in p for p in run_gates(root, TODAY))


def test_journal_gate_revision_without_rationale(data_copy):
    root, edit = data_copy

    def add_unjustified_revision(d):
        entry = dict(d["score_history"][0])
        entry.pop("rationale")
        entry["event"] = "data_correction"
        d["score_history"].append(entry)

    edit(ALPHA, add_unjustified_revision)
    assert any("JOURNAL GATE" in p and "rationale" in p for p in run_gates(root, TODAY))


def test_journal_gate_detects_unrecorded_grade_change():
    methodology = load_methodology()
    alpha = load_datacenters()["zz-test-alpha"]
    assert _changed(alpha, methodology) is None  # journal is in sync
    alpha["score_history"][-1]["grades"]["site"] = "A"  # pretend the record says A
    assert _changed(alpha, methodology) is not None  # engine refuses the silent mismatch


def test_history_entry_fields_shape(methodology):
    alpha = load_datacenters()["zz-test-alpha"]
    fields = history_entry_fields(score_datacenter(alpha, methodology), methodology)
    assert fields == {
        "methodology_version": methodology["version"],
        "grades": {"site": "B", "project_process": "C"},
        "confidence": "high",
    }


def test_gate9_l2_measured_on_aggregator_power(data_copy):
    # memo 2026-07-19: an aggregator MW is a third-party claim — L2 may not stay 'measured' on it.
    root, edit = data_copy
    edit(ALPHA, lambda d: _ind(d, "L2")["source"].update(
        title="puissance 7.0 MW (DCWatch ODbL, export 7dd5b5e9)"))
    assert any("GATE 9" in p and "non-regulatory" in p for p in run_gates(root, TODAY))


def test_gate9_l2_measured_on_regulatory_power_passes(data_copy):
    root, edit = data_copy
    edit(ALPHA, lambda d: _ind(d, "L2")["source"].update(
        title="puissance 7.0 MW (EED register RVO, INSTALLED)"))
    assert not any("GATE 9" in p for p in run_gates(root, TODAY))


def test_gate9_lenient_on_unattributed_prose(data_copy):
    # 'unknown' is never silently promoted NOR accused — fictional fixtures stay green.
    root, edit = data_copy
    edit(ALPHA, lambda d: _ind(d, "L2")["source"].update(title="Fictional census (test)"))
    assert not any("GATE 9" in p for p in run_gates(root, TODAY))


def test_gate10_estimated_power_requires_estimated_l2(data_copy):
    # 1c (2026-07-27): a model-derived MW must be tagged end-to-end — L2 fed by our own
    # estimate may not be served as a fact.
    root, edit = data_copy
    edit(ALPHA, lambda d: d["identity"].update(power_mw_status="estimated"))
    assert any("GATE 10" in p and "estimated" in p for p in run_gates(root, TODAY))


def test_gate10_estimated_l2_requires_identity_marker(data_copy):
    root, edit = data_copy
    edit(ALPHA, lambda d: _ind(d, "L2").update(status="estimated"))
    assert any("GATE 10" in p and "power_mw_status" in p for p in run_gates(root, TODAY))


def test_gate10_coherent_estimated_pair_passes(data_copy):
    root, edit = data_copy
    def coherent(d):
        d["identity"]["power_mw_status"] = "estimated"
        _ind(d, "L2")["status"] = "estimated"
    edit(ALPHA, coherent)
    assert not any("GATE 10" in p for p in run_gates(root, TODAY))


# ── GATE GÉO : des dents là où il y a un corpus, inerte là où il n'y en a pas ───────────────
def test_geo_gate_inerte_sans_newsroom_mais_mordant_avec(tmp_path, monkeypatch):
    """Sans corpus privé monté, ce gate n'a rien à protéger — AVEC, un sidecar manquant est
    un vrai manquement.

    Défaut vécu le 2026-10-01 : le gate exigeait le sidecar `centroid-check.json`, qui vit
    dans le newsroom PRIVÉ. Vert en local (newsroom monté), rouge dans toute CI et tout clone
    frais — et il a bloqué la PR d'un coéquipier sur un sujet sans aucun rapport. Un gate qui
    échoue là où il ne peut rien protéger finit par être désactivé, et c'est alors le vrai
    cas qui passe.
    """
    from engine.validate import geo_gate
    from engine.core import DATA_DIR

    monkeypatch.setenv("NEWSROOM_CAL", str(tmp_path / "jamais-monte"))
    assert geo_gate(DATA_DIR) == [], "sans newsroom, le gate doit se taire (CI, clone frais)"

    newsroom = tmp_path / "newsroom-sans-sidecar"
    newsroom.mkdir()
    monkeypatch.setenv("NEWSROOM_CAL", str(newsroom))
    violations = geo_gate(DATA_DIR)
    assert any("sidecar" in v for v in violations), (
        "avec un newsroom monté et PAS de sidecar, le gate doit refuser — sinon il suffirait "
        "de ne pas lancer la mesure pour passer"
    )


# ── GATE POSITION : deux fiches au même point doivent avoir été tranchées ───────────────────
def _fiche_au_point(dossier, fid, lat, lon, adjudication=None):
    """Le minimum que le gate position lit : un identifiant, un point, une provenance."""
    (dossier / f"{fid}.json").write_text(json.dumps(
        {"identity": {"coordinates": {"lat": lat, "lon": lon}}}), encoding="utf-8")
    if adjudication is not None:
        (dossier / f"{fid}.provenance.json").write_text(json.dumps(
            {"position_adjudication": adjudication}), encoding="utf-8")
    return dossier / f"{fid}.json"


def test_position_gate_refuse_une_paire_neuve_et_accepte_une_paire_tranchee(tmp_path):
    """La garantie, écrite noir sur blanc : une NOUVELLE paire co-localisée ne passe pas.

    Ce gate existe parce que le contrôle avait d'abord été appliqué à un seul lot — 13 fiches
    britanniques retenues sur ce critère, pendant que 78 paires à un mètre ou moins étaient
    déjà servies sur neuf autres pays. Le standard était bon, son périmètre était faux.
    """
    from engine.validate import position_gate

    d = tmp_path / "cal"
    d.mkdir()
    a = _fiche_au_point(d, "xx-alpha", 48.8566, 2.3522)
    b = _fiche_au_point(d, "xx-beta", 48.8566, 2.3522)        # exactement le même point
    loin = _fiche_au_point(d, "xx-gamma", 48.8570, 2.3522)    # ~44 m plus au nord

    v = position_gate([a, b, loin])
    assert len(v) == 1 and "xx-alpha" in v[0] and "xx-beta" in v[0], (
        "deux fiches au même point sans adjudication doivent être refusées"
    )
    assert "xx-gamma" not in v[0], "44 m, ce sont deux points distincts — pas une paire"

    # La MÊME paire, tranchée sur une seule des deux fiches : elle passe au mérite.
    _fiche_au_point(d, "xx-beta", 48.8566, 2.3522,
                    adjudication={"verdict": "confirmed", "basis": "deux halls, même campus",
                                  "source": "registre", "date": "2026-10-02"})
    assert position_gate([a, b, loin]) == [], (
        "une paire tranchée en provenance doit passer — le gate exige une décision, "
        "pas l'absence de co-localisation"
    )


def test_position_gate_laisse_passer_la_dette_inventoriee_mais_rien_d_autre(tmp_path, monkeypatch):
    """La dette héritée passe PARCE QU'ELLE EST LISTÉE, et elle seule."""
    from engine import position_waivers
    from engine.validate import position_gate

    d = tmp_path / "cal"
    d.mkdir()
    a = _fiche_au_point(d, "xx-dette-a", 50.0, 3.0)
    b = _fiche_au_point(d, "xx-dette-b", 50.0, 3.0)
    assert position_gate([a, b]), "hors inventaire, la paire est refusée"

    monkeypatch.setitem(position_waivers.POSITION_WAIVERS,
                        ("xx-dette-a", "xx-dette-b"), "2026-10-02 — héritée, à trancher")
    assert position_gate([a, b]) == [], "inventoriée, la paire passe"


def test_position_waivers_est_une_dette_pas_une_regle():
    """Un inventaire sans date n'est pas une dette, c'est une permission déguisée."""
    from engine.position_waivers import POSITION_WAIVERS

    for paire, motif in POSITION_WAIVERS.items():
        assert paire == tuple(sorted(paire)), f"clé non triée : {paire!r}"
        assert re.match(r"^20\d\d-\d\d-\d\d — ", motif), (
            f"{paire!r} : une dérogation sans date ni motif est un aveu d'échec — {motif!r}"
        )


def test_geo_gate_refuse_une_fiche_indecidable(tmp_path, monkeypatch):
    """Une fiche qu'on ne sait PAS juger ne part pas en ligne.

    Le détecteur classait « faux positif » — donc sain — une fiche près d'un centroïde dont
    le verdict bâtiment manquait. Une fiche jamais mesurée ressemblait alors à une fiche
    mesurée et propre, et le détecteur paraissait d'autant plus net qu'on lui ajoutait des
    fiches qu'il ne savait pas juger. Le troisième état `non_evalue` vient d'agent-data-
    pipeline-FR ; ce test fixe la conséquence côté gate, qui est de refuser.
    """
    from engine.validate import geo_gate, GEO_WAIVERS
    from engine.core import DATA_DIR, datacenter_paths

    newsroom = tmp_path / "newsroom"
    (newsroom / "geo-audit").mkdir(parents=True)
    sidecar = newsroom / "geo-audit" / "centroid-check.json"
    monkeypatch.setenv("NEWSROOM_CAL", str(newsroom))
    n = len(datacenter_paths(DATA_DIR))

    def ecrire(non_evalues):
        sidecar.write_text(json.dumps({
            "meta": {"counts": {"testées": n}},
            "fabriquees_probables": [],
            "non_evalues": [{"id": i} for i in non_evalues],
        }), encoding="utf-8")

    ecrire([])
    assert geo_gate(DATA_DIR) == [], "mesure complète et rien à signaler : le gate se tait"

    ecrire(["xx-jamais-mesuree"])
    violations = geo_gate(DATA_DIR)
    assert any("xx-jamais-mesuree" in v and "indécidable" in v for v in violations), (
        "une fiche sans verdict bâtiment doit être REFUSÉE, pas comptée saine"
    )

    monkeypatch.setitem(GEO_WAIVERS, "xx-jamais-mesuree", "2026-10-02 — cas de test")
    assert geo_gate(DATA_DIR) == [], "une dérogation datée la fait passer, comme pour les fabriquées"


def test_geo_gate_dit_ce_qu_il_ne_voit_pas_quand_il_passe(tmp_path, monkeypatch, capsys):
    """Vert ne veut pas dire « coordonnées certifiées », et le gate doit le dire lui-même.

    Deux angles morts sont établis : le test ne regarde que le centroïde de COMMUNE (il rate
    un centroïde de district postal, cf. gb-virtus-london5-stockley-park) et il compare à UN
    seul répertoire géographique (quatre fiches suisses décrites comme des centroïdes de
    commune n'apparaissent dans aucune liste du sidecar). La provenance ne rattrape rien :
    1285 coordonnées sur 1430 sont `unrecorded`. Un gate qu'on croit plus large qu'il n'est
    vaut moins qu'un gate absent.
    """
    from engine.validate import geo_gate
    from engine.core import DATA_DIR, datacenter_paths

    newsroom = tmp_path / "newsroom"
    (newsroom / "geo-audit").mkdir(parents=True)
    monkeypatch.setenv("NEWSROOM_CAL", str(newsroom))
    (newsroom / "geo-audit" / "centroid-check.json").write_text(json.dumps({
        "meta": {"counts": {"testées": len(datacenter_paths(DATA_DIR))},
                 "angle_mort": "ne voit pas les aires sub-communales"},
        "fabriquees_probables": [], "non_evalues": [],
    }), encoding="utf-8")

    assert geo_gate(DATA_DIR) == []
    dit = capsys.readouterr().err
    assert "rien à signaler" in dit and "ne voit pas les aires sub-communales" in dit, (
        "quand il passe, le gate doit énoncer sa portée — sinon « vert » se lit « certifié »"
    )


def test_projection_se_perime_sur_les_distances_pas_sur_le_compte(tmp_path, monkeypatch):
    """Un cache de carte indexé sur le seul NOMBRE de sites ment dès qu'une valeur change.

    Vécu le 2026-10-02 : l'intensité carbone britannique harmonisée sur les 148 fiches, le
    compte inchangé. Les listes de voisins, recalculées, perdaient bien l'artefact de
    millésime (99 % de voisinage entre fiches d'un même millésime, retombé à 3 %) pendant
    que la CARTE, relue en cache, continuait d'afficher les familles d'avant. Deux vérités
    à l'écran sur la même page.
    """
    import sys
    import numpy as np
    sys.path.insert(0, "scripts")
    import build_comparator as bc

    monkeypatch.setattr(bc, "PROJ_DIR", tmp_path)
    D1 = np.array([[0.0, 1.0], [1.0, 0.0]])
    D2 = np.array([[0.0, 2.0], [2.0, 0.0]])          # MÊME nombre de sites, distances autres
    (tmp_path / "ZZ.json").write_text(json.dumps({
        "n": 2, "sig": bc.hashlib.sha256(np.round(D1, 6).tobytes()).hexdigest()[:16],
        "xy": [[0.0, 0.0], [1.0, 1.0]], "familles": [0, 0]}), encoding="utf-8")

    xy, fam = bc.projection("ZZ", D1, froid=False)
    assert xy.shape == (2, 2), "distances inchangées : le cache doit être relu"

    try:
        bc.projection("ZZ", D2, froid=False)
    except SystemExit as e:
        assert "distances différentes" in str(e), (
            f"le refus doit nommer la vraie cause, pas un écart de compte — {e}"
        )
    else:
        raise AssertionError("mêmes sites, autres distances : le cache ne doit PAS être relu")


def test_gate5_judges_only_the_journal_head_and_lets_history_keep_old_versions(data_copy):
    """UN JOURNAL GARDE SES VIEILLES VERSIONS, SINON CE N'EST PAS UN JOURNAL.

    GATE 5 contrôlait chaque entrée : il réclamait donc que l'historique soit réécrit à
    chaque montée de méthodo, alors qu'un re-score APPEND. Le remède qu'il imprime
    (« make rescore ») ne pouvait jamais le satisfaire — boucle constatée en v0.3.0
    (2026-10-06). Ce qui doit être à jour, c'est l'état PUBLIÉ, donc la dernière entrée.
    """
    root, edit = data_copy
    actif = load_methodology(root)["version"]

    def deux_entrees(d):
        tete = dict(d["score_history"][-1])
        d["score_history"] = [
            dict(tete, methodology_version="0.0.1", event="methodology_change",
                 rationale="entrée historique : calculée sous une méthodo antérieure"),
            dict(tete, methodology_version=actif),
        ]

    edit(ALPHA, deux_entrees)
    stale = [p for p in run_gates(root, TODAY) if STALE_METHODOLOGY_REMEDY in p]
    assert stale == [], f"une entrée ANCIENNE ne doit rien déclencher : {stale}"

    # …mais une tête périmée, si : c'est l'état servi qui serait calculé sous l'ancienne grille.
    edit(ALPHA, lambda d: d["score_history"][-1].update(methodology_version="0.0.1"))
    assert any(STALE_METHODOLOGY_REMEDY in p for p in run_gates(root, TODAY))


# ─────────────────────────────────────────────────────────────────────────────────────────
# GATE STATUT — « en service » est une AFFIRMATION, et elle doit avoir une source.
# Trois fois le même défaut avant que ce gate existe : le lot DCmag (6 faux operational d'un
# annuaire curé), les 361 invérifiables, puis 8 fiches irlandaises de licence EPA où la valeur
# était forcée dans l'entrée du run. Chaque fois trouvé À LA MAIN, par quelqu'un qui pensait
# à regarder. Ces contre-épreuves fixent ce que le gate refuse — un gate non éprouvé est une
# piste d'audit qui ment.
# ─────────────────────────────────────────────────────────────────────────────────────────

def _corpus_statut(racine, fiches: dict[str, str], verdicts: dict[str, str]):
    """Un corpus jouet : {id: project_status} + le sidecar {id: verdict}."""
    dossier = racine / "datacenters"
    if dossier.is_dir():
        # 🔴 Repartir PROPRE : la première version empilait, et les fiches du cas précédent
        # restaient « en service » sans être dans le nouveau sidecar — le test suivant
        # échouait sur un défaut qu'il n'avait pas écrit.
        for vieux in dossier.iterdir():
            vieux.unlink()
    dossier.mkdir(parents=True, exist_ok=True)
    for fid, statut in fiches.items():
        (dossier / f"{fid}.json").write_text(
            json.dumps({"id": fid, "identity": {"project_status": statut}}), encoding="utf-8")
    (racine / "status-proof").mkdir(parents=True, exist_ok=True)
    (racine / "status-proof" / "status_check.json").write_text(
        json.dumps({"fiches": {k: {"verdict": v} for k, v in verdicts.items()}}), encoding="utf-8")


def test_statut_gate_refuse_une_fiche_de_plus_sans_source(tmp_path, monkeypatch):
    """Le cliquet empêche la fiche SUIVANTE — c'est tout son objet.

    Il ne prétend pas que les fiches déjà servies soient justes : il empêche qu'il y en ait
    une de plus. Et on ne remplace pas une affirmation non sourcée par une autre (la leçon
    des 35 : un flip de masse vers `announced` fabriquerait de faux « annoncés » sur de vrais
    sites en service). Elles baissent par la preuve, fiche à fiche.
    """
    from engine.validate import statut_gate
    import engine.validate as validate

    _corpus_statut(tmp_path, {"xx-un": "operational"}, {"xx-un": "unverified"})
    monkeypatch.setattr(validate, "STATUT_NON_SOURCE", 1)
    assert statut_gate(tmp_path) == [], "au niveau du cliquet, le gate se tait"

    _corpus_statut(tmp_path, {"xx-un": "operational", "xx-deux": "operational"},
                   {"xx-un": "unverified", "xx-deux": "unverified"})
    violations = statut_gate(tmp_path)
    assert any("1 fiche(s) de plus" in v and "xx-deux" in v for v in violations), violations


def test_statut_gate_mord_aussi_quand_le_compte_BAISSE(tmp_path, monkeypatch):
    """Un cliquet dont le chiffre n'est plus exact laisse la place à une régression muette.

    Même discipline que la dette i18n : si le compte descend sans que le nombre suive, il
    reste de la marge pour qu'une fiche non sourcée revienne sans rien casser.
    """
    from engine.validate import statut_gate
    import engine.validate as validate

    _corpus_statut(tmp_path, {"xx-un": "operational"}, {"xx-un": "verified"})
    monkeypatch.setattr(validate, "STATUT_NON_SOURCE", 1)
    violations = statut_gate(tmp_path)
    assert any("baisser `STATUT_NON_SOURCE` à 0" in v for v in violations), violations


def test_statut_gate_accepte_les_deux_preuves_et_une_seule_suffit(tmp_path, monkeypatch):
    """Les réseaux interconnectés dans le bâtiment, OU une source qui cite le stade.

    `live_signal` compte comme `verified` : les deux sont des signaux d'exploitation. En
    revanche `unverified` veut dire « on a cherché et rien trouvé » — ce n'est pas une preuve,
    et ce n'est pas non plus la même chose qu'une fiche jamais mesurée, qui n'apparaît pas du
    tout dans le sidecar.
    """
    from engine.validate import statut_gate
    import engine.validate as validate

    monkeypatch.setattr(validate, "STATUT_NON_SOURCE", 0)
    _corpus_statut(tmp_path, {"xx-res": "operational", "xx-sig": "operational"},
                   {"xx-res": "verified", "xx-sig": "live_signal"})
    assert statut_gate(tmp_path) == [], "une preuve PeeringDB suffit"

    _corpus_statut(tmp_path, {"xx-prov": "operational"}, {"xx-prov": "unverified"})
    assert statut_gate(tmp_path), "sans provenance, la fiche compte"
    (tmp_path / "datacenters" / "xx-prov.provenance.json").write_text(json.dumps(
        {"project_status_provenance": {"to": "operational",
                                       "source": {"title": "t", "url": "https://exemple.test"},
                                       "date": "2026-10-29"}}), encoding="utf-8")
    assert statut_gate(tmp_path) == [], "une provenance qui cite sa source suffit aussi"


def test_statut_gate_voit_une_fiche_jamais_mesuree(tmp_path, monkeypatch):
    """Une fiche « en service » absente du sidecar n'est pas une fiche propre.

    C'est le même piège que le gate géo : il suffirait de ne pas relancer la mesure après un
    onboarding pour passer sans être vu. Elle compte comme non sourcée — le refus est le bon —
    mais le gate le NOMME, sinon un onboarding sans mesure ressemble à une mesure propre.
    """
    from engine.validate import statut_gate
    import engine.validate as validate

    monkeypatch.setattr(validate, "STATUT_NON_SOURCE", 0)
    _corpus_statut(tmp_path, {"xx-neuve": "operational"}, {})
    violations = statut_gate(tmp_path)
    assert any("jamais été mesurées" in v and "xx-neuve" in v for v in violations), violations


def test_statut_gate_inerte_sans_newsroom(tmp_path, monkeypatch):
    """Sans corpus privé monté, ce gate n'a rien à protéger — même nuance que le gate géo.

    Le gate géo a été câblé en exigeant son sidecar : vert en local, rouge dans toute CI et
    tout clone frais, et il a bloqué la PR d'un coéquipier sur un sujet sans rapport. Un gate
    qui échoue là où il ne peut rien protéger finit par être désactivé — et c'est alors le
    vrai cas qui passe.
    """
    from engine.validate import statut_gate
    from engine.core import DATA_DIR

    monkeypatch.setenv("NEWSROOM_CAL", str(tmp_path / "jamais-monte"))
    assert statut_gate(DATA_DIR) == [], "sans newsroom, le gate se tait"

    newsroom = tmp_path / "newsroom-sans-sidecar"
    newsroom.mkdir()
    monkeypatch.setenv("NEWSROOM_CAL", str(newsroom))
    assert any("sidecar" in v for v in statut_gate(DATA_DIR)), (
        "avec un newsroom monté, un sidecar manquant est un vrai manquement"
    )


def test_aucun_gate_ne_reste_debranche():
    """Tout `*_gate` d'`engine.validate` doit être APPELÉ par `scripts/validate_corpus.py`.

    🔴 C'est le défaut que ce dépôt a déjà payé DEUX fois, et son propre commentaire le dit :
    « le gate avait toutes ses dents, braquées sur le vide ». Le gate géo existait depuis le
    2026-09-29, câblé dans `run_gates()` — donc dans `make validate`, qui ne voit que les deux
    fixtures du dépôt : son contrôle de couverture comparait 1 447 fiches mesurées à 2 et
    passait trivialement, tandis que le gate de déploiement, seul à voir le corpus réel, ne
    l'appelait pas. Même histoire pour le gate POSITION.

    La liste des gates appelés était tenue à la main, à côté des gates qui existent — une
    liste à deux endroits finit par mentir, et ici le mensonge est silencieux : le gate neuf
    passe la revue, il est même testé, et il ne tourne jamais sur le corpus servi.
    """
    import inspect
    import engine.validate as validate

    gates = {
        nom for nom, obj in vars(validate).items()
        if nom.endswith("_gate") and inspect.isfunction(obj) and not nom.startswith("_")
    }
    assert gates, "aucun gate trouvé dans engine.validate — le relevé ne cherche plus"
    source = (REPO_ROOT / "scripts" / "validate_corpus.py").read_text(encoding="utf-8")
    debranches = sorted(g for g in gates if f"{g}(" not in source)
    assert not debranches, (
        f"{debranches} existe(nt) dans engine.validate mais n'est/ne sont appelé(s) nulle part "
        f"dans scripts/validate_corpus.py — donc jamais sur le corpus SERVI. Un gate débranché "
        f"a toutes ses dents, braquées sur le vide."
    )
