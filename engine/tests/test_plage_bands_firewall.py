# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Firewall — a coverage band may be SERVED on a pipeline (« en veille ») fiche, but must
never touch the DEFINITIVE grade of an operational fiche.

Franck validated serving a PUBLIC provisional band on pipeline projects (labelled
provisional). So `engine.plage_bands` is no longer forbidden everywhere — the artifact
builder may attach a band. The invariant is refined, NOT dropped:

  (A) Static — the DEFINITIVE-grade computation must stay band-free. `scoring.py`,
      `normalize.py`, `score.py` compute the published letter; if any imported plage_bands
      a band could feed the real grade. They must never import it.

  (B) Behavioural — the single serving gate `servable_band()` enforces the display rules:
      - operational (any non-pipeline) status -> None: NEVER a band (definitive letter only);
      - pipeline + non-credible (> 2 adjacent letters) -> « en veille » marker, no letter;
      - pipeline + credible (<= 2 adjacent letters) -> a provisional band object that carries
        NO bare `grade` key, so it can never be slotted into `grades.site.grade`.

Together: a band can reach the public build ONLY through `servable_band`, ONLY on a pipeline
fiche, ONLY when credible, and ALWAYS in a provisional-typed object distinct from a grade.
"""

import ast
import json
from pathlib import Path

from engine.core import load_methodology
from engine.plage_bands import (
    servable_band, PIPELINE_STATUSES, build_reference_pool,
    pillar_bands, base_definitions, grade_of, GRADE_ORDER,
)

ENGINE = Path(__file__).resolve().parent.parent
REPO = ENGINE.parent

# (A) Modules that compute the DEFINITIVE grade — must never import the band util.
DEFINITIVE_GRADE_MODULES = [
    ENGINE / "scoring.py",
    ENGINE / "normalize.py",
    ENGINE / "score.py",
]


def _imports_plage_bands(path: Path) -> bool:
    if not path.exists():
        return False
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "plage_bands" in node.module:
            return True
        if isinstance(node, ast.Import) and any("plage_bands" in a.name for a in node.names):
            return True
    return False


def test_definitive_grade_path_never_imports_plage_bands():
    offenders = [p.name for p in DEFINITIVE_GRADE_MODULES if _imports_plage_bands(p)]
    assert not offenders, (
        "coverage-band util imported by a DEFINITIVE-grade module: "
        f"{offenders}. The published letter must be computed by score_datacenter alone — "
        "a provisional band must never be able to feed grades.site.grade."
    )


# (B) The serving gate behaviour — the contract the artifact builder relies on.
_METHO = load_methodology()

# A rich present-set (structural gaps small) → a plage at the irreducible floor, i.e. servable.
# E6 joined the base block with méthodo v0.2.0 (chaleur fatale split out of F5); a fixture that
# still omitted it carried one gap too many and drifted to « en attente » — the fixture had not
# followed the base set, the rule had not changed.
_RICH = {"E1": 30.0, "E2": 70.0, "E3": 65.0, "E6": 50.0, "W1": 60.0, "W2": 80.0, "W3": 65.0,
         "F1": 70.0, "F2": 100.0, "L1": 60.0, "L3": 100.0}
# The SAME knowledge, 10 points lower: same plage width (the floor), but the window now sits
# across THREE letters instead of two. See test_same_width_same_treatment_wherever_it_sits.
_RICH_SHIFTED = {i: v - 10.0 for i, v in _RICH.items()}
# A thin present-set (many structural gaps) → a plage WIDER than the floor: we really don't know.
_THIN = {"E1": 30.0, "W1": 60.0}


def test_operational_fiche_never_gets_a_band():
    for op_status in ("operational", "decommissioned", "unknown", None):
        assert servable_band(op_status, _RICH, "FR", _METHO, None) is None, (
            f"status {op_status!r} is not pipeline yet servable_band returned a band — "
            "an operational fiche must keep its definitive letter, never a band."
        )


def test_pipeline_credible_returns_a_provisional_object_without_a_grade_key():
    out = servable_band("announced", _RICH, "FR", _METHO, None)
    assert out is not None and out["kind"] == "provisional_band"
    assert out.get("provisional") is True
    # crucial: no bare `grade`/`grade_site` key that could be slotted into a definitive field
    assert "grade" not in out and "grade_site" not in out, (
        "a provisional band must not carry a definitive-grade key — it could be published "
        "as a real letter."
    )
    # loupe display contract: central (big) + the endpoint letters around it (small)
    assert out["central"] in {"A", "B", "C", "D", "E"}, "central must be a letter"
    assert all(g in {"A", "B", "C", "D", "E"} for g in out["edges"]), "edges must be letters"
    assert out["central"] not in out["edges"], "edges are the letters OTHER than central"
    assert out["edges"] == sorted(set(out["edges"]), key="ABCDE".index, reverse=True), (
        "edges must be ordered worst-first and deduplicated — a set literal was iterated here "
        "once, which only stayed stable while a plage could touch at most two letters."
    )
    assert out["adjacent"] == (out["edges"][0] if len(out["edges"]) == 1 else None)
    assert out["confidence"] in {"low", "medium", "high"}
    assert "–" in out["band"], "a band is a RANGE (e.g. B–C), never a single letter"


def test_confidence_passthrough_wins_over_the_coverage_proxy():
    out = servable_band("announced", _RICH, "FR", _METHO, None, confidence="high")
    assert out["confidence"] == "high"


def test_same_width_same_treatment_wherever_it_sits():
    """Deux fiches qui en savent AUTANT sont traitées pareil, où que tombe leur fenêtre.

    Le défaut réparé le 2026-09-30 : le critère d'affichage comptait les LETTRES que la plage
    chevauche. Comme une plage provisoire fait presque toujours exactement STATUS_FLOOR de large
    — une convention, pas une mesure — ce critère mesurait la POSITION de la fenêtre contre les
    seuils, pas ce qu'on sait. Conséquence vécue : ajouter un fait MESURÉ (E6) déplaçait Étrechet
    de 2,3 points, la même fenêtre de 18,0 points débordait alors le seuil du E de 1,4 point, et
    la fiche la plus consultée du corpus perdait sa note, son titre et sa carte de partage.

    Ici les deux jeux portent la même information à 10 points près : même largeur, mais l'un
    tient sur deux lettres et l'autre sur trois. Les deux doivent être servis.
    """
    wide, shifted = (servable_band("announced", p, "FR", _METHO, None)
                     for p in (_RICH, _RICH_SHIFTED))
    assert wide["kind"] == "provisional_band"
    assert shifted["kind"] == "provisional_band", (
        "same plage width, merely sitting across three letters instead of two, and the band was "
        "withheld — the criterion is measuring position again, not knowledge."
    )
    assert (wide["best"] - wide["worst"]) == (shifted["best"] - shifted["worst"]), (
        "the two fixtures must have the SAME width for this test to mean anything"
    )
    assert len(shifted["edges"]) == 2, "the shifted window is expected to touch three letters"


def test_pipeline_wide_carries_the_probable_and_its_bounds():
    # RÈGLE C-BIS (Franck 2026-10-16): a wide window is no longer a mute chip — it carries the
    # PROBABLE (renorm point) and its bounds. The kind stays "en_attente" (still wider than the
    # irreducible floor; the renderer must say so), and there is still no bare "grade" key.
    out = servable_band("announced", _THIN, "FR", _METHO, None)
    assert out is not None and out["kind"] == "en_attente"
    assert out["wide"] is True and out["provisional"] is True
    assert out["central"] in ("B", "C", "D", "E")          # the probable (A reserved -> B)
    assert "–" in out["band"] or out["band"] == out["central"]
    assert out["width"] > out["floor"]
    assert "grade" not in out, "never a bare grade key — it must not slot into grades.site"


def test_knn_expected_score_is_internal_and_imputes_medians():
    from engine.plage_bands import knn_expected_score
    # pool: 4 same-country neighbours all carrying W1 -> median imputation kicks in
    pool = build_reference_pool([
        {"country": "FR", "present": {"E1": 60.0, "W1": v}} for v in (10.0, 30.0, 50.0, 70.0)
    ])
    out = knn_expected_score({"E1": 60.0}, "FR", _METHO, pool)
    assert out["n_imputed"] >= 1 and "W1" in out["imputed"]
    assert out["imputed"]["W1"] == 40.0                    # median of 10/30/50/70
    assert out["grade"] in ("A", "B", "C", "D", "E")
    assert "jamais servi" in out["semantics"]
    # fewer than 3 neighbours for a gap -> the gap stays ABSENT, never a fabricated midpoint
    thin_pool = build_reference_pool([{"country": "FR", "present": {"E1": 60.0, "W1": 10.0}}])
    out2 = knn_expected_score({"E1": 60.0}, "FR", _METHO, thin_pool)
    assert "W1" not in out2["imputed"]


def test_espérance_is_never_referenced_by_the_artifact_builder():
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "artifacts.py").read_text()
    assert "knn_expected_score" not in src, (
        "the kNN espérance is a model output on named sites — INTERNAL, never served (1c)."
    )


def test_pipeline_statuses_are_exactly_the_provisional_set():
    # guards against a status silently gaining/losing band-eligibility
    assert PIPELINE_STATUSES == frozenset({"announced", "permitting", "under_construction"})


def test_publication_signee_domine_laffichage_principe_pas_implementation():
    """HIÉRARCHIE (actée pipeline+site, 2026-10-16) : publication (veille.json, Franck signe)
    > affichage (règle C/C-bis). Le PRINCIPE figé côté moteur — pas l'implémentation du scrub :
    `plage_bands` est PUR et ne consulte JAMAIS veille.json (aucune I/O). Si la bande savait
    lire la veille, il y aurait deux autorités de blanchiment qui divergent en silence ; la
    couche de service reste la SEULE autorité qui retire (lettres ET provisional_band) ce
    qu'une décision de publication signée retient."""
    import pathlib
    from engine import plage_bands
    src = pathlib.Path(plage_bands.__file__).read_text()
    assert "veille.json" not in src, "plage_bands ne doit jamais consulter la liste de veille"
    for io_marker in ("open(", "read_text", "urllib", "requests", "json.load"):
        assert io_marker not in src, f"plage_bands doit rester pur (trouvé {io_marker!r})"


# ---------------------------------------------------------- RÈGLE C-BIS AUX PILIERS (2026-10-23)
def test_un_pilier_sur_une_seule_mesure_reste_muet():
    """UNE LETTRE QUI TIENT SUR UNE MESURE EST CETTE MESURE, DÉGUISÉE EN LETTRE.

    Cas fondateur : us-stamp-data-center, pilier « Impact local ». Le moteur lui donne un C
    définitif — mais ce C repose sur L2 SEUL (le ratio MW/habitants). Le publier en sous-note
    probable ferait lire « nous avons apprécié l'impact local » là où nous ne connaissons que
    la taille relative du projet. Le pilier sort donc du résultat : il n'est pas « en attente »,
    il est ABSENT, et le compte d'indicateurs de la fiche dit ce qu'il y a à dire.
    """
    methodology = load_methodology()
    base = base_definitions(methodology)
    local = [d["id"] for d in base if d["pillar"] == "local_impact"]
    assert len(local) >= 2, "ce test suppose un pilier local à plusieurs indicateurs de base"

    present = {local[0]: 60.0}
    bands = pillar_bands("announced", present, "US", methodology, pool=None)
    assert "local_impact" not in bands, (
        "un pilier à une seule mesure présente ne doit porter AUCUNE sous-note probable"
    )

    present[local[1]] = 40.0
    bands = pillar_bands("announced", present, "US", methodology, pool=None)
    assert "local_impact" in bands, "à deux mesures présentes, le pilier doit parler"


def test_une_sous_bande_ne_porte_jamais_de_cle_grade():
    """Même invariant que la bande du site : l'objet ne doit pas pouvoir être glissé dans
    `pillars.<id>.grade`. Il porte `central`, `edges` et `band` — jamais `grade`."""
    methodology = load_methodology()
    base = base_definitions(methodology)
    eau = [d["id"] for d in base if d["pillar"] == "water"][:2]
    bands = pillar_bands("announced", {eau[0]: 20.0, eau[1]: 0.0}, "US", methodology, pool=None)
    assert bands, "le cas de test doit produire au moins une sous-bande"
    for pid, b in bands.items():
        assert "grade" not in b and "grade_site" not in b, f"{pid} porte une clé grade"
        assert isinstance(b["central"], str) and b["central"] in GRADE_ORDER


def test_une_fiche_en_service_na_aucune_sous_bande():
    """LE PARE-FEU VAUT AUSSI POUR LES PILIERS.

    Une fiche en service publie ses lettres DÉFINITIVES ; une bande de couverture ne doit
    jamais les recouvrir. La règle existait pour la note du site, elle n'aurait eu aucun sens
    d'être relâchée d'un cran plus bas.
    """
    methodology = load_methodology()
    base = base_definitions(methodology)
    eau = [d["id"] for d in base if d["pillar"] == "water"][:2]
    present = {eau[0]: 20.0, eau[1]: 0.0}
    assert pillar_bands("operational", present, "US", methodology, pool=None) == {}
    assert pillar_bands("announced", present, "US", methodology, pool=None) != {}


def test_la_sous_note_probable_ne_contredit_pas_la_lettre_du_moteur():
    """LES DEUX SORTENT DU MÊME CALCUL : ELLES DOIVENT DIRE LA MÊME CHOSE.

    C'est la raison d'être de toute l'extension. Avant le 2026-10-23 la fiche publiait une note
    probable pour le SITE et cinq tirets pour les piliers, issus des mêmes mesures ; la phrase
    citable, elle, annonçait déjà « noté D sur le site, mais E sur Eau ». Trois surfaces, trois
    affirmations.

    Le point renormalisé d'un pilier EST la lettre que le moteur lui donne quand il accepte de
    la donner : si les deux divergeaient, l'une des deux mentirait. Ce test les confronte sur
    une fiche fabriquée dont tous les piliers tiennent sur au moins deux mesures.
    """
    methodology = load_methodology()
    base = base_definitions(methodology)
    # Deux indicateurs posés par pilier, valeurs étagées pour balayer l'échelle.
    present, valeurs = {}, [0.0, 20.0, 60.0, 100.0]
    for n, pillar in enumerate(dict.fromkeys(d["pillar"] for d in base)):
        for d in [d for d in base if d["pillar"] == pillar][:2]:
            present[d["id"]] = valeurs[n % len(valeurs)]

    bands = pillar_bands("announced", present, "ZZ", methodology, pool=None)
    assert bands, "le cas de test doit produire des sous-bandes"
    for pillar, b in bands.items():
        defs = [d for d in base if d["pillar"] == pillar and d["id"] in present]
        poids = sum(d["weight_in_pillar"] for d in defs)
        point = sum(d["weight_in_pillar"] * present[d["id"]] for d in defs) / poids
        attendu = grade_of(point, methodology)
        attendu = "B" if attendu == "A" else attendu   # A-25 : réservé sur une fiche pipeline
        assert b["central"] == attendu, (
            f"{pillar} : sous-note probable {b['central']} contre {attendu} au point renormalisé"
        )
