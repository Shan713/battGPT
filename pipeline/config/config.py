"""Pipeline Configuration and Deterministic URI Scheme definitions."""
from dataclasses import dataclass, field
from pathlib import Path
import os
import re

# Load Materials Project API key from the project-root .env file if present.
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:  # pragma: no cover - dotenv is optional
    pass

@dataclass
class URIScheme:
    """Deterministic URI generator for Knowledge Graph nodes and predicates."""
    BASE_NS: str = "https://w3id.org/battgpt/kg#"
    BASE_RESOURCE: str = "https://w3id.org/battgpt/kg/"

    @classmethod
    def sanitize_id(cls, value: str) -> str:
        """Sanitize strings for valid URI components."""
        return re.sub(r'[^a-zA-Z0-9_\-\.]', '_', str(value))

    @classmethod
    def material_uri(cls, material_id: str) -> str:
        return f"{cls.BASE_RESOURCE}material/{cls.sanitize_id(material_id)}"

    @classmethod
    def crystal_uri(cls, material_id: str) -> str:
        return f"{cls.BASE_RESOURCE}crystal/{cls.sanitize_id(material_id)}"

    @classmethod
    def unitcell_uri(cls, material_id: str) -> str:
        return f"{cls.BASE_RESOURCE}unitcell/{cls.sanitize_id(material_id)}"

    @classmethod
    def spacegroup_uri(cls, spacegroup_number: int) -> str:
        return f"{cls.BASE_RESOURCE}spacegroup/{spacegroup_number}"

    @classmethod
    def crystalsystem_uri(cls, system_name: str) -> str:
        return f"{cls.BASE_RESOURCE}crystalsystem/{cls.sanitize_id(system_name.lower())}"

    @classmethod
    def site_uri(cls, material_id: str, site_index: int) -> str:
        return f"{cls.BASE_RESOURCE}site/{cls.sanitize_id(material_id)}/{site_index}"

    @classmethod
    def species_uri(cls, symbol: str, oxidation_state: int | float | None) -> str:
        ox_str = f"_{int(oxidation_state)}" if oxidation_state is not None else "_0"
        return f"{cls.BASE_RESOURCE}species/{cls.sanitize_id(symbol)}{ox_str}"

    @classmethod
    def element_uri(cls, symbol: str) -> str:
        return f"{cls.BASE_RESOURCE}element/{cls.sanitize_id(symbol)}"

    @classmethod
    def property_uri(cls, material_id: str, prop_name: str) -> str:
        return f"{cls.BASE_RESOURCE}property/{cls.sanitize_id(material_id)}/{cls.sanitize_id(prop_name)}"

    @classmethod
    def bond_uri(cls, material_id: str, src_site_idx: int, tgt_site_idx: int) -> str:
        return f"{cls.BASE_RESOURCE}bond/{cls.sanitize_id(material_id)}/{src_site_idx}_{tgt_site_idx}"

    @classmethod
    def batterycell_uri(cls, material_id: str) -> str:
        return f"{cls.BASE_RESOURCE}batterycell/{cls.sanitize_id(material_id)}"

    @classmethod
    def battgpt_pred(cls, pred_name: str) -> str:
        return f"{cls.BASE_NS}{pred_name}"


@dataclass
class PipelineConfig:
    """Master configuration settings for Knowledge Graph processing."""
    mp_api_key: str | None = field(default_factory=lambda: os.getenv("MP_API_KEY"))
    use_offline_fallback: bool = True
    output_dir: Path = field(default_factory=lambda: Path(__file__).parents[2] / "output")
    sample_materials: list[str] = field(default_factory=lambda: [
        "mp-22526",   # LiCoO2 (Cathode)  — verified vs MP API (R-3m, #166)
        "mp-19017",   # LiFePO4 (Cathode) — verified vs MP API (Pnma, #62)
        "mp-25411",   # LiNiO2 (Cathode)  — verified vs MP API (R-3m, #166)
        "mp-685194",  # Li4Ti5O12 (Anode) — verified vs MP API (C2/c, #15, ground state)
        "mp-48",      # Graphite / C (Anode) — verified vs MP API (P6_3/mmc, #194)
        "mp-696128",  # Li10Ge(PS6)2 / LGPS (Solid Electrolyte) — verified vs MP API
        "mp-19226",   # NaFePO4 (Na-ion Cathode) — verified vs MP API (Pnma, #62)
        "mp-149",     # Silicon / Si (Anode) — verified vs MP API (Fd-3m, #227)
        "mp-942733",  # Li7La3Zr2O12 (LLZO Solid Electrolyte) — verified vs MP API (I4_1/acd, #142)
        "mp-22584",   # LiMn2O4 (Spinel Cathode) — verified vs MP API (Fd-3m, #227)
        "mp-776557",  # Na3V2(PO4)3 (NASICON Na Cathode) — verified vs MP API (C2/c, #15)
        "mp-1143"     # Al2O3 (Separator coating / insulating ceramic) — verified vs MP API (R-3c, #167)
    ])
    cathode_test_materials: list[str] = field(default_factory=lambda: [
        "mp-22526",   # LiCoO2 — LayeredOxideStructure (R-3m, #166)
        "mp-19017",   # LiFePO4 — OlivineStructure (Pnma, #62)
        "mp-25411",   # LiNiO2 — LayeredOxideStructure (R-3m, #166)
        "mp-22584",   # LiMn2O4 — SpinelStructure (Fd-3m, #227)
        "mp-19226",   # NaFePO4 — OlivineStructure (Pnma, #62)
        "mp-776557",  # Na3V2(PO4)3 — NASICONStructure
        "mp-18997",   # LiMnPO4 — OlivineStructure (Pnma, #62)
        "mp-18957",   # NaMnO2 — LayeredOxideStructure (C2/m, #12)
        "mp-19149",   # NaNiO2 — LayeredOxideStructure (C2/m, #12)
        "mp-6396",    # Li3V2(PO4)3 — NASICONStructure (P2_1/c, #14)
    ])

    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
