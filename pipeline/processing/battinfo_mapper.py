"""BattINFO Semantic Mapping Engine with Provenance Tracking & Categorical Heuristics."""
import logging
from ..models import MaterialRecord

logger = logging.getLogger(__name__)

# EMMO / BattINFO IRIs
POSITIVE_ELECTRODE_IRI = "https://w3id.org/emmo/domain/battery#battery_b8f04fd5_8741_4d17_9713_931d752c0021"
NEGATIVE_ELECTRODE_IRI = "https://w3id.org/emmo/domain/battery#battery_0a37db91_6c02_4eb4_9b2d_e8a2a02b1f85"
ELECTROLYTE_IRI = "https://w3id.org/emmo/domain/battery#battery_b69c4c79_463e_436b_8b59_5b067f9446d6"
SEPARATOR_IRI = "https://w3id.org/emmo/domain/battery#battery_13e9a59b_2ef4_4a2a_b5e5_d9a8c27bc32f"

# Curated lookup connecting canonical material formulas to BattINFO battery roles
CURATED_BATTERY_ROLES: dict[str, dict[str, str]] = {
    # ── Cathode Active Materials (PositiveElectrode) ──
    "LiCoO2": {
        "role": "PositiveElectrode",
        "role_iri": POSITIVE_ELECTRODE_IRI,
        "evidence": "Curated benchmark insertion cathode material (LCO)"
    },
    "LiFePO4": {
        "role": "PositiveElectrode",
        "role_iri": POSITIVE_ELECTRODE_IRI,
        "evidence": "Curated olivine cathode material (LFP)"
    },
    "LiNiO2": {
        "role": "PositiveElectrode",
        "role_iri": POSITIVE_ELECTRODE_IRI,
        "evidence": "Curated high-Ni layered oxide cathode material (LNO)"
    },
    "LiMn2O4": {
        "role": "PositiveElectrode",
        "role_iri": POSITIVE_ELECTRODE_IRI,
        "evidence": "Curated spinel cathode active material (LMO)"
    },
    "NaFePO4": {
        "role": "PositiveElectrode",
        "role_iri": POSITIVE_ELECTRODE_IRI,
        "evidence": "Curated Na-ion olivine cathode material"
    },
    "Na3V2(PO4)3": {
        "role": "PositiveElectrode",
        "role_iri": POSITIVE_ELECTRODE_IRI,
        "evidence": "Curated NASICON Na-ion cathode material"
    },

    # ── Anode Active Materials (NegativeElectrode) ──
    "Li4Ti5O12": {
        "role": "NegativeElectrode",
        "role_iri": NEGATIVE_ELECTRODE_IRI,
        "evidence": "Curated zero-strain spinel anode material (LTO)"
    },
    "C": {
        "role": "NegativeElectrode",
        "role_iri": NEGATIVE_ELECTRODE_IRI,
        "evidence": "Curated graphite intercalation anode material"
    },
    "Si": {
        "role": "NegativeElectrode",
        "role_iri": NEGATIVE_ELECTRODE_IRI,
        "evidence": "Curated alloy anode material (Silicon)"
    },

    # ── Electrolytes (Electrolyte) ──
    "Li10Ge(PS6)2": {
        "role": "Electrolyte",
        "role_iri": ELECTROLYTE_IRI,
        "evidence": "Curated superionic thiophosphate solid electrolyte (LGPS)"
    },
    "Li10GeP2S12": {
        "role": "Electrolyte",
        "role_iri": ELECTROLYTE_IRI,
        "evidence": "Curated superionic thiophosphate solid electrolyte (LGPS)"
    },
    "Li7La3Zr2O12": {
        "role": "Electrolyte",
        "role_iri": ELECTROLYTE_IRI,
        "evidence": "Curated garnet solid electrolyte (LLZO)"
    },

    # ── Separator / Coating Materials ──
    "Al2O3": {
        "role": "Separator",
        "role_iri": SEPARATOR_IRI,
        "evidence": "Curated ceramic separator coating layer"
    }
}


class BattINFOMapper:
    """Assigns BattINFO battery semantics and provenance with curated lookup and heuristic rules."""

    def process(self, record: MaterialRecord) -> MaterialRecord:
        """Progressively enrich MaterialRecord with BattINFO battery role semantics."""
        role_info = CURATED_BATTERY_ROLES.get(record.formula)
        if role_info:
            record.battery_role = role_info["role"]
            record.battery_role_iri = role_info["role_iri"]
            record.battery_role_evidence = role_info["evidence"]
            record.is_active_material = True
            record.provenance_map["battinfo"] = "BattINFO Curated Role Mapping"
            logger.info(f"Mapped {record.formula} to BattINFO role: {record.battery_role}")
            return record

        # Heuristic rules based on elemental composition for scale expansion
        comp_elems = set(record.composition.keys())
        formula = record.formula

        # 1. Solid Electrolyte Heuristics (LLZO garnets, LGPS sulfides, NASICON electrolytes, halides)
        if ("Li" in comp_elems and "Zr" in comp_elems and "O" in comp_elems) or \
           ("Li" in comp_elems and "Ge" in comp_elems and "S" in comp_elems) or \
           ("Li" in comp_elems and "P" in comp_elems and "S" in comp_elems) or \
           ("Na" in comp_elems and "S" in comp_elems and "P" in comp_elems):
            record.battery_role = "Electrolyte"
            record.battery_role_iri = ELECTROLYTE_IRI
            record.battery_role_evidence = "Heuristic mapping for alkali solid electrolyte system"
            record.is_active_material = True
            record.provenance_map["battinfo"] = "BattINFO Rule-based Heuristic"
            return record

        # 2. Cathode Heuristics (Li/Na/K/Mg + Transition Metals + O/P/F)
        alkali = {"Li", "Na", "K", "Mg", "Ca", "Zn", "Al"}.intersection(comp_elems)
        tm = {"Co", "Ni", "Mn", "Fe", "V", "Cr", "Cu", "Nb", "Mo"}.intersection(comp_elems)
        anion = {"O", "P", "S", "F"}.intersection(comp_elems)

        if alkali and tm and anion:
            record.battery_role = "PositiveElectrode"
            record.battery_role_iri = POSITIVE_ELECTRODE_IRI
            record.battery_role_evidence = "Heuristic mapping for transition metal cathode compound"
            record.is_active_material = True
            record.provenance_map["battinfo"] = "BattINFO Rule-based Heuristic"
            return record

        # 3. Anode Heuristics (Titanates, Silicon, Carbon)
        if ("Ti" in comp_elems and "O" in comp_elems) or "Si" in comp_elems or formula == "C":
            record.battery_role = "NegativeElectrode"
            record.battery_role_iri = NEGATIVE_ELECTRODE_IRI
            record.battery_role_evidence = "Heuristic mapping for anode active material system"
            record.is_active_material = True
            record.provenance_map["battinfo"] = "BattINFO Rule-based Heuristic"
            return record

        # 4. Separator / Coating Heuristics (Al2O3, ZrO2, SiO2)
        if formula in ["Al2O3", "ZrO2", "SiO2", "TiO2"]:
            record.battery_role = "Separator"
            record.battery_role_iri = SEPARATOR_IRI
            record.battery_role_evidence = "Heuristic mapping for ceramic separator/coating material"
            record.is_active_material = False
            record.provenance_map["battinfo"] = "BattINFO Rule-based Heuristic"
            return record

        # Fallback for generic materials
        record.battery_role = None
        record.battery_role_iri = None
        record.battery_role_evidence = None
        record.is_active_material = False
        logger.debug(f"Material {record.formula} has no battery role mapping. Retained as generic material.")
        return record
