"""Candidate-material search for growing the KG beyond the ~22 hand-curated materials.

Two independent pieces, used together by scripts/populate_kg_ont.py:

1. `sweep_candidates()` — issues a set of *targeted* Materials Project searches by
   **stoichiometric ratio pattern** ("anonymous formula", e.g. "ABC2" for a 1:1:2 compound like
   LiCoO2), not by element list. This matters: an early version of this sweep searched by element
   set alone ("contains Li, Co, O") and pulled back every stoichiometry the Li-Co-O phase diagram
   has (Li2CoO3, LiCo2O4, Co3O4, ...) -- only ~18% of which matched a real structure-family ratio.
   Searching by the exact ratio a structure family is defined by (still requiring the right anion
   elements be present) finds the compounds that could plausibly BE that family directly, in one
   API call per family instead of one per (alkali, metal) pair. Whether a hit's *symmetry* also
   matches (see structure_family_mapper.py) is still decided locally, per material, after fetch --
   this only narrows the *stoichiometry*, which is necessary but not sufficient on its own.

   A separate, deliberately unconstrained "diversity" pull is included too, so the KG isn't only
   prototype-shaped compounds.

2. `pick_representative_polymorph()` — a single formula (e.g. "LiCoPO4") can have dozens of
   Materials Project entries, one per DFT-relaxed polymorph. We need exactly one to represent that
   formula in the KG. See BUILD_LOG.md Step 4 for why "lowest computed energy" alone is the wrong
   default (it can pick a purely theoretical low-symmetry relaxation over the real, experimentally
   verified structure) and what we do instead.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Fields we need at the *candidate* stage. Deliberately excludes "structure" (heavy) -- that's
# fetched once per selected material by MPIngester, not once per candidate here.
_LIGHT_FIELDS = ["material_id", "formula_pretty", "composition", "energy_above_hull", "is_stable", "theoretical", "nelements", "nsites"]

# Ceiling on energy above the computed convex hull (eV/atom). Real, synthesizable battery
# materials are essentially always within this range; higher than this is usually a DFT artifact
# rather than a material anyone could make. Matches the ~0.05 eV/atom range we saw on real
# curated cathodes in Step 4, with headroom.
_E_HULL_CEILING = 0.15
_MAX_SITES = 40


@dataclass
class RatioSweep:
    """One 'find compounds shaped like this' search: a stoichiometric ratio pattern (Materials
    Project's anonymous-formula notation, e.g. "ABC2" = three distinct elements in a 1:1:2 count
    ratio) plus the anion element(s) that must be present. The ratio pattern is anonymous -- it
    doesn't pin which element fills which slot -- so hits still need local, per-material chemical
    + symmetry checks (structure_family_mapper.py) before being labelled anything. This sweep only
    narrows candidates to the right *shape*.
    """
    family_hint: str          # just for logging -- the real classification happens later, locally
    pattern: str               # e.g. "ABC2"
    required_anion_elements: list[str]   # e.g. ["O"], ["P", "O"], ["S"]
    alkalis: list[str]          # which working ions to search this pattern for


_RATIO_SWEEPS = [
    # Discovered by asking Materials Project for the formula_anonymous of our own curated
    # examples (LiCoO2, LiMn2O4, CaTiO3, LiFePO4, Na3V2(PO4)3, Li7La3Zr2O12, Li10GeP2S12,
    # Li6PS5Cl) rather than derived by hand -- see BUILD_LOG.md Step 5.
    RatioSweep("layered oxide / rock salt (ABC2, e.g. LiCoO2)", "ABC2", ["O"], ["Li", "Na"]),
    RatioSweep("spinel (AB2C4, e.g. LiMn2O4)", "AB2C4", ["O"], ["Li", "Na"]),
    RatioSweep("perovskite (ABC3, e.g. CaTiO3)", "ABC3", ["O"], ["Li", "Na"]),
    RatioSweep("olivine (ABCD4, e.g. LiFePO4)", "ABCD4", ["P", "O"], ["Li", "Na"]),
    RatioSweep("NASICON (A2B3C3D12, e.g. Na3V2(PO4)3)", "A2B3C3D12", ["P", "O"], ["Li", "Na"]),
    RatioSweep("garnet (A2B3C7D12, e.g. Li7La3Zr2O12)", "A2B3C7D12", ["O"], ["Li"]),
    RatioSweep("LGPS-type (AB2C10D12, e.g. Li10GeP2S12)", "AB2C10D12", ["S"], ["Li"]),
    RatioSweep("argyrodite (ABC5D6, e.g. Li6PS5Cl)", "ABC5D6", ["S"], ["Li"]),
]


def sweep_candidates(mpr, diversity_pool_size: int = 30, per_sweep_chunk: int = 100) -> dict[str, list]:
    """Run every ratio-pattern sweep plus a small unconstrained diversity pool.

    Returns {formula_pretty: [list of lightweight MP docs for that formula]} -- callers pick one
    representative polymorph per formula with pick_representative_polymorph().
    """
    by_formula: dict[str, list] = {}
    calls = [(sweep, alkali) for sweep in _RATIO_SWEEPS for alkali in sweep.alkalis]
    logger.info(f"Running {len(calls)} ratio-pattern searches ({len(_RATIO_SWEEPS)} families x their alkalis)...")
    for sweep, alkali in calls:
        try:
            docs = mpr.materials.summary.search(
                formula=sweep.pattern, elements=[alkali, *sweep.required_anion_elements],
                energy_above_hull=(0, _E_HULL_CEILING), num_sites=(1, _MAX_SITES),
                fields=_LIGHT_FIELDS, num_chunks=None, chunk_size=per_sweep_chunk,
            )
        except Exception as e:
            logger.warning(f"Sweep [{sweep.family_hint}] alkali={alkali} failed: {e}")
            continue
        for d in docs:
            by_formula.setdefault(d.formula_pretty, []).append(d)
        logger.info(f"  [{sweep.family_hint}] alkali={alkali}: {len(docs)} hits -> {len(by_formula)} distinct formulas so far")

    logger.info(f"Ratio-pattern sweeps done: {len(by_formula)} distinct formulas.")

    # Diversity pool: broader, unconstrained-by-ratio pull so the KG isn't only prototype-shaped
    # compounds. Small on purpose -- most of these will end up with no structure-family label,
    # which is fine (honest) but shouldn't dominate the KG.
    try:
        docs = mpr.materials.summary.search(
            elements=["Li"], is_stable=True, num_elements=(2, 4), num_sites=(1, _MAX_SITES),
            fields=_LIGHT_FIELDS, num_chunks=1, chunk_size=diversity_pool_size,
        )
        for d in docs:
            by_formula.setdefault(d.formula_pretty, []).append(d)
        logger.info(f"Diversity pool added ({len(docs)} hits); {len(by_formula)} distinct formulas total.")
    except Exception as e:
        logger.warning(f"Diversity pool search failed: {e}")

    return by_formula


def pick_representative_polymorph(docs: list) -> tuple:
    """Pick ONE Materials Project entry to represent a formula that has several polymorphs.

    Priority (see BUILD_LOG.md Step 4 for why):
      1. On the convex hull (is_stable=True) -- the DFT-predicted most stable arrangement.
      2. Else, among entries Materials Project has matched to a real experimental structure
         (theoretical=False), the lowest-energy one. Prefers a REAL, synthesized structure over a
         computationally lower-energy hypothetical one -- battery cathodes routinely sit a little
         above the 0K hull without that meaning they don't exist.
      3. Else, lowest energy above hull overall (all entries are theoretical-only).
      4. Else, whatever came back first.

    Returns (doc, reason_string).
    """
    stable = [d for d in docs if d.is_stable]
    if stable:
        return min(stable, key=lambda d: d.energy_above_hull), "on convex hull (is_stable)"
    verified = [d for d in docs if d.theoretical is False]
    if verified:
        return min(verified, key=lambda d: d.energy_above_hull), "experimentally verified (ICSD-matched), lowest E_above_hull among those"
    if docs:
        return min(docs, key=lambda d: (d.energy_above_hull if d.energy_above_hull is not None else 1e9)), "lowest E_above_hull (all entries theoretical-only)"
    return None, None
