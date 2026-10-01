# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Le RATTACHEMENT : quel avis parle de quelle fiche du corpus.

Dernier maillon manquant. On a 39 avis d'un côté, 1 438 fiches de l'autre, et aucun lien :
le rattachement avait été retiré du JSON d'extraction à juste titre (« c'est de l'extraction,
pas de l'analyse ») et n'avait jamais été reconstruit ailleurs.

IL VIT DONC DANS SON PROPRE FICHIER, et c'est une décision, pas un fait. Le JSON d'extraction
reste ce qu'il est ; `rattachement.json` dit, séparément, ce qu'on croit relier à quoi, avec
quoi on le croit, et si un humain l'a confirmé.

RIEN N'EST AUTO-CONFIRMÉ. Le registre porte le centroïde du DOSSIER, notre corpus porte le
BÂTIMENT : à Tremblay l'écart est de 1,1 km, et c'est le même site. Une commune peut porter
deux data centers de deux opérateurs (Marcoussis, Marseille, Argenteuil en ont chacune au
moins deux dans notre corpus). Un rattachement faux ferait apparaître sur une fiche les
chiffres d'un autre projet — l'erreur la plus grave que ce chantier puisse produire, parce
qu'elle serait invisible : des faits justes, sur la mauvaise fiche.

QUATRE SIGNAUX, jamais un seul :
  · la GÉOMÉTRIE, quand le registre la porte (16 avis sur 39) ;
  · la COMMUNE, du champ quand il existe (15/39), sinon lue dans l'intitulé ;
  · le PÉTITIONNAIRE contre l'opérateur de la fiche (14/39) ;
  · les JETONS DISTINCTIFS de l'intitulé — « TH3 », « MRS5 », « ND1 », « PA16 » — qui
    nomment le bâtiment et tranchent là où la commune ne suffit pas.

Un avis dont deux candidats obtiennent le même meilleur score est déclaré AMBIGU et attend
un humain. Mieux vaut trente rattachements sûrs et neuf questions qu'un lot complet dont on
ne sait pas lequel est faux.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

# Le registre porte le centroïde du DOSSIER, le corpus le bâtiment : 1,1 km d'écart sur
# Tremblay, qui est pourtant le même site. On ratisse large et on classe, on ne tranche pas
# sur la distance seule.
RAYON_M = 3000.0
# En deçà, la géométrie est si proche qu'elle suffit même sans autre signal.
RAYON_CERTAIN_M = 400.0


def _slug(s: str | None) -> str:
    s = unicodedata.normalize("NFKD", (s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _mots(s: str | None) -> set[str]:
    return {m for m in _slug(s).split() if len(m) > 2}


# Formes juridiques et mots de remplissage : ils ne distinguent personne et font croire à une
# ressemblance là où il n'y en a pas (« … France », « … Services » matchent tout le monde).
_HABILLAGE = re.compile(
    r"\b(sas|sa|sarl|snc|sci|scs|ltd|limited|gmbh|bv|nv|inc|llc|plc|group|groupe|"
    r"france|french|international|corporation|corp|company|technology|technologies|"
    r"services|service|developments|development|societe|projet|project)\b")


def _enseigne(s: str | None) -> str:
    """Le nom de marque, condensé et débarrassé de son habillage juridique.

    « DATA 4 SAS » et « Data4 » désignent le même exploitant, mais une comparaison mot à mot
    les manque : « data 4 sas » n'a aucun mot commun de plus de deux lettres avec « data4 ».
    On condense donc tout (« data4sas » → « data4 ») et on compare par INCLUSION, ce qui
    rattrape aussi « Telehouse International Corporation Of Europe » contre « Telehouse ».
    """
    return re.sub(r"[^a-z0-9]", "", _HABILLAGE.sub(" ", _slug(s)))


def _meme_exploitant(a: str | None, b: str | None) -> bool:
    ea, eb = _enseigne(a), _enseigne(b)
    if len(ea) < 4 or len(eb) < 4:
        return False
    return ea in eb or eb in ea


def _haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


# Jetons qui NOMMENT un bâtiment plutôt qu'un lieu : « TH3 », « MRS5 », « PA16 », « ND1 ».
# Ce sont eux qui départagent deux data centers d'une même commune.
_JETON = re.compile(r"\b([a-z]{1,4}\d{1,3}[a-z]?)\b")


def _jetons(s: str | None) -> set[str]:
    return {m for m in _JETON.findall(_slug(s)) if not m.isdigit()}


@dataclass
class Candidat:
    fiche: str
    commune_fiche: str | None = None
    distance_m: float | None = None
    signaux: list[str] = field(default_factory=list)

    @property
    def score(self) -> int:
        return len(self.signaux)


@dataclass
class Proposition:
    avis: str
    intitule: str
    retenu: str | None = None
    distance_m: float | None = None
    signaux: list[str] = field(default_factory=list)
    statut: str = "non_rattache"      # rattache_propose | rattache_multiple | a_confirmer | ambigu | non_rattache
    fiches: list[str] = field(default_factory=list)   # rattache_multiple : le site, pas un bâtiment
    autres: list[dict] = field(default_factory=list)
    confirme: bool = False            # JAMAIS vrai sans relecture humaine
    exploitant_document: str | None = None   # l'exploitant lu DANS le PDF, pas dans le registre

    def as_dict(self) -> dict:
        d = {"avis": self.avis, "intitule": self.intitule[:120], "statut": self.statut,
             "confirme": self.confirme}
        if self.fiches:
            d["fiches"] = self.fiches
        if self.retenu:
            d["fiche"] = self.retenu
            d["signaux"] = self.signaux
            if self.distance_m is not None:
                d["distance_m"] = round(self.distance_m)
        if self.autres:
            d["autres_candidats"] = self.autres
        return d


def _communes_du_corpus(corpus: dict[str, dict]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for fid, f in corpus.items():
        c = _slug(f.get("municipality"))
        if c:
            out.setdefault(c, []).append(fid)
    return out


def _commune_de_lavis(proc: dict, nom_fichier: str, communes: dict[str, list[str]]) -> str | None:
    """La commune du champ quand elle existe ; sinon lue dans l'intitulé ou le nom de fichier.

    Vingt-trois avis sur trente-neuf viennent de l'index national, qui ne porte pas de commune.
    Mais leur intitulé la contient presque toujours — « …tremblay-en-france… », « …nozay-91… ».
    On cherche donc les communes CONNUES du corpus dans le texte, en commençant par les plus
    longues : « magny-les-hameaux » doit l'emporter sur « magny ».
    """
    direct = _slug(proc.get("commune"))
    if direct and direct in communes:
        return direct
    foin = _slug(f"{proc.get('intitule') or ''} {nom_fichier}")
    for c in sorted(communes, key=len, reverse=True):
        if len(c) > 4 and re.search(rf"\b{re.escape(c)}\b", foin):
            return c
    return direct or None


def proposer(avis_docs: dict[str, dict], corpus: dict[str, dict]) -> list[Proposition]:
    """corpus : {fiche_id: {municipality, operator, coordinates{lat,lon}}}."""
    communes = _communes_du_corpus(corpus)
    propositions: list[Proposition] = []

    for nom, doc in sorted(avis_docs.items()):
        proc = doc.get("procedure") or {}
        intitule = proc.get("intitule") or nom
        p = Proposition(avis=nom, intitule=intitule)
        centro = proc.get("centroid")
        commune = _commune_de_lavis(proc, nom, communes)
        jetons = _jetons(f"{intitule} {nom}")

        cands: list[Candidat] = []
        for fid, f in corpus.items():
            c = Candidat(fiche=fid, commune_fiche=f.get("municipality"))
            coords = f.get("coordinates") or {}
            if centro and coords:
                d = _haversine_m((centro["lat"], centro["lon"]), (coords["lat"], coords["lon"]))
                if d <= RAYON_M:
                    c.distance_m = d
                    c.signaux.append("geometrie")
                    if d <= RAYON_CERTAIN_M:
                        c.signaux.append("geometrie_proche")
            if commune and _slug(f.get("municipality")) == commune:
                c.signaux.append("commune")
            if _meme_exploitant(proc.get("petitionnaire"), f.get("operator")):
                c.signaux.append("petitionnaire")
            if jetons and jetons & _jetons(fid):
                c.signaux.append("jeton_batiment")
            if c.signaux:
                cands.append(c)

        if not cands:
            propositions.append(p)
            continue

        cands.sort(key=lambda c: (-c.score, c.distance_m if c.distance_m is not None else 9e9))
        meilleur = cands[0]
        exaequo = [c for c in cands[1:] if c.score == meilleur.score]

        p.retenu = meilleur.fiche
        p.distance_m = meilleur.distance_m
        p.signaux = meilleur.signaux
        p.autres = [{"fiche": c.fiche, "signaux": c.signaux,
                     **({"distance_m": round(c.distance_m)} if c.distance_m is not None else {})}
                    for c in cands[1:5]]

        # Un ex æquo de SCORE n'est pas forcément une ambiguïté : si le premier est à 300 m et
        # le suivant à 2 km, la géométrie les départage. On ne déclare ambigu que lorsque le
        # concurrent est VRAIMENT comparable — même score ET pas nettement plus loin.
        def indiscernable(c: Candidat) -> bool:
            if meilleur.distance_m is None or c.distance_m is None:
                return True
            return c.distance_m <= max(meilleur.distance_m * 2, meilleur.distance_m + 500)

        rivaux = [c for c in exaequo if indiscernable(c)]

        if rivaux:
            # TOUS les rivaux appartiennent-ils au MÊME exploitant, sur la MÊME commune ?
            # Alors ce n'est pas une ambiguïté : l'avis décrit un SITE que notre corpus
            # découpe en plusieurs bâtiments (Interxion a quatre fiches à La Courneuve,
            # Colt quatre à Villebon). Choisir l'une d'elles au hasard serait arbitraire et
            # faux ; les rattacher toutes dit la vérité — ce dossier environnemental couvre
            # ce site. Mesuré : 10 des 20 cas « ambigus » sont de cette nature.
            lot = [meilleur] + rivaux
            noms = [corpus[c.fiche].get("operator") for c in lot]
            connus = [n for n in noms if _enseigne(n) and _enseigne(n) != "unknown"]
            # Homogène si toutes les enseignes connues se reconnaissent entre elles. On compare
            # par ENSEIGNE et non par chaîne exacte : « Cloud HQ FRANCE » et « CloudHQ » sont
            # le même exploitant, et une égalité stricte les aurait déclarés en conflit.
            homogene = all(_meme_exploitant(connus[0], n) for n in connus[1:]) if connus else False
            communes_lot = {_slug(corpus[c.fiche].get("municipality")) for c in lot}
            if homogene and len(communes_lot) == 1:
                p.statut = "rattache_multiple"
                p.fiches = [c.fiche for c in lot]
            else:
                p.statut = "ambigu"
        elif meilleur.score >= 2 or "geometrie_proche" in meilleur.signaux:
            p.statut = "rattache_propose"
        elif len(cands) == 1:
            # Un seul candidat, un seul signal : ce n'est pas ambigu — il n'y a personne
            # d'autre — mais ce n'est pas démontré non plus. Une commune peut abriter un data
            # center que notre corpus ignore, et l'avis parlerait alors de celui-là. Statut
            # distinct, pour que la relecture humaine sache qu'elle arbitre une VRAISEMBLANCE
            # et non un choix entre deux.
            p.statut = "a_confirmer"
        else:
            p.statut = "ambigu"
        propositions.append(p)

    return propositions


def projets_candidats(propositions: list[Proposition]) -> list[dict]:
    """Les avis qui ne correspondent à AUCUNE fiche : des projets que l'État documente et
    que notre corpus ignore.

    C'est une SORTIE à part entière, pas un reliquat. Le premier passage en a trouvé cinq —
    DIGITAL MRS5 et SEGRO Urban Logistics à Marseille, le Village Delage à Courbevoie (deux
    avis), un programme mixte à Vélizy — et ils ont été repérés À LA MAIN, en lisant les PDF
    un par un. Un détecteur qui ne vit que dans la tête de celui qui a fait le run ne détecte
    rien au run suivant : il est donc ici, nommé, et il écrit son fichier à chaque passage.

    DEUX CAS, et le second est le plus utile :
      · `non_rattache` — aucun candidat dans le rayon ni dans la commune ;
      · `projet_absent_du_corpus` — des candidats existaient, mais l'EXPLOITANT nommé par le
        document ne correspond à aucun d'eux. C'est le cas des cinq : la commune était la
        bonne, les fiches voisines aussi, et pourtant l'avis parlait d'un autre site.
    """
    return [
        {"avis": p.avis, "intitule": p.intitule[:160], "statut": p.statut,
         "exploitant_dans_le_document": p.exploitant_document,
         "communes_candidates": [c["fiche"] for c in p.autres[:4]] or None}
        for p in propositions
        if p.statut in ("non_rattache", "projet_absent_du_corpus")
    ]


def ecrire(propositions: list[Proposition], out: Path, date: str) -> dict:
    par_statut: dict[str, int] = {}
    for p in propositions:
        par_statut[p.statut] = par_statut.get(p.statut, 0) + 1
    candidats = projets_candidats(propositions)
    doc = {
        "schema": "smdc.registre-ae.rattachement/1",
        "genere_le": date,
        "note": ("PROPOSITIONS, pas des faits. Un rattachement faux ferait apparaître sur une "
                 "fiche les chiffres d'un autre projet — des faits justes, sur la mauvaise "
                 "fiche. Rien n'est servi tant que `confirme` n'est pas passé à true par un "
                 "humain."),
        "resume": par_statut,
        "propositions": [p.as_dict() for p in propositions],
        # Sortie à part entière : les projets que l'État documente et que notre corpus ignore.
        # Elle est ÉCRITE À CHAQUE PASSAGE, pour que la détection ne dépende pas de qui lance
        # le run ni de ce qu'il a remarqué ce jour-là.
        "projets_a_collecter": candidats,
    }
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return doc
