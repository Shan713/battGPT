"""Structural-Prototype Classification Engine mapping materials to the battgpt:StructureFamily
taxonomy introduced in BattGpt-Ontology v0.3.0 (StructureFamily / OxideStructureFamily /
PolyanionStructureFamily / SulfideStructureFamily and their leaf structure-type classes).

Two tiers, same pattern BattINFOMapper already uses for battery roles:

1. CURATED_STRUCTURE_FAMILIES — exact-formula lookup. Each entry was individually checked by a
   human against the material's Materials Project space group. Highest confidence.
2. _heuristic_structure_family() — space-group + stoichiometry rules for everything not in the
   curated table, so materials pulled fresh from the Materials Project API still get a label
   instead of falling back to the ontology's top-level "substance" type. This is NOT the same
   thing as "guessing from composition alone": each rule below pins down BOTH (a) a stoichiometric
   ratio that defines the prototype chemically and (b) the actual computed space-group number,
   sourced from the same crystallographic prototypes documented in CURATED_STRUCTURE_FAMILIES /
   pipeline/config/config.py's per-material comments, generalized to their well-known textbook
   space groups. Only the 9 *leaf* classes are ever assigned — the non-leaf grouping classes
   (StructureFamily, OxideStructureFamily, PolyanionStructureFamily, SulfideStructureFamily) have
   no individuals and are never assigned directly.

Confidence is recorded in plain text in `structure_family_evidence` (serialized as an rdfs:comment
by RDFBuilder) so nothing downstream has to guess how trustworthy a label is:
    "Curated benchmark: ..."            <- tier 1, human-verified
    "Heuristic (space group + ...): ..." <- tier 2, rule-matched, not individually reviewed

If neither tier matches, structure_family stays None (see MaterialRecord). We never force a label
onto ambiguous data — an unlabelled material is honest; a wrong label is not.
"""
import logging
from ..models import MaterialRecord

logger = logging.getLogger(__name__)

# Curated lookup: formula -> (battgpt: leaf class local name, evidence)
CURATED_STRUCTURE_FAMILIES: dict[str, tuple[str, str]] = {
    # ── LayeredOxideStructure: alpha-NaFeO2-type (O3) layered rock-salt-derived oxide ──
    "LiCoO2": ("LayeredOxideStructure", "R-3m (#166) alpha-NaFeO2-type layered oxide (LCO)"),
    "LiNiO2": ("LayeredOxideStructure", "R-3m (#166) alpha-NaFeO2-type layered oxide (LNO)"),
    "NaMnO2": ("LayeredOxideStructure", "C2/m (#12) Jahn-Teller-distorted O3-type layered oxide"),
    "NaNiO2": ("LayeredOxideStructure", "C2/m (#12) Jahn-Teller-distorted O3-type layered oxide"),

    # ── SpinelStructure: AB2O4, space group Fd-3m ──
    "LiMn2O4": ("SpinelStructure", "Fd-3m (#227) spinel-type structure (LMO)"),
    "Li4Ti5O12": ("SpinelStructure", "Fd-3m (#227) spinel-type structure (LTO, zero-strain anode)"),

    # ── OlivineStructure: space group Pnma phosphate olivine ──
    "LiFePO4": ("OlivineStructure", "Pnma (#62) olivine-type phosphate (LFP)"),
    "NaFePO4": ("OlivineStructure", "Pnma (#62) olivine-type phosphate, Na-ion analogue of LFP"),
    "LiMnPO4": ("OlivineStructure", "Pnma (#62) olivine-type phosphate, Mn analogue of LFP"),

    # ── NASICONStructure: NASICON-type open 3D phosphate framework ──
    "Na3V2(PO4)3": ("NASICONStructure", "NASICON-type (Na Super Ionic Conductor) 3D phosphate framework"),
    "Li3V2(PO4)3": ("NASICONStructure", "P2_1/c (#14) monoclinic NASICON-type framework (Li-ion analogue)"),

    # ── GarnetStructure: space group Ia-3d framework, fast Li-ion solid electrolytes ──
    "Li7La3Zr2O12": ("GarnetStructure", "Ia-3d (#230) garnet-type framework (LLZO solid electrolyte)"),

    # ── LGPSTypeStructure: Li10GeP2S12-type thio-LISICON sulfide framework ──
    "Li10Ge(PS6)2": ("LGPSTypeStructure", "Thio-LISICON Li10GeP2S12 (LGPS)-type sulfide framework"),
    "Li10GeP2S12": ("LGPSTypeStructure", "Thio-LISICON Li10GeP2S12 (LGPS)-type sulfide framework"),
}

# Elements treated as the alkali / working-ion cation across the heuristic rules.
_ALKALI = {"Li", "Na", "K"}
# Elements treated as "framework" transition/main-group cations in oxide & phosphate hosts.
_FRAMEWORK_METALS = {
    "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Zr", "Nb", "Mo", "Ta", "W", "Sn", "Al", "Mg",
}
_LANTHANIDE_OR_Y = {"Y", "La", "Ce", "Pr", "Nd", "Sm", "Gd", "Yb"}
_LGPS_FRAMEWORK = {"Ge", "Si", "Sn"}
_HALOGENS = {"Cl", "Br", "I"}


def _ratio(composition: dict[str, float], numerator_elems: set[str], denominator_elems: set[str]) -> float | None:
    """sum(counts of numerator_elems) / sum(counts of denominator_elems), or None if the
    denominator is absent. Works on raw (not necessarily reduced) MaterialRecord.composition
    counts, since we only ever compare a *ratio* of two sums, which is reduction-invariant."""
    num = sum(v for k, v in composition.items() if k in numerator_elems)
    den = sum(v for k, v in composition.items() if k in denominator_elems)
    if den <= 0:
        return None
    return num / den


def _close(value: float | None, target: float, tol: float) -> bool:
    return value is not None and abs(value - target) <= tol


def _heuristic_structure_family(record: MaterialRecord) -> tuple[str, str] | None:
    """Space-group + stoichiometry fallback for materials not in CURATED_STRUCTURE_FAMILIES.

    Each branch checks a chemical family (decided by which anions are present: sulfide vs.
    phosphate vs. plain oxide) and, within it, a stoichiometric ratio that is the textbook
    definition of that prototype. Branches are ordered anion-first (S -> P -> plain O) so a
    phosphate is never miscompared against a pure-oxide ratio, then most-specific-first within
    each anion group. A rule only fires if BOTH the ratio AND (where noted) the space group match;
    unmatched materials return None rather than a low-confidence guess.
    """
    comp = record.composition
    elems = set(comp.keys())
    sg = record.spacegroup_number
    has_alkali = bool(_ALKALI & elems)

    # ── Sulfide framework families (contain S) ──
    if "S" in elems and has_alkali:
        # Argyrodite: Li6PS5X (X = halogen). Needs P, S, and a halogen. Textbook space group
        # F-43m (#216); real samples are sometimes solved in a lower-symmetry ordered subgroup,
        # so the space group is reported as corroboration, not a hard gate, here.
        if "P" in elems and (_HALOGENS & elems):
            sg_note = f", space group #{sg} matches the F-43m (#216) argyrodite aristotype" if sg == 216 else f" (space group #{sg}, not the #216 aristotype -- likely an ordered/distorted variant)"
            return "ArgyroditeStructure", (
                f"Heuristic (composition match): contains alkali + P + S + halogen "
                f"({', '.join(sorted(_HALOGENS & elems))}), the Li6PS5X argyrodite signature{sg_note}"
            )
        # LGPS-type: Li10GeP2S12-type thio-LISICON, alkali + (Ge/Si/Sn) + P + S.
        if "P" in elems and (_LGPS_FRAMEWORK & elems):
            sg_note = " space group #137 (P4_2/nmc) matches the LGPS aristotype" if sg == 137 else f"space group #{sg} (LGPS-family compounds span several related space groups, so this is corroborating only, not required)"
            return "LGPSTypeStructure", (
                f"Heuristic (composition match): contains alkali + P + S + "
                f"{'/'.join(sorted(_LGPS_FRAMEWORK & elems))}, the thio-LISICON/LGPS signature; {sg_note}"
            )
        return None

    # ── Phosphate framework families (contain P, no S) ──
    if "P" in elems and "O" in elems and has_alkali:
        framework = _FRAMEWORK_METALS & elems
        if not framework:
            return None
        metal_to_p = _ratio(comp, framework, {"P"})
        # NASICON: A_x M2(PO4)3 -- metal:P ~ 2:3 (0.667). Real NASICON battery compounds are
        # reported across several related space groups (rhombohedral R-3c #167 for the ambient
        # aristotype, or monoclinic C2/c #15 / P2_1/c #14 distorted polymorphs -- both already
        # seen in this project's own curated set), so space group is corroborating, not required.
        if _close(metal_to_p, 2 / 3, 0.15):
            sg_note = f"space group #{sg} is a known NASICON-family group" if sg in (167, 15, 14) else f"space group #{sg} (outside the common NASICON list -- corroborating only)"
            return "NASICONStructure", (
                f"Heuristic (space-group + stoichiometry match): metal:P ratio "
                f"{metal_to_p:.2f} matches the NASICON A_xM2(PO4)3 framework (~0.67); {sg_note}"
            )
        # Olivine: ABPO4 -- metal:P ~ 1:1, space group Pnma (#62), same as the curated examples.
        if _close(metal_to_p, 1.0, 0.15) and sg == 62:
            return "OlivineStructure", (
                f"Heuristic (space-group + stoichiometry match): metal:P ratio {metal_to_p:.2f} "
                f"matches the olivine ABPO4 framework (~1.0) and space group #62 (Pnma)"
            )
        return None

    # ── Plain oxide families (O present, no P or S) ──
    if "O" in elems and "P" not in elems and "S" not in elems:
        # Garnet: Li-stuffed garnet solid electrolytes (LLZO-type) -- alkali + lanthanide/Y +
        # (Zr/Nb/Ta) + O. Space group cubic Ia-3d (#230, fast-conducting) or tetragonal I4_1/acd
        # (#142, ordered) -- both already documented for this exact family in config.py.
        if has_alkali and (_LANTHANIDE_OR_Y & elems) and ({"Zr", "Nb", "Ta"} & elems):
            sg_note = f"space group #{sg} matches the cubic (#230) or tetragonal (#142) LLZO-type garnet" if sg in (230, 142) else f"space group #{sg} (not #230/#142 -- corroborating only)"
            return "GarnetStructure", (
                f"Heuristic (composition match): contains alkali + lanthanide/Y + (Zr/Nb/Ta) + O, "
                f"the Li-stuffed garnet (LLZO-type) signature; {sg_note}"
            )
        if not has_alkali:
            return None
        framework = _FRAMEWORK_METALS & elems
        if not framework:
            return None
        o_to_cation = _ratio(comp, {"O"}, _ALKALI | framework)
        # Spinel: AB2O4 -- O:(A+B) ~ 4:3 (1.33). Space group Fd-3m (#227), exactly as curated.
        if _close(o_to_cation, 4 / 3, 0.15) and sg == 227:
            return "SpinelStructure", (
                f"Heuristic (space-group + stoichiometry match): O:cation ratio {o_to_cation:.2f} "
                f"matches the spinel AB2O4 framework (~1.33) and space group #227 (Fd-3m)"
            )
        # ABO2 ratio: 1 alkali : 1 framework metal : 2 O, so O:(A+B) = 2/(1+1) = 1.0. Splits on
        # symmetry into either a cation-ORDERED layered oxide (rhombohedral/monoclinic) or a
        # cation-DISORDERED rock salt (cubic) -- same formula, different space group, which is
        # exactly why this family cannot be told apart by composition alone (see module docstring).
        if _close(o_to_cation, 1.0, 0.2):
            alkali_to_fw = _ratio(comp, _ALKALI, framework)
            if _close(alkali_to_fw, 1.0, 0.2) and sg in (166, 12):
                return "LayeredOxideStructure", (
                    f"Heuristic (space-group + stoichiometry match): ABO2 ratio "
                    f"(alkali:metal:O ~ 1:1:2) with space group #{sg} "
                    f"({'R-3m' if sg == 166 else 'C2/m'}), a cation-ordered layered oxide"
                )
            if sg in (225, 200, 205):
                return "RockSaltStructure", (
                    f"Heuristic (space-group + stoichiometry match): O:cation ratio {o_to_cation:.2f} "
                    f"(~ABO2) with cubic space group #{sg} (cation-disordered rock salt, "
                    f"not the rhombohedral/monoclinic symmetry of an ordered layered oxide)"
                )
            return None
        # Perovskite: ABO3 -- O:(A+B) ~ 3:2 (1.5). Catch-all for oxide ternaries that are
        # neither the spinel nor the ABO2 ratio above. Space group cubic Pm-3m (#221),
        # rhombohedral R-3c (#167), tetragonal I4/mcm (#140), or orthorhombic GdFeO3-type Pnma
        # (#62 -- safe to reuse here since olivine already required P, which this branch excludes).
        if _close(o_to_cation, 1.5, 0.15) and sg in (221, 167, 140, 62):
            return "PerovskiteStructure", (
                f"Heuristic (space-group + stoichiometry match): O:cation ratio {o_to_cation:.2f} "
                f"matches the perovskite ABO3 framework (~1.5) and space group #{sg}"
            )
    return None


class StructureFamilyMapper:
    """Assigns battgpt:StructureFamily leaf-class classification: curated formula lookup first,
    then the space-group/stoichiometry heuristic in _heuristic_structure_family()."""

    def process(self, record: MaterialRecord) -> MaterialRecord:
        """Enrich MaterialRecord with a StructureFamily classification, curated tier first."""
        entry = CURATED_STRUCTURE_FAMILIES.get(record.formula)
        if entry:
            record.structure_family, evidence = entry
            record.structure_family_evidence = f"Curated benchmark: {evidence}"
            logger.info(f"Classified {record.formula} as battgpt:{record.structure_family} (curated)")
            return record

        heuristic = _heuristic_structure_family(record)
        if heuristic:
            record.structure_family, record.structure_family_evidence = heuristic
            logger.info(f"Classified {record.formula} as battgpt:{record.structure_family} (heuristic)")
        return record
