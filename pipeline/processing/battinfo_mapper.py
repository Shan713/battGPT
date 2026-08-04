"""BattINFO Semantic Mapping Engine with Provenance Tracking."""
import logging
from ..models import MaterialRecord

logger = logging.getLogger(__name__)

# Curated lookup connecting canonical material formulas to BattINFO battery roles
CURATED_BATTERY_ROLES: dict[str, dict[str, str]] = {
    # ── Cathode Active Materials (PositiveElectrode) ──
    "LiCoO2": {
        "role": "PositiveElectrode",
        "role_iri": "https://w3id.org/emmo/domain/battery#battery_b8f04fd5_8741_4d17_9713_931d752c0021",
        "evidence": "Curated benchmark insertion cathode material (LCO)"
    },
    "LiFePO4": {
        "role": "PositiveElectrode",
        "role_iri": "https://w3id.org/emmo/domain/battery#battery_b8f04fd5_8741_4d17_9713_931d752c0021",
        "evidence": "Curated olivine cathode material (LFP)"
    },
    "LiNiO2": {
        "role": "PositiveElectrode",
        "role_iri": "https://w3id.org/emmo/domain/battery#battery_b8f04fd5_8741_4d17_9713_931d752c0021",
        "evidence": "Curated high-Ni layered oxide cathode material (LNO)"
    },
    "LiMn2O4": {
        "role": "PositiveElectrode",
        "role_iri": "https://w3id.org/emmo/domain/battery#battery_b8f04fd5_8741_4d17_9713_931d752c0021",
        "evidence": "Curated spinel cathode active material (LMO)"
    },
    "NaFePO4": {
        "role": "PositiveElectrode",
        "role_iri": "https://w3id.org/emmo/domain/battery#battery_b8f04fd5_8741_4d17_9713_931d752c0021",
        "evidence": "Curated Na-ion olivine cathode material"
    },
    "Na3V2(PO4)3": {
        "role": "PositiveElectrode",
        "role_iri": "https://w3id.org/emmo/domain/battery#battery_b8f04fd5_8741_4d17_9713_931d752c0021",
        "evidence": "Curated NASICON Na-ion cathode material"
    },

    # ── Anode Active Materials (NegativeElectrode) ──
    "Li4Ti5O12": {
        "role": "NegativeElectrode",
        "role_iri": "https://w3id.org/emmo/domain/battery#battery_0a37db91_6c02_4eb4_9b2d_e8a2a02b1f85",
        "evidence": "Curated zero-strain spinel anode material (LTO)"
    },
    "C": {
        "role": "NegativeElectrode",
        "role_iri": "https://w3id.org/emmo/domain/battery#battery_0a37db91_6c02_4eb4_9b2d_e8a2a02b1f85",
        "evidence": "Curated graphite intercalation anode material"
    },
    "Si": {
        "role": "NegativeElectrode",
        "role_iri": "https://w3id.org/emmo/domain/battery#battery_0a37db91_6c02_4eb4_9b2d_e8a2a02b1f85",
        "evidence": "Curated alloy anode material (Silicon)"
    },

    # ── Electrolytes (Electrolyte) ──
    "Li10Ge(PS6)2": {  # MP formula_pretty for mp-696128 (ideal stoichiometry: Li10GeP2S12)
        "role": "Electrolyte",
        "role_iri": "https://w3id.org/emmo/domain/battery#battery_b69c4c79_463e_436b_8b59_5b067f9446d6",
        "evidence": "Curated superionic thiophosphate solid electrolyte (LGPS)"
    },
    "Li10GeP2S12": {  # ideal-stoichiometry alias
        "role": "Electrolyte",
        "role_iri": "https://w3id.org/emmo/domain/battery#battery_b69c4c79_463e_436b_8b59_5b067f9446d6",
        "evidence": "Curated superionic thiophosphate solid electrolyte (LGPS)"
    },
    "Li7La3Zr2O12": {
        "role": "Electrolyte",
        "role_iri": "https://w3id.org/emmo/domain/battery#battery_b69c4c79_463e_436b_8b59_5b067f9446d6",
        "evidence": "Curated garnet solid electrolyte (LLZO)"
    },

    # ── Separator / Coating Materials ──
    "Al2O3": {
        "role": "Separator",
        "role_iri": "https://w3id.org/emmo/domain/battery#battery_13e9a59b_2ef4_4a2a_b5e5_d9a8c27bc32f",
        "evidence": "Curated ceramic separator coating layer"
    }
}


class BattINFOMapper:
    """Assigns BattINFO battery semantics and provenance when curated external evidence exists."""

    def process(self, record: MaterialRecord) -> MaterialRecord:
        """Progressively enrich MaterialRecord with curated BattINFO battery role semantics."""
        role_info = CURATED_BATTERY_ROLES.get(record.formula)
        if role_info:
            record.battery_role = role_info["role"]
            record.battery_role_iri = role_info["role_iri"]
            record.battery_role_evidence = role_info["evidence"]
            record.is_active_material = True
            record.provenance_map["battinfo"] = "BattINFO Curated Role Mapping"
            logger.info(f"Mapped {record.formula} to BattINFO role: {record.battery_role}")
        else:
            record.battery_role = None
            record.battery_role_iri = None
            record.battery_role_evidence = None
            record.is_active_material = False
            logger.debug(f"Material {record.formula} has no curated battery role mapping. Retained as generic material.")

        return record
