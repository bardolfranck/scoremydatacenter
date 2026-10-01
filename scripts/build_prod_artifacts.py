# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Rebuild the PRODUCTION site artifacts from the private newsroom calibration.

Two-repo hazard: `make score` reads the PUBLIC repo (only the zz- test fixtures) and
overwrites site/public/data with those 2 DCs — wiping the real corpus and the
watchlist from the served map. The production DCs (every `datacenters*` panel) and
the "En veille" watchlist live in the newsroom; this rebuilds the served artifacts
from there. Deterministic; no gate run (the calibration holds work-in-progress
drafts) — use `make score` / `make validate` for the public fixtures.

    make prod-artifacts                 # ../smdc-newsroom/calibration
    NEWSROOM_CAL=/path make prod-artifacts
"""

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root, so `engine` imports when run as a file

from engine.artifacts import build_artifacts
from engine.core import ARTIFACTS_DIR, load_datacenters, load_methodology, load_watchlist

CAL = Path(os.environ.get("NEWSROOM_CAL", Path(__file__).resolve().parent.parent.parent / "smdc-newsroom" / "calibration"))

# Media env (HMAC secret + public base URL) lives OUTSIDE both repos —
# ~/.smdc/media.env — loaded here so `make prod-artifacts` just works.
_MEDIA_ENV = Path.home() / ".smdc" / "media.env"
if _MEDIA_ENV.is_file():
    for line in _MEDIA_ENV.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def patch_satellite_images() -> int:
    """Brief 9-img-sat: every fiche artifact gets its satellite_image
    {url, thumb, credit} — URL derived from the frozen id + HMAC secret
    (A-28 non-enumerable keys). Only when the media env is configured;
    the engine build and the golden never see this."""
    secret = os.environ.get("SMDC_MEDIA_SECRET")
    base = (os.environ.get("SMDC_MEDIA_BASE") or "").rstrip("/")
    if not secret or not base:
        return 0
    from engine.core import write_json
    from pipelines.media.satellite import media_key
    patched = 0
    for f in sorted((ARTIFACTS_DIR / "dc").glob("*.json")):
        d = json.loads(f.read_text())
        if d["id"].startswith("zz-"):
            continue
        key = media_key(d["id"], secret)
        d["satellite_image"] = {
            "url": f"{base}/{key}",
            "thumb": f"{base}/{key.replace('.webp', '-thumb.webp')}",
            "credit": "Esri, Maxar, Earthstar Geographics",
        }
        write_json(f, d)
        patched += 1
    return patched


LASTMOD_STATE = Path(__file__).resolve().parent.parent / ".lastmod.json"


def patch_updated_at() -> int:
    """Date de mise à jour, sur TOUTES les fiches, sans exception.

    Règle Franck (SEO, 2026-09-29) : le titre porte « — au {date} » partout, « pas
    d'exceptions qui pourrissent le code ». La date rend bénigne une SERP en retard sur un
    changement de note — cas vécu le matin même, Fouju passée de E à D pendant que Google
    servait encore l'ancienne.

    C'est la date du BUILD, et c'est le bon sens : le corpus entier est recalculé à chaque
    build depuis la source, donc chaque fiche est bien vérifiée à cette date. Ce n'est pas
    la date du dernier changement de la fiche, et le titre ne le prétend pas — il dit « au »,
    pas « modifié le ».
    """
    import hashlib
    from datetime import date
    from engine.core import write_json
    today = date.today().isoformat()

    # `content_changed_at` n'est PAS la date du build : c'est la date du dernier build où le
    # CONTENU de la fiche a bougé, repérée par empreinte. Elle alimente le lastmod du
    # sitemap, et c'est pour ça qu'elle doit être honnête — un lastmod qui change à chaque
    # build annoncerait 1 438 pages modifiées tous les jours, ce que Google finit par
    # ignorer. On perdrait exactement ce qu'on cherche : déclencher un recrawl quand une
    # note bouge vraiment.
    state = json.loads(LASTMOD_STATE.read_text()) if LASTMOD_STATE.is_file() else {}
    fresh: dict[str, list[str]] = {}
    n = moved = 0
    for f in sorted((ARTIFACTS_DIR / "dc").glob("*.json")):
        d = json.loads(f.read_text())
        # Empreinte sur un SOUS-ENSEMBLE stable et éditorial : ce qu'un lecteur voit changer.
        # Hacher la fiche entière rendait l'empreinte instable, parce que les champs média
        # (vignette, carte de contexte) s'ajoutent APRÈS ce passage et varient au fil de la
        # production. Un lastmod ne doit pas bouger parce qu'une image a été générée.
        core = {k: d.get(k) for k in ("name", "municipality", "admin_area", "country",
                                      "operator", "project_status", "power_mw", "grades",
                                      "provisional_band", "indicators", "synthesis",
                                      "confidence", "contestation")}
        digest = hashlib.sha256(
            json.dumps(core, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
        prev = state.get(d["id"])
        if not prev or prev[0] != digest:
            changed, moved = today, moved + 1
        else:
            changed = prev[1]
        fresh[d["id"]] = [digest, changed]
        d["updated_at"] = today
        d["content_changed_at"] = changed
        write_json(f, d)
        n += 1
    LASTMOD_STATE.write_text(json.dumps(fresh, ensure_ascii=False))
    print(f"prod-artifacts: content changed on {moved} fiches since last build")
    return n


def patch_context_maps() -> int:
    """La carte de contexte — photo satellite ANNOTÉE — quand elle existe sur R2.

    Décision Franck 2026-09-28 : elle devient la photo par défaut de la fiche et REMPLACE
    la vignette à l'affichage, sans la supprimer du stockage — `satellite_image` reste
    servi et sert de repli.

    À la différence de la vignette, toutes les fiches n'en ont PAS : le rendu est réservé
    aux coordonnées vérifiées (sur un bâtiment ou à ≤25 m) plus les projets. On ne devine
    donc pas l'URL comme pour `sat/` — on lit le manifeste des clés confirmées sur R2,
    sinon la fiche pointerait un 404. Pas de manifeste = pas de carte, jamais d'URL
    inventée.
    """
    secret = os.environ.get("SMDC_MEDIA_SECRET")
    base = (os.environ.get("SMDC_MEDIA_BASE") or "").rstrip("/")
    manifest = Path(__file__).resolve().parent.parent / ".media-sat" / "context-uploaded.txt"
    if not secret or not base or not manifest.is_file():
        return 0
    from engine.core import write_json
    from pipelines.media.satellite import media_key
    confirmed = set(manifest.read_text().split())
    patched = 0
    for f in sorted((ARTIFACTS_DIR / "dc").glob("*.json")):
        d = json.loads(f.read_text())
        key = media_key(d["id"], secret).replace("sat/", "ctx/")
        if key not in confirmed:
            continue
        thumb = key.replace(".webp", "-thumb.webp")
        d["context_map"] = {
            "url": f"{base}/{key}",
            **({"thumb": f"{base}/{thumb}"} if thumb in confirmed else {}),
            "credit": "Esri, Maxar, Earthstar Geographics · OpenStreetMap (ODbL)",
            "caveat": {
                "fr": "Distances à vol d'oiseau depuis la coordonnée de référence. "
                      "Les anneaux sont des tampons de distance, non un zonage réglementaire.",
                "en": "Straight-line distances from the reference coordinate. "
                      "The rings are distance buffers, not statutory zoning.",
            },
        }
        write_json(f, d)
        patched += 1
    return patched


_ASCII = str.maketrans("àáâäãåçèéêëìíîïñòóôöõùúûüýÿ", "aaaaaaceeeeiiiinooooouuuuyy")


def _ascii_lower(s: str) -> str:
    """Accent-folded lowercase, SAME LENGTH as the input (so spans map back to the original)."""
    return s.lower().translate(_ASCII)


def display_name(name: str, municipality: str | None = None) -> str:
    """Rule (Franck 2026-07-24, applied 2026-09-17): a seed name like « ADISTA_-_AIX_EN_PROVENCE »
    is shown « ADISTA - Aix-en-Provence ». Underscores become spaces, spaces collapse, and where the
    name carries the fiche's commune the commune's REAL spelling is restored — French place names are
    hyphenated (Aix-en-Provence, Saint-Germain), and a blind underscore→space loses that. Casing is
    otherwise untouched: never an automatic .title() (it would break OVH, GDC, TDF)."""
    import re
    out = re.sub(r"\s+", " ", (name or "").replace("_", " ")).strip()
    toks = [t for t in re.split(r"[\s-]+", (municipality or "").strip()) if t]
    if not toks:
        return out
    # the commune may appear spaced or hyphenated in the seed name — match either, accent-blind
    pattern = r"\b" + r"[\s-]+".join(re.escape(_ascii_lower(t)) for t in toks) + r"\b"
    m = re.search(pattern, _ascii_lower(out))
    return out[:m.start()] + municipality.strip() + out[m.end():] if m else out


def registry_display_name(denomination: str) -> str:
    """« T D F (TDF) » → « TDF », « BLUE (BLUE) » → « BLUE », « DATAONE FRANCE SAS » → « DATAONE FRANCE »:
    the register's legal denomination, made readable without inventing anything."""
    import re
    parts = [x.strip() for x in re.findall(r"\(([^)]*)\)", denomination)]
    main = re.sub(r"\s*\([^)]*\)", "", denomination).strip()
    if parts and re.fullmatch(r"(?:\S )+\S", main):   # spaced initials → use the sigle
        main = parts[0]
    return re.sub(r"\s+(SAS|SASU|SA|SARL|EURL)$", "", main).strip()


def apply_operator_identity(dcs: dict) -> dict:
    """Operator-fill (Franck go 2026-09-17): a fiche whose operator is unknown takes the company the
    French register resolves with CONFIDENCE (weekly job, pipelines/status_proof/siren.py). Only the
    `confident` tier; developer candidates / lower tiers never fill. Returns {id: source} for the
    fiche artifact's provenance link."""
    sidecar = CAL / "status-proof" / "operator_identity.json"
    if not sidecar.is_file():
        return {}
    sources = {}
    for dc_id, e in json.loads(sidecar.read_text()).get("fiches", {}).items():
        dc = dcs.get(dc_id)
        if not dc or e.get("emit_tier") != "confident" or not (e.get("resolved") or {}).get("denomination"):
            continue
        if str(dc["identity"].get("operator") or "").strip().lower() not in ("", "unknown", "none"):
            continue
        siren_id = e["resolved"]["siren"]
        dc["identity"]["operator"] = registry_display_name(e["resolved"]["denomination"])
        sources[dc_id] = {"source": "SIRENE", "siren": siren_id,
                          "url": f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren_id}",
                          "checked_at": e.get("checked_at")}
    return sources


def patch_operator_source(sources: dict) -> None:
    from engine.core import write_json
    for dc_id, src in sources.items():
        f = ARTIFACTS_DIR / "dc" / f"{dc_id}.json"
        if f.is_file():
            d = json.loads(f.read_text())
            d["operator_source"] = src
            write_json(f, d)


# NAF codes we publish as a real-estate DEVELOPMENT activity (an opposable register fact), with a
# short FR/EN label. Restricted to promotion/construction — never the ambiguous 68.10Z (marchand de
# biens) or a rental code, which are not "a developer" on their own.
NAF_DEVELOPER_PUBLISH = {
    "41.10A": ("promotion immobilière", "real-estate development"),
    "41.10B": ("promotion immobilière", "real-estate development"),
    "41.10C": ("promotion immobilière", "real-estate development"),
    "41.20A": ("construction de bâtiments", "building construction"),
    "41.20B": ("construction de bâtiments", "building construction"),
}


def apply_developer_identity(dcs: dict) -> dict:
    """Developer-when-known (Franck go 2026-09-25). We do NOT publish our own "developer" verdict — we
    publish a SOURCED, opposable FACT: the company's declared register activity (NAF) + its register
    link. Gate is strict, because name-matching produced homonyms (the COLT lesson): a case is
    published ONLY when R&D has SIGNED it (emit_tier "developer_confirmed", never the raw
    "developer_needs_confirm") AND its NAF is a real-estate development code. Fills the operator name
    if unknown. Zero signed cases → nothing published, which is an acceptable outcome."""
    sidecar = CAL / "status-proof" / "operator_identity.json"
    if not sidecar.is_file():
        return {}
    sources = {}
    for dc_id, e in json.loads(sidecar.read_text()).get("fiches", {}).items():
        dc = dcs.get(dc_id)
        r = e.get("resolved") or {}
        naf = r.get("naf")
        if not dc or e.get("emit_tier") != "developer_confirmed" or naf not in NAF_DEVELOPER_PUBLISH:
            continue
        if not r.get("denomination") or not r.get("siren"):
            continue
        siren_id = r["siren"]
        if str(dc["identity"].get("operator") or "").strip().lower() in ("", "unknown", "none"):
            dc["identity"]["operator"] = registry_display_name(r["denomination"])
        activity_fr, activity_en = NAF_DEVELOPER_PUBLISH[naf]
        sources[dc_id] = {"source": "SIRENE", "siren": siren_id, "naf": naf,
                          "activity_fr": activity_fr, "activity_en": activity_en,
                          "url": f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren_id}",
                          "checked_at": e.get("checked_at")}
    # Second chemin, plus fort que le registre des entreprises : le fait déclaré DANS la fiche,
    # quand il vient d'un acte administratif nommant le pétitionnaire de CETTE installation.
    # Le rapprochement par nom au registre des entreprises produit des homonymes (leçon COLT,
    # et Goodman tenu en réserve des semaines pour ça) ; un registre d'évaluation
    # environnementale, lui, ne rapproche pas des noms — il dit qui a déposé le dossier, pour
    # cette commune et cette procédure. Aucune signature R&D requise, parce qu'il n'y a pas
    # d'appariement à valider : la source EST l'appariement.
    for dc_id, dc in dcs.items():
        dev = (dc.get("identity") or {}).get("developer")
        if not dev or not isinstance(dev, dict) or dc_id in sources:
            continue
        if not dev.get("name") or not (dev.get("source") or {}).get("url"):
            continue
        sources[dc_id] = {"source": dev["source"].get("title") or "acte administratif",
                          "activity_fr": dev.get("activity_fr") or "pétitionnaire du dossier",
                          "activity_en": dev.get("activity_en") or "applicant on the case file",
                          "url": dev["source"]["url"],
                          "checked_at": dev["source"].get("accessed")}
        if str(dc["identity"].get("operator") or "").strip().lower() in ("", "unknown", "none"):
            dc["identity"]["operator"] = dev["name"]
    return sources


def patch_developer_source(sources: dict) -> None:
    from engine.core import write_json
    for dc_id, src in sources.items():
        f = ARTIFACTS_DIR / "dc" / f"{dc_id}.json"
        if f.is_file():
            d = json.loads(f.read_text())
            d["developer_source"] = src
            write_json(f, d)


def patch_nearest_dwelling() -> int:
    """Distance aux premières habitations (Franck 2026-09-21) : un FAIT sourcé posé à côté de la
    note — il n'entre dans aucun indicateur ni aucune lettre. Seuls les relevés aboutis voyagent ;
    un site sans réponse OSM n'affiche rien plutôt qu'un chiffre inventé."""
    sidecar = CAL / "habitations" / "distance.json"
    if not sidecar.is_file():
        return 0
    from engine.core import write_json
    rows = json.loads(sidecar.read_text()).get("fiches", {})
    patched = 0
    for f in sorted((ARTIFACTS_DIR / "dc").glob("*.json")):
        d = json.loads(f.read_text())
        r = rows.get(d["id"])
        if not r or not r.get("found"):
            d.pop("nearest_dwelling", None)
        else:
            d["nearest_dwelling"] = {"distance_m": r["distance_m"], "kind": r["kind"],
                                     "source": r.get("source", "OpenStreetMap"),
                                     "checked_at": r.get("checked_at")}
            patched += 1
        write_json(f, d)
    return patched


def _date_publiable(source: dict, proc: dict) -> bool:
    """Une date s'affiche quand elle est corroborée. Sinon, un trou — un trou se voit, une date
    fausse se croit.

    Pour un avis venu du REGISTRE régional, la date est un acte administratif indexé : elle fait
    foi. Pour un avis venu de l'INDEX NATIONAL, elle a été lue dans le PDF, et la mesure du
    2026-10-01 était sans appel : 9 des 23 portaient une date que contredisait le nom de fichier
    de la MRAe, dont un « 2026-04-13 » dans le FUTUR et un « 2020-07-06 » sur un document de 2025.

    La corroboration VIT EN AMONT (pipelines/registers/fiche.date_corroboree, testée), et comme
    pour la dédup on l'APPELLE au lieu de la refaire : j'en avais écrit une seconde ici, et deux
    écritures d'une même règle finissent par diverger. Il ne reste à cette porte qu'une décision
    d'AFFICHAGE — la seule qui m'appartienne : une date se publie quand les deux oracles
    s'accordent (`confirmee`) ou quand l'amont a tranché (`corrigee`).

    `a_arbitrer` ne se publie PAS, et ce n'est pas une prudence provisoire : le statut dit
    littéralement que personne n'a encore décidé laquelle des deux dates est la bonne. Publier
    l'une des deux parce que l'écart est petit, ce serait choisir en silence — et un jour où
    l'écart ne serait plus petit, le même code publierait la mauvaise. `non_confirmee` non plus :
    là il n'existe même pas de second oracle (nom de fichier sans date lisible).
    """
    if "national" not in (source.get("origine") or ""):
        return True
    from pipelines.registers.fiche import date_corroboree  # amont : une seule écriture de la règle

    _retenue, statut = date_corroboree(proc.get("date_avis"), source.get("doc_url"))
    return statut in ("confirmee", "corrigee")


def _sans_doublons(rendus: list[tuple[dict, dict]]) -> list[dict]:
    """Garde-fou de publication contre le même PDF indexé deux fois — région ET national.

    Trois fiches (campus LCP, Corbeil-Essonnes) affichaient deux fois l'avis du 30 mars 2022,
    sous deux noms de fichier. La dédup VIT EN AMONT, dans pipelines/registers (run.dedup_contenu,
    testée) ; ici on ne réimplémente pas la règle, on APPELLE la sienne — deux écritures d'un
    même discriminant finiraient par diverger, et c'est au bord de la publication que l'écart
    coûterait le plus cher. Ce garde-fou doit mesurer zéro une fois le registre nettoyé : s'il
    attrape quelque chose, c'est que l'amont n'a pas tourné.

    L'empreinte se calcule sur le document BRUT du registre, pas sur les faits déjà filtrés de
    leurs mentions : c'est l'entrée qu'attend l'amont, et la même pour les deux couches.
    On garde l'exemplaire du registre régional — il porte le sha256, la licence et la procédure,
    là où l'index national n'a qu'un lien.
    """
    from pipelines.registers.run import _content_fp  # amont : une seule écriture de la règle

    garde: dict[str, dict] = {}
    for brut, rendu in rendus:
        fp = _content_fp(brut)
        if fp is None:  # aucun fait : rien à comparer, l'amont ne regroupe pas non plus
            continue
        tenu = garde.get(fp)
        if tenu is None or ("national" in (tenu["source"].get("origine") or "")
                            and "national" not in (rendu["source"].get("origine") or "")):
            garde[fp] = rendu
    retenus = {id(r) for r in garde.values()}
    gardes = [rendu for brut, rendu in rendus
              if _content_fp(brut) is None or id(rendu) in retenus]
    if len(gardes) < len(rendus):
        # Un garde-fou qui attrape quelque chose n'est pas une bonne nouvelle : il dit que
        # l'amont n'a pas été rejoué. Il le DIT, plutôt que de rattraper en silence.
        print(f"  ⚠ dossier environnemental : {len(rendus) - len(gardes)} doublon(s) rattrapé(s) "
              f"à la publication — rejouer la dédup du registre (pipelines/registers)")
    return gardes


def patch_dossier_environnemental() -> int:
    """L'avis d'autorité environnementale posé À CÔTÉ de la note (Franck 2026-10-01).

    Ce que l'État écrit sur un projet : les groupes électrogènes et leur fioul, le bruit
    mesuré avant travaux, la distance aux habitations et aux établissements scolaires, la
    chaleur fatale, et les réserves de l'autorité. Aucun de ces faits n'entre dans un
    indicateur ni dans une lettre — ils complètent la fiche, ils ne la notent pas.

    TROIS RÈGLES, et chacune a été payée.

    1. SEULS LES RATTACHEMENTS SÛRS VOYAGENT. On lit `rattachement.json` et on ne retient
       que `rattache_propose` et `rattache_multiple`. Les `a_confirmer` et les `ambigu`
       attendent un humain. Un rattachement faux ferait apparaître sur une fiche les
       chiffres d'un AUTRE projet — des faits justes, sur la mauvaise fiche, et rien dans
       la page ne trahirait l'erreur.

    2. UNE MENTION N'EST PAS UN FAIT. Les champs de présence — « NOx : mentionné »,
       « fluides frigorigènes : mentionné » — restent dans le JSON d'extraction, où ils
       qualifient une absence, et ne sortent JAMAIS sur la fiche : une puce « mentionné »
       n'apprend rien au lecteur et ressemble à une insinuation.

    3. ON N'ADDITIONNE RIEN. Un campus porte plusieurs puissances (Nozay : 75, 37,5 et
       15 MW) ; chacune garde sa phrase, qui nomme son bâtiment. Une somme serait un
       calcul, interdit dans une couche qui rapporte, et fausse ici : on ignore si les
       tranches sont simultanées.
    """
    ratt = CAL.parent / "registres" / "rattachement.json"
    if not ratt.is_file():
        return 0
    from engine.core import write_json
    doc = json.loads(ratt.read_text())
    reg = CAL.parent / "registres"

    # fiche_id -> liste de noms d'avis (un site peut en porter plusieurs)
    liens: dict[str, list[str]] = {}
    ecartes = 0
    for p in doc.get("propositions", []):
        if p.get("statut") not in ("rattache_propose", "rattache_multiple"):
            continue
        # LA MÊME COMMUNE N'EST PAS LE MÊME PROJET. Un avis d'origine nationale n'a qu'un
        # signal possible — l'index MRAe ne publie ni géométrie, ni pétitionnaire, ni INSEE
        # (cf. fiche.build_national) — alors le rapprochement par la seule commune l'accroche
        # à TOUS les data centers de la ville. Mesuré le 2026-10-01 : 4 avis dans ce cas, dont
        # « DC PA-16 Argenteuil » servi sur 3 fiches Equinix et un avis de La Courneuve sur 5.
        # Résultat à l'écran : une fiche affichant 22 groupes au fioul ET 18 groupes à l'HVO,
        # 30 salariés ET 40, sans que rien ne trahisse qu'il s'agit d'un AUTRE projet.
        # C'est exactement l'erreur contre laquelle le reste de cette fonction est écrit, et
        # j'avais pris `rattache_multiple` pour un gage de sûreté : c'en est un sur le NOMBRE
        # de fiches, pas sur la FORCE du lien.
        if set(p.get("signaux") or []) <= {"commune"}:
            ecartes += 1
            continue
        for fid in (p.get("fiches") or ([p["fiche"]] if p.get("fiche") else [])):
            liens.setdefault(fid, []).append(p["avis"])
    if ecartes:
        print(f"  dossier environnemental : {ecartes} avis écarté(s) — rattachés sur la seule "
              f"commune (voir pipelines/registers/match.py)")

    # Les champs de PRÉSENCE ne franchissent pas la frontière de la fiche (règle 2).
    MENTIONS = {
        "artificialisation", "bruit_emergence", "bruit_point_mesure", "bruit_zer",
        "cuves_enterrees", "eaux_pluviales", "especes_protegees", "essais_groupes",
        "etablissements_sensibles", "fluides_frigorigenes", "incendie", "natura2000",
        "nox", "pfas", "pollution_sols", "qualite_air_campagne", "rejets_aqueux",
        "trafic_pl", "zones_humides", "emplois_mention",
    }

    patched = 0
    for f in sorted((ARTIFACTS_DIR / "dc").glob("*.json")):
        d = json.loads(f.read_text())
        noms = liens.get(d["id"])
        if not noms:
            d.pop("dossier_environnemental", None)
            write_json(f, d)
            continue
        avis_rendus = []
        for nom in noms:
            src = reg / f"{nom}.json" if not nom.endswith(".json") else reg / nom
            if not src.is_file():
                continue
            a = json.loads(src.read_text())
            faits = [x for fs in a["installation"]["faits"].values() for x in fs
                     if x["indicateur"] not in MENTIONS and x["valeur"] is not True]
            if not faits and not a["installation"].get("recommandations_autorite"):
                continue
            proc = dict(a["procedure"])
            if not _date_publiable(a["source"], proc):
                proc.pop("date_avis", None)
            avis_rendus.append((a, {
                "source": a["source"], "procedure": proc, "faits": faits,
                "recommandations": a["installation"].get("recommandations_autorite", []),
            }))
        avis_rendus = _sans_doublons(avis_rendus)
        if avis_rendus:
            d["dossier_environnemental"] = {"avis": avis_rendus}
            patched += 1
        else:
            d.pop("dossier_environnemental", None)
        write_json(f, d)
    return patched


def patch_status_check() -> int:
    """Status proof (Franck 2026-09-17): every OPERATIONAL fiche artifact gets its
    status_check {verified, checked_at, evidence?} from the weekly sidecar written by
    `make status-proof`. Only the public verdict travels — the internal live_signal /
    demote candidates never reach a served file. No sidecar → nothing added (the fiche
    shows no status label rather than a wrong one)."""
    sidecar = CAL / "status-proof" / "status_check.json"
    if not sidecar.is_file():
        return 0
    from engine.core import write_json
    checks = json.loads(sidecar.read_text()).get("fiches", {})
    patched = 0
    for f in sorted((ARTIFACTS_DIR / "dc").glob("*.json")):
        d = json.loads(f.read_text())
        c = checks.get(d["id"])
        if d.get("project_status") != "operational" or not c or c.get("verdict") not in ("verified", "unverified"):
            d.pop("status_check", None)
        else:
            d["status_check"] = {
                "verified": c["verdict"] == "verified",
                "checked_at": c.get("checked_at"),
                **({"evidence": {k: c["evidence"][k] for k in ("source", "url", "networks")}}
                   if c["verdict"] == "verified" and c.get("evidence") else {}),
            }
            patched += 1
        write_json(f, d)
    return patched


def main() -> int:
    if not (CAL / "datacenters").is_dir():
        raise SystemExit(f"newsroom calibration not found at {CAL} — clone smdc-newsroom or set NEWSROOM_CAL")
    dcs = load_datacenters(CAL)          # every datacenters* panel (FR, BE, …)
    # The zz- fixtures NEVER ship to production (Franck 2026-07-17): they are
    # internal plumbing for CI and the public clone (`make score`), not
    # something visitors should meet. Prod = the real corpus only.
    # `study-` is the A-19 firewall belt-and-suspenders (R&D, 2026-09-06): the internal
    # precursor-validation cohort lives in a SEPARATE corpus (validation/, never read here) —
    # this prefix drop is the second lock, so a study fiche mistakenly copied into a
    # datacenters* panel still can NEVER be served with a real grade.
    dcs = {k: v for k, v in dcs.items() if not k.startswith(("zz-", "study-"))}
    watchlist = load_watchlist(CAL)      # "En veille" 🗣️ layer
    operator_sources = apply_operator_identity(dcs)
    developer_sources = apply_developer_identity(dcs)
    for dc in dcs.values():
        dc["identity"]["name"] = display_name(dc["identity"]["name"], dc["identity"].get("municipality"))
    for e in watchlist:
        e["name"] = display_name(e.get("name"), e.get("municipality"))
    results = build_artifacts(dcs, load_methodology(), out_dir=ARTIFACTS_DIR, watchlist=watchlist)
    # Purge stale per-DC artifacts (build_artifacts writes, never deletes):
    # anything on disk that is not in this corpus would silently resurrect
    # as a fiche page — the exact leak this script must prevent.
    stale = [f for f in (ARTIFACTS_DIR / "dc").glob("*.json") if f.stem not in dcs]
    for f in stale:
        f.unlink()
    if stale:
        print(f"prod-artifacts: purged {len(stale)} stale fiche artifact(s): " + ", ".join(f.stem for f in stale))
    de = sorted(i for i, r in results.items()
                if {r["grades"]["site"]["grade"], r["grades"]["project_process"]["grade"]} & {"D", "E"})
    print(f"prod-artifacts: {len(dcs)} DC + {len(watchlist)} watchlist entries → {ARTIFACTS_DIR}")
    print(f"prod-artifacts: exposure — {len(de)} DC(s) at D/E: " + (", ".join(de) if de else "none"))
    patch_operator_source(operator_sources)
    print(f"prod-artifacts: operator filled from the company register on {len(operator_sources)} fiches")
    patch_developer_source(developer_sources)
    print(f"prod-artifacts: developer fact on {len(developer_sources)} fiches (registre entreprises signé R&D, ou acte administratif)")
    dwell = patch_nearest_dwelling()
    print(f"prod-artifacts: nearest_dwelling on {dwell} fiches" if dwell
          else "prod-artifacts: nearest_dwelling skipped (no habitations sidecar — run make habitations)")
    dossiers = patch_dossier_environnemental()
    print(f"prod-artifacts: dossier environnemental sur {dossiers} fiches (avis d'autorité)")
    checked = patch_status_check()
    print(f"prod-artifacts: status_check on {checked} operational fiches"
          if checked else "prod-artifacts: status_check skipped (no status-proof sidecar — run make status-proof)")
    patched = patch_satellite_images()
    if patched:
        print(f"prod-artifacts: satellite_image patched on {patched} fiches (media env configured)")
    else:
        print("prod-artifacts: satellite_image skipped (SMDC_MEDIA_SECRET/BASE not set — see ~/.smdc/media.env)")
    stamped = patch_updated_at()
    print(f"prod-artifacts: updated_at on {stamped} fiches")
    ctx = patch_context_maps()
    print(f"prod-artifacts: context_map on {ctx} fiches (photo satellite annotée)" if ctx
          else "prod-artifacts: context_map skipped (aucune clé confirmée sur R2)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
