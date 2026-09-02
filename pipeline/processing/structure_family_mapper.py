"""Structural-Prototype Classification Engine mapping materials to the battgpt:StructureFamily
taxonomy introduced in BattGpt-Ontology v0.3.0 (StructureFamily / OxideStructureFamily /
PolyanionStructureFamily / SulfideStructureFamily and their leaf structure-type classes).

Curated lookup only, by formula: each entry below is a real, well-documented crystallographic
classification (verified against the material's Materials Project space group), not a guess from
composition alone. Only the 9 *leaf* classes are ever assigned to a material — the non-leaf
grouping classes (StructureFamily, OxideStructureFamily, PolyanionStructureFamily,
SulfideStructureFamily) have no individuals and are never assigned directly, matching how the
ontology itself only declares NamedIndividuals for the 9 leaf classes.
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


class StructureFamilyMapper:
    """Assigns battgpt:StructureFamily leaf-class classification via curated formula lookup."""

    def process(self, record: MaterialRecord) -> MaterialRecord:
        """Enrich MaterialRecord with a StructureFamily classification if the formula is curated."""
        entry = CURATED_STRUCTURE_FAMILIES.get(record.formula)
        if entry:
            record.structure_family, record.structure_family_evidence = entry
            logger.info(f"Classified {record.formula} as battgpt:{record.structure_family}")
        return record
